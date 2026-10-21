"""Live catalog uses Discovery and does not mix in demo games."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import AppError
from app.main import create_app
from app.providers.ticketmaster import TicketmasterDiscoveryClient
from app.services.catalog import CatalogService
from app.services.event_store import MemoryEventStore

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "ticketmaster" / "events_search.json"


def _live_settings() -> Settings:
    return Settings(
        demo_mode=False,
        provider_demo_enabled=False,
        provider_ticketmaster_enabled=True,
        ticketmaster_api_key="test-key",
        ticketmaster_min_interval_seconds=0,
    )


def _catalog() -> CatalogService:
    payload = json.loads(FIXTURE.read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = TicketmasterDiscoveryClient(
        "test-key",
        min_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    )
    return CatalogService(_live_settings(), store=MemoryEventStore(), discovery=client)


@pytest.mark.asyncio
async def test_live_search_omits_concert_and_keeps_demo_out() -> None:
    catalog = _catalog()
    result = await catalog.list_events(team="Lakers", start=None, end=None, page=1, page_size=20)
    assert result.meta.data_status == "LIVE"
    assert result.meta.demo_mode is False
    assert "not a complete NBA schedule" in (result.meta.warning or "")
    assert "omitted" in (result.meta.warning or "")
    ids = {item.provider_code for item in result.data.items}
    assert ids == {"ticketmaster"}
    assert len(result.data.items) == 2
    assert all(item.price_granularity == "EVENT" for item in result.data.items)
    assert all(item.lowest_all_in_price_minor is None for item in result.data.items)
    assert all(item.price_basis == "FROM_PRICE" for item in result.data.items)

    detail = await catalog.get_event(str(result.data.items[0].id))
    assert detail.meta.data_status == "CACHED"
    offers = await catalog.get_offers(str(result.data.items[0].id), quantity=2)
    assert offers.meta.data_status == "CACHED"
    assert len(offers.data) == 1
    assert offers.data[0].granularity == "EVENT"
    assert offers.data[0].section is None
    assert offers.data[0].row is None
    assert offers.data[0].all_in_price_minor is None
    assert "not a section" in (offers.meta.warning or "")


@pytest.mark.asyncio
async def test_demo_mode_does_not_call_discovery() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Discovery was called during demo mode")

    client = TicketmasterDiscoveryClient("test-key", transport=httpx.MockTransport(handler))
    catalog = CatalogService(
        Settings(
            demo_mode=True,
            provider_ticketmaster_enabled=True,
            ticketmaster_api_key="test-key",
        ),
        discovery=client,
    )
    result = await catalog.list_events(team=None, start=None, end=None, page=1, page_size=20)
    assert result.meta.data_status == "DEMO"
    assert all(item.data_status == "DEMO" for item in result.data.items)


@pytest.mark.asyncio
async def test_missing_key_is_unavailable() -> None:
    catalog = CatalogService(
        Settings(
            demo_mode=False,
            provider_demo_enabled=True,
            provider_ticketmaster_enabled=True,
            ticketmaster_api_key=None,
        )
    )
    with pytest.raises(AppError) as exc:
        await catalog.list_events(team=None, start=None, end=None, page=1, page_size=20)
    assert exc.value.status_code == 503
    assert "TICKETMASTER_API_KEY" in exc.value.message


def test_teams_and_invalid_date_range() -> None:
    app = create_app()
    with TestClient(app) as client:
        teams = client.get("/api/v1/teams")
        assert teams.status_code == 200
        body = teams.json()
        assert len(body["data"]) == 30
        assert any(team["abbreviation"] == "LAL" for team in body["data"])

        bad = client.get("/api/v1/events", params={"start": "2026-12-01", "end": "2026-11-01"})
        assert bad.status_code == 400
        assert bad.json()["error"]["code"] == "invalid_filters"

        empty = client.get("/api/v1/events", params={"end": date(2000, 1, 1).isoformat()})
        assert empty.status_code == 200
        assert empty.json()["data"]["pagination"]["total"] == 0
