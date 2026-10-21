"""Discovery adapter contract tests. No network calls."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.core.errors import AppError
from app.providers.discovery_models import DiscoverySearchResponse
from app.providers.ticketmaster import TicketmasterDiscoveryClient

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "ticketmaster" / "events_search.json"
SECRET = "test-key-not-a-real-secret"


def _payload() -> dict[str, object]:
    loaded = json.loads(FIXTURE.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _client(handler: httpx.MockTransport) -> TicketmasterDiscoveryClient:
    return TicketmasterDiscoveryClient(
        SECRET,
        min_interval_seconds=0,
        transport=handler,
    )


@pytest.mark.asyncio
async def test_search_parses_recorded_fixture_without_leaking_key() -> None:
    raw = FIXTURE.read_text()
    assert SECRET not in raw
    assert "apikey" not in raw

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["apikey"] == SECRET
        assert request.url.params["classificationName"] == "NBA"
        assert request.url.params["sort"] == "date,asc"
        assert request.url.params["page"] == "0"
        assert "events.json" in str(request.url)
        return httpx.Response(200, json=_payload())

    events, total = await _client(httpx.MockTransport(handler)).search_nba_events(
        keyword="Lakers",
        start=None,
        end=None,
        page=1,
        page_size=20,
    )
    assert total == 3
    assert [event.id for event in events] == [
        "vvG1LakersCeltics",
        "vvG1LakersWarriorsLate",
        "vvConcertLakersNight",
    ]
    assert events[0].price_ranges[0].min == 48.0
    parsed = DiscoverySearchResponse.model_validate(_payload())
    assert parsed.events()[0].primary_venue() is not None


@pytest.mark.asyncio
async def test_rate_limit_and_auth_errors_hide_the_key() -> None:
    def limited(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"fault": {"faultstring": SECRET}})

    with pytest.raises(AppError) as rate_limited:
        await _client(httpx.MockTransport(limited)).search_nba_events(
            keyword=None, start=None, end=None, page=1, page_size=20
        )
    assert rate_limited.value.status_code == 429
    assert rate_limited.value.code == "upstream_rate_limited"
    assert SECRET not in rate_limited.value.message

    def denied(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text=SECRET)

    with pytest.raises(AppError) as unauthorized:
        await _client(httpx.MockTransport(denied)).search_nba_events(
            keyword=None, start=None, end=None, page=1, page_size=20
        )
    assert unauthorized.value.status_code == 503
    assert SECRET not in unauthorized.value.message


@pytest.mark.asyncio
async def test_upstream_failure_is_503() -> None:
    def down(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    with pytest.raises(AppError) as exc:
        await _client(httpx.MockTransport(down)).search_nba_events(
            keyword=None, start=None, end=None, page=1, page_size=20
        )
    assert exc.value.status_code == 503
    assert exc.value.code == "source_unavailable"
