"""Ticketmaster Discovery v2 client.

Calls are server-side only. The API key is a query parameter and is never logged.
Throttle defaults to 2 requests/second (the stricter published FAQ figure).
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, date, datetime
from datetime import time as dt_time
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.errors import AppError
from app.providers.base import ProviderCapabilities
from app.providers.discovery_models import DiscoveryEvent, DiscoverySearchResponse


class RateLimiter:
    """Serial gap between outbound calls. Interval 0 disables waiting."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = max(0.0, min_interval_seconds)
        self._lock = asyncio.Lock()
        self._next_at = 0.0

    async def wait(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            delay = self._next_at - now
            if delay > 0:
                await asyncio.sleep(delay)
            self._next_at = time.monotonic() + self._min_interval


def _day_start(value: date) -> str:
    stamp = datetime.combine(value, dt_time.min, tzinfo=UTC)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _day_end(value: date) -> str:
    stamp = datetime.combine(value, dt_time.max.replace(microsecond=0), tzinfo=UTC)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


class TicketmasterDiscoveryClient:
    """Search NBA events. Does not request partner inventory or seat maps."""

    name = "Ticketmaster Discovery"
    code = "ticketmaster"
    capabilities = ProviderCapabilities(
        search_events=True,
        event_price_summary=True,
        granular_offers=False,
        all_in_prices=False,
        seat_locations=False,
        purchase_deep_links=False,
    )

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://app.ticketmaster.com/discovery/v2",
        min_interval_seconds: float = 0.5,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._transport = transport
        self._limiter = limiter or RateLimiter(min_interval_seconds)

    async def search_nba_events(
        self,
        *,
        keyword: str | None,
        start: date | None,
        end: date | None,
        page: int,
        page_size: int,
    ) -> tuple[list[DiscoveryEvent], int]:
        params: dict[str, Any] = {
            "apikey": self._api_key,
            "classificationName": "NBA",
            "sort": "date,asc",
            "size": page_size,
            "page": max(page - 1, 0),
        }
        if keyword:
            params["keyword"] = keyword
        if start is not None:
            params["startDateTime"] = _day_start(start)
        else:
            params["startDateTime"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        if end is not None:
            params["endDateTime"] = _day_end(end)
        payload = await self._get_json("/events.json", params)
        try:
            parsed = DiscoverySearchResponse.model_validate(payload)
        except ValidationError as exc:
            raise AppError(
                code="source_unavailable",
                message="Ticketmaster Discovery returned an unexpected event payload",
                status_code=503,
            ) from exc
        return parsed.events(), parsed.total()

    async def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        await self._limiter.wait()
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(f"{self._base_url}{path}", params=params)
        except httpx.HTTPError as exc:
            raise AppError(
                code="source_unavailable",
                message="Ticketmaster Discovery could not be reached",
                status_code=503,
            ) from exc
        return self._decode(response)

    def _decode(self, response: httpx.Response) -> Any:
        if response.status_code == 429:
            raise AppError(
                code="upstream_rate_limited",
                message="Ticketmaster Discovery rate limit reached",
                status_code=429,
            )
        if response.status_code in {401, 403}:
            raise AppError(
                code="provider_unauthorized",
                message="Ticketmaster rejected the Discovery API key",
                status_code=503,
            )
        if response.status_code >= 400:
            raise AppError(
                code="source_unavailable",
                message="Ticketmaster Discovery is unavailable",
                status_code=503,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise AppError(
                code="source_unavailable",
                message="Ticketmaster Discovery returned invalid JSON",
                status_code=503,
            ) from exc
