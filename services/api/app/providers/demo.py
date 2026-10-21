"""Isolated DEMO provider — synthetic fixtures only. Never labeled LIVE."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.providers.base import ProviderCapabilities
from app.schemas.common import DataStatus, Granularity, PriceBasis
from app.schemas.events import (
    EventStatus,
    EventSummary,
    Offer,
    TeamSummary,
    VenueSummary,
)

# Stable UUIDs so the UI can deep-link consistently across restarts.
_TEAM_LAL = UUID("11111111-1111-4111-8111-111111111101")
_TEAM_GSW = UUID("11111111-1111-4111-8111-111111111102")
_TEAM_BOS = UUID("11111111-1111-4111-8111-111111111103")
_TEAM_NYK = UUID("11111111-1111-4111-8111-111111111104")
_VENUE_STAPLES = UUID("22222222-2222-4222-8222-222222222201")
_VENUE_CHASE = UUID("22222222-2222-4222-8222-222222222202")
_EVENT_1 = UUID("33333333-3333-4333-8333-333333333301")
_EVENT_2 = UUID("33333333-3333-4333-8333-333333333302")
_EVENT_3 = UUID("33333333-3333-4333-8333-333333333303")


def _future(days: int, hour_utc: int = 2) -> datetime:
    base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    return base + timedelta(days=days, hours=hour_utc)


class DemoProvider:
    """Synthetic NBA games and offers for local development."""

    name = "TicketHound Demo"
    code = "demo"
    capabilities = ProviderCapabilities(
        search_events=True,
        event_price_summary=True,
        granular_offers=True,
        all_in_prices=True,
        seat_locations=True,
        purchase_deep_links=False,
    )

    def __init__(self) -> None:
        self._teams = {
            _TEAM_LAL: TeamSummary(
                id=_TEAM_LAL, name="Los Angeles Lakers", abbreviation="LAL", city="Los Angeles"
            ),
            _TEAM_GSW: TeamSummary(
                id=_TEAM_GSW, name="Golden State Warriors", abbreviation="GSW", city="San Francisco"
            ),
            _TEAM_BOS: TeamSummary(
                id=_TEAM_BOS, name="Boston Celtics", abbreviation="BOS", city="Boston"
            ),
            _TEAM_NYK: TeamSummary(
                id=_TEAM_NYK, name="New York Knicks", abbreviation="NYK", city="New York"
            ),
        }
        self._venues = {
            _VENUE_STAPLES: VenueSummary(
                id=_VENUE_STAPLES,
                name="Crypto.com Arena",
                city="Los Angeles",
                state="CA",
                timezone="America/Los_Angeles",
            ),
            _VENUE_CHASE: VenueSummary(
                id=_VENUE_CHASE,
                name="Chase Center",
                city="San Francisco",
                state="CA",
                timezone="America/Los_Angeles",
            ),
        }
        starts = [_future(7), _future(12), _future(18)]
        self._events: list[EventSummary] = [
            EventSummary(
                id=_EVENT_1,
                home_team=self._teams[_TEAM_LAL],
                away_team=self._teams[_TEAM_BOS],
                venue=self._venues[_VENUE_STAPLES],
                start_at_utc=starts[0],
                local_start_at=starts[0] - timedelta(hours=7),
                status=EventStatus.SCHEDULED,
                data_status=DataStatus.DEMO,
                lowest_all_in_price_minor=18500,
                currency="USD",
            ),
            EventSummary(
                id=_EVENT_2,
                home_team=self._teams[_TEAM_GSW],
                away_team=self._teams[_TEAM_LAL],
                venue=self._venues[_VENUE_CHASE],
                start_at_utc=starts[1],
                local_start_at=starts[1] - timedelta(hours=7),
                status=EventStatus.SCHEDULED,
                data_status=DataStatus.DEMO,
                lowest_all_in_price_minor=14200,
                currency="USD",
            ),
            EventSummary(
                id=_EVENT_3,
                home_team=self._teams[_TEAM_NYK],
                away_team=self._teams[_TEAM_BOS],
                venue=VenueSummary(
                    id=UUID("22222222-2222-4222-8222-222222222203"),
                    name="Madison Square Garden",
                    city="New York",
                    state="NY",
                    timezone="America/New_York",
                ),
                start_at_utc=starts[2],
                local_start_at=starts[2] - timedelta(hours=4),
                status=EventStatus.SCHEDULED,
                data_status=DataStatus.DEMO,
                lowest_all_in_price_minor=21000,
                currency="USD",
            ),
        ]
        self._offers: dict[UUID, list[Offer]] = {
            _EVENT_1: [
                Offer(
                    id="demo-offer-lal-bos-upper",
                    provider_code=self.code,
                    section="312",
                    row="12",
                    seat_zone="upper",
                    ticket_count_for_price=2,
                    all_in_price_minor=18500,
                    base_price_minor=16000,
                    currency="USD",
                    price_basis=PriceBasis.ALL_IN,
                    granularity=Granularity.LISTING,
                    purchase_url=None,
                    observed_at=datetime.now(UTC),
                    data_status=DataStatus.DEMO,
                ),
                Offer(
                    id="demo-offer-lal-bos-lower",
                    provider_code=self.code,
                    section="114",
                    row="8",
                    seat_zone="lower",
                    ticket_count_for_price=2,
                    all_in_price_minor=42000,
                    base_price_minor=38000,
                    currency="USD",
                    price_basis=PriceBasis.ALL_IN,
                    granularity=Granularity.LISTING,
                    purchase_url=None,
                    observed_at=datetime.now(UTC),
                    data_status=DataStatus.DEMO,
                ),
            ],
            _EVENT_2: [
                Offer(
                    id="demo-offer-gsw-lal-mid",
                    provider_code=self.code,
                    section="208",
                    row="5",
                    seat_zone="mid",
                    ticket_count_for_price=2,
                    all_in_price_minor=14200,
                    base_price_minor=12500,
                    currency="USD",
                    price_basis=PriceBasis.ALL_IN,
                    granularity=Granularity.LISTING,
                    purchase_url=None,
                    observed_at=datetime.now(UTC),
                    data_status=DataStatus.DEMO,
                ),
            ],
            _EVENT_3: [
                Offer(
                    id="demo-offer-nyk-bos-upper",
                    provider_code=self.code,
                    section="420",
                    row="3",
                    seat_zone="upper",
                    ticket_count_for_price=2,
                    all_in_price_minor=21000,
                    base_price_minor=18500,
                    currency="USD",
                    price_basis=PriceBasis.ALL_IN,
                    granularity=Granularity.LISTING,
                    purchase_url=None,
                    observed_at=datetime.now(UTC),
                    data_status=DataStatus.DEMO,
                ),
            ],
        }

    async def list_events(
        self,
        *,
        team: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[EventSummary], int]:
        items = self._events
        if team:
            needle = team.strip().lower()
            items = [
                e
                for e in items
                if needle
                in {
                    e.home_team.name.lower(),
                    e.home_team.abbreviation.lower(),
                    e.home_team.city.lower(),
                    e.away_team.name.lower(),
                    e.away_team.abbreviation.lower(),
                    e.away_team.city.lower(),
                }
                or needle in e.home_team.name.lower()
                or needle in e.away_team.name.lower()
            ]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end], total

    async def get_event(self, event_id: str) -> EventSummary | None:
        try:
            uid = UUID(event_id)
        except ValueError:
            return None
        for event in self._events:
            if event.id == uid:
                return event
        return None

    async def get_offers(self, event_id: str, quantity: int = 2) -> list[Offer]:
        try:
            uid = UUID(event_id)
        except ValueError:
            return []
        offers = self._offers.get(uid, [])
        return [o for o in offers if o.ticket_count_for_price == quantity]
