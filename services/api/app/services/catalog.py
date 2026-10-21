"""Catalog orchestration — selects DEMO vs future live providers via flags."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import Settings
from app.core.errors import AppError
from app.providers.demo import DemoProvider
from app.schemas.common import (
    ApiResponse,
    DataStatus,
    PaginatedData,
    PaginationMeta,
    ResponseMeta,
)
from app.schemas.events import EventSummary, Offer, ProviderStatus


class CatalogService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.demo = DemoProvider()

    def _meta(self, *, warning: str | None = None) -> ResponseMeta:
        demo = self.settings.demo_mode or self.settings.provider_demo_enabled
        return ResponseMeta(
            data_status=DataStatus.DEMO if demo else DataStatus.UNAVAILABLE,
            fetched_at=datetime.now(UTC),
            warning=warning
            or (
                "Synthetic demonstration data, not purchasable tickets"
                if demo
                else "No live providers enabled"
            ),
            demo_mode=demo,
        )

    def provider_status(self) -> ApiResponse[list[ProviderStatus]]:
        statuses: list[ProviderStatus] = [
            ProviderStatus(
                code="demo",
                enabled=self.settings.provider_demo_enabled,
                data_status=DataStatus.DEMO
                if self.settings.provider_demo_enabled
                else DataStatus.UNAVAILABLE,
                capabilities=self.demo.capabilities.model_dump(),
                notes="Isolated fixture provider for local/portfolio demos",
            ),
            ProviderStatus(
                code="ticketmaster",
                enabled=self.settings.provider_ticketmaster_enabled,
                data_status=DataStatus.UNAVAILABLE,
                capabilities={
                    "search_events": False,
                    "event_price_summary": False,
                    "granular_offers": False,
                    "all_in_prices": False,
                    "seat_locations": False,
                    "purchase_deep_links": False,
                },
                notes="Phase 1 — Discovery API stub only; credentials TBD",
            ),
        ]
        return ApiResponse(data=statuses, meta=self._meta())

    async def list_events(
        self,
        *,
        team: str | None,
        page: int,
        page_size: int,
    ) -> ApiResponse[PaginatedData[EventSummary]]:
        if not self.settings.provider_demo_enabled and not self.settings.demo_mode:
            raise AppError(
                code="provider_unavailable",
                message="No enabled event providers",
                status_code=503,
            )
        items, total = await self.demo.list_events(team=team, page=page, page_size=page_size)
        return ApiResponse(
            data=PaginatedData(
                items=items,
                pagination=PaginationMeta(page=page, page_size=page_size, total=total),
            ),
            meta=self._meta(),
        )

    async def get_event(self, event_id: str) -> ApiResponse[EventSummary]:
        event = await self.demo.get_event(event_id)
        if event is None:
            raise AppError(
                code="event_not_found",
                message=f"Event {event_id} not found",
                status_code=404,
            )
        return ApiResponse(data=event, meta=self._meta())

    async def get_offers(
        self, event_id: str, quantity: int
    ) -> ApiResponse[list[Offer]]:
        event = await self.demo.get_event(event_id)
        if event is None:
            raise AppError(
                code="event_not_found",
                message=f"Event {event_id} not found",
                status_code=404,
            )
        offers = await self.demo.get_offers(event_id, quantity=quantity)
        return ApiResponse(data=offers, meta=self._meta())
