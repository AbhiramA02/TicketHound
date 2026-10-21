"""Event matching: home/away wording, reschedule identity, doubleheaders, concerts."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from app.providers.discovery_models import DiscoveryEvent
from app.schemas.common import DataStatus
from app.services.event_store import MemoryEventStore
from app.services.matching import match_discovery_event

FIXTURE = Path(__file__).resolve().parents[3] / "fixtures" / "ticketmaster" / "events_search.json"
OBSERVED = datetime(2026, 10, 21, tzinfo=UTC)


def _events() -> list[DiscoveryEvent]:
    payload = json.loads(FIXTURE.read_text())
    return [DiscoveryEvent.model_validate(item) for item in payload["_embedded"]["events"]]


def _lakers_celtics() -> DiscoveryEvent:
    return _events()[0]


def _with_name(
    event: DiscoveryEvent, name: str, *, venue_city: str | None = None
) -> DiscoveryEvent:
    data = event.model_dump(by_alias=True)
    data["name"] = name
    if venue_city is not None:
        data["_embedded"]["venues"][0]["city"]["name"] = venue_city
    return DiscoveryEvent.model_validate(data)


def test_at_wording_sets_home_team_and_vs_does_not_reverse_it() -> None:
    at_game = match_discovery_event(_lakers_celtics(), observed_at=OBSERVED)
    assert at_game is not None
    assert at_game.home.abbreviation == "LAL"
    assert at_game.away.abbreviation == "BOS"
    assert at_game.matched_method == "title_at_and_venue"
    assert at_game.price_min_minor == 4800
    assert at_game.price_max_minor == 42000
    assert at_game.season_type == "regular"
    assert at_game.venue_timezone == "America/Los_Angeles"

    vs_game = match_discovery_event(
        _with_name(_lakers_celtics(), "Los Angeles Lakers vs Boston Celtics"),
        observed_at=OBSERVED,
    )
    assert vs_game is not None
    assert vs_game.home.abbreviation == "LAL"
    assert vs_game.away.abbreviation == "BOS"
    assert vs_game.matched_method == "title_vs_and_venue"


def test_conflicting_at_and_venue_is_unresolved() -> None:
    swapped = _with_name(
        _lakers_celtics(),
        "Los Angeles Lakers at Boston Celtics",
        venue_city="Los Angeles",
    )
    assert match_discovery_event(swapped, observed_at=OBSERVED) is None


def test_concert_is_not_an_nba_game() -> None:
    concert = _events()[2]
    assert match_discovery_event(concert, observed_at=OBSERVED) is None


def test_doubleheader_stays_two_events() -> None:
    store = MemoryEventStore()
    matched = [match_discovery_event(event, observed_at=OBSERVED) for event in _events()[:2]]
    assert all(item is not None for item in matched)
    saved = [
        store.upsert(item, data_status=DataStatus.LIVE) for item in matched if item is not None
    ]
    assert saved[0] is not None and saved[1] is not None
    assert saved[0].id != saved[1].id
    assert saved[0].start_at_utc != saved[1].start_at_utc
    assert saved[0].home_team.abbreviation == saved[1].home_team.abbreviation == "LAL"


def test_reschedule_keeps_canonical_id_when_provider_id_matches() -> None:
    store = MemoryEventStore()
    original = match_discovery_event(_lakers_celtics(), observed_at=OBSERVED)
    assert original is not None
    first = store.upsert(original, data_status=DataStatus.LIVE)
    assert first is not None

    raw = _lakers_celtics().model_dump(by_alias=True)
    moved = deepcopy(raw)
    moved["dates"]["start"]["dateTime"] = "2026-11-10T03:30:00Z"
    moved["dates"]["start"]["localDate"] = "2026-11-09"
    moved["dates"]["status"] = {"code": "rescheduled"}
    rescheduled = match_discovery_event(DiscoveryEvent.model_validate(moved), observed_at=OBSERVED)
    assert rescheduled is not None
    second = store.upsert(rescheduled, data_status=DataStatus.LIVE)
    assert second is not None
    assert second.id == first.id
    assert second.start_at_utc != first.start_at_utc
    assert second.status == "SCHEDULED"
