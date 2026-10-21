"""API contract tests for health + demo catalog (no live providers)."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with patch("app.api.v1.health.check_database", return_value=True):
        app = create_app()
        with TestClient(app) as c:
            yield c


def test_health_ok(client: TestClient) -> None:
    with patch("app.api.v1.health.check_database", return_value=True):
        res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"ok", "degraded"}
    assert "demo_mode" in body


def test_providers_status_includes_demo(client: TestClient) -> None:
    res = client.get("/api/v1/providers/status")
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["data_status"] == "DEMO"
    codes = {p["code"] for p in body["data"]}
    assert "demo" in codes
    assert "ticketmaster" in codes


def test_list_events_demo(client: TestClient) -> None:
    res = client.get("/api/v1/events")
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["data_status"] == "DEMO"
    assert "Synthetic" in (body["meta"]["warning"] or "")
    assert body["data"]["pagination"]["total"] >= 1
    assert all(item["data_status"] == "DEMO" for item in body["data"]["items"])


def test_event_offers_demo(client: TestClient) -> None:
    listing = client.get("/api/v1/events").json()
    event_id = listing["data"]["items"][0]["id"]
    res = client.get(f"/api/v1/events/{event_id}/offers", params={"quantity": 2})
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["data_status"] == "DEMO"
    assert len(body["data"]) >= 1
    assert all(o["data_status"] == "DEMO" for o in body["data"])


def test_missing_event_404(client: TestClient) -> None:
    res = client.get("/api/v1/events/00000000-0000-4000-8000-000000000099")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "event_not_found"


def test_team_filter(client: TestClient) -> None:
    res = client.get("/api/v1/events", params={"team": "Lakers"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    assert any(
        "Lakers" in i["home_team"]["name"] or "Lakers" in i["away_team"]["name"] for i in items
    )
