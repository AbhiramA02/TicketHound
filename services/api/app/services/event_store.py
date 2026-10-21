"""Persist canonical games and the Ticketmaster provider link.

The same provider event id updates one canonical row, including after a reschedule.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Event, ProviderEvent, Team, Venue
from app.db.nba_teams import NBA_TEAMS, NbaTeam
from app.db.session import SessionLocal
from app.schemas.common import DataStatus, Granularity, PriceBasis
from app.schemas.events import EventStatus, EventSummary, TeamSummary, VenueSummary
from app.services.matching import MatchedEvent

PROVIDER_CODE = "ticketmaster"


def summary_from_match(
    matched: MatchedEvent,
    event_id: uuid.UUID,
    data_status: DataStatus,
) -> EventSummary:
    has_price = matched.price_min_minor is not None
    return EventSummary(
        id=event_id,
        home_team=TeamSummary(
            id=matched.home.id,
            name=matched.home.name,
            abbreviation=matched.home.abbreviation,
            city=matched.home.city,
        ),
        away_team=TeamSummary(
            id=matched.away.id,
            name=matched.away.name,
            abbreviation=matched.away.abbreviation,
            city=matched.away.city,
        ),
        venue=VenueSummary(
            id=uuid.uuid5(event_id, matched.venue_name),
            name=matched.venue_name,
            city=matched.venue_city,
            state=matched.venue_state,
            timezone=matched.venue_timezone,
        ),
        start_at_utc=matched.start_at_utc,
        local_start_at=matched.local_start_at,
        status=matched.status,
        data_status=data_status,
        season_type=matched.season_type,
        provider_code=PROVIDER_CODE,
        source_url=matched.external_url,
        source_observed_at=matched.observed_at,
        lowest_all_in_price_minor=None,
        price_min_minor=matched.price_min_minor,
        price_max_minor=matched.price_max_minor,
        price_basis=PriceBasis.FROM_PRICE if has_price else None,
        price_granularity=Granularity.EVENT if has_price else None,
        currency=matched.price_currency,
    )


class MemoryEventStore:
    """Identity rules for tests. Production uses SqlEventStore."""

    def __init__(self) -> None:
        self.by_provider: dict[str, EventSummary] = {}
        self.by_id: dict[uuid.UUID, EventSummary] = {}

    def ensure_teams(self) -> None:
        return None

    def upsert(self, matched: MatchedEvent, *, data_status: DataStatus) -> EventSummary | None:
        existing = self.by_provider.get(matched.provider_event_id)
        event_id = existing.id if existing is not None else uuid.uuid4()
        summary = summary_from_match(matched, event_id, data_status)
        self.by_provider[matched.provider_event_id] = summary
        self.by_id[event_id] = summary
        return summary

    def get(self, event_id: uuid.UUID) -> EventSummary | None:
        found = self.by_id.get(event_id)
        if found is None:
            return None
        return found.model_copy(update={"data_status": DataStatus.CACHED})


class SqlEventStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_teams(self) -> None:
        present = set(self.db.scalars(select(Team.nba_team_id)).all())
        for team in NBA_TEAMS:
            if team.nba_team_id in present:
                continue
            self.db.add(
                Team(
                    id=team.id,
                    nba_team_id=team.nba_team_id,
                    name=team.name,
                    abbreviation=team.abbreviation,
                    city=team.city,
                    aliases=", ".join(team.aliases),
                    active="true",
                )
            )
        self.db.flush()

    def upsert(self, matched: MatchedEvent, *, data_status: DataStatus) -> EventSummary | None:
        self.ensure_teams()
        link = self.db.scalar(
            select(ProviderEvent).where(
                ProviderEvent.provider_code == PROVIDER_CODE,
                ProviderEvent.provider_event_id == matched.provider_event_id,
            )
        )
        event: Event | None = None
        try:
            with self.db.begin_nested():
                event = self._apply(link, matched)
                if event is None:
                    return None
                self.db.flush()
        except IntegrityError:
            return None
        stored = self.db.scalar(
            select(ProviderEvent).where(
                ProviderEvent.provider_code == PROVIDER_CODE,
                ProviderEvent.provider_event_id == matched.provider_event_id,
            )
        )
        if stored is None or event is None:
            return None
        return self._summary(event, stored, data_status)

    def get(self, event_id: uuid.UUID) -> EventSummary | None:
        event = self.db.get(Event, event_id)
        if event is None:
            return None
        link = self.db.scalar(select(ProviderEvent).where(ProviderEvent.event_id == event.id))
        if link is None:
            return None
        return self._summary(event, link, DataStatus.CACHED)

    def _apply(self, link: ProviderEvent | None, matched: MatchedEvent) -> Event | None:
        home_id = self._team_id(matched.home)
        away_id = self._team_id(matched.away)
        venue_id = self._venue_id(matched)
        if link is None:
            event = Event(
                id=uuid.uuid4(),
                league="NBA",
                home_team_id=home_id,
                away_team_id=away_id,
                venue_id=venue_id,
                start_at_utc=matched.start_at_utc,
                local_start_at=matched.local_start_at,
                status=matched.status.value,
                season_type=matched.season_type,
                last_verified_at=matched.observed_at,
            )
            self.db.add(event)
            self.db.flush()
            self.db.add(self._link(event.id, matched))
            return event
        existing = self.db.get(Event, link.event_id)
        if existing is None:
            return None
        existing.home_team_id = home_id
        existing.away_team_id = away_id
        existing.venue_id = venue_id
        existing.start_at_utc = matched.start_at_utc
        existing.local_start_at = matched.local_start_at
        existing.status = matched.status.value
        existing.season_type = matched.season_type
        existing.last_verified_at = matched.observed_at
        link.external_url = matched.external_url
        link.matched_method = matched.matched_method
        link.match_confidence = matched.match_confidence
        link.last_seen_at = matched.observed_at
        link.price_min_minor = matched.price_min_minor
        link.price_max_minor = matched.price_max_minor
        link.price_currency = matched.price_currency
        return existing

    def _link(self, event_id: uuid.UUID, matched: MatchedEvent) -> ProviderEvent:
        return ProviderEvent(
            id=uuid.uuid4(),
            event_id=event_id,
            provider_code=PROVIDER_CODE,
            provider_event_id=matched.provider_event_id,
            external_url=matched.external_url,
            matched_method=matched.matched_method,
            match_confidence=matched.match_confidence,
            last_seen_at=matched.observed_at,
            price_min_minor=matched.price_min_minor,
            price_max_minor=matched.price_max_minor,
            price_currency=matched.price_currency,
        )

    def _team_id(self, team: NbaTeam) -> uuid.UUID:
        row = self.db.scalar(select(Team).where(Team.nba_team_id == team.nba_team_id))
        if row is None:
            return team.id
        return row.id

    def _venue_id(self, matched: MatchedEvent) -> uuid.UUID:
        row = self.db.scalar(
            select(Venue).where(Venue.name == matched.venue_name, Venue.city == matched.venue_city)
        )
        if row is not None:
            return row.id
        venue = Venue(
            id=uuid.uuid4(),
            name=matched.venue_name,
            city=matched.venue_city,
            state=matched.venue_state or "NA",
            timezone=matched.venue_timezone,
        )
        self.db.add(venue)
        self.db.flush()
        return venue.id

    def _summary(self, event: Event, link: ProviderEvent, data_status: DataStatus) -> EventSummary:
        home = self.db.get(Team, event.home_team_id)
        away = self.db.get(Team, event.away_team_id)
        venue = self.db.get(Venue, event.venue_id)
        if home is None or away is None or venue is None:
            raise RuntimeError("canonical event is missing a team or venue")
        has_price = link.price_min_minor is not None
        return EventSummary(
            id=event.id,
            home_team=TeamSummary(
                id=home.id,
                name=home.name,
                abbreviation=home.abbreviation,
                city=home.city,
            ),
            away_team=TeamSummary(
                id=away.id,
                name=away.name,
                abbreviation=away.abbreviation,
                city=away.city,
            ),
            venue=VenueSummary(
                id=venue.id,
                name=venue.name,
                city=venue.city,
                state=venue.state,
                timezone=venue.timezone,
            ),
            start_at_utc=event.start_at_utc,
            local_start_at=event.local_start_at,
            status=EventStatus(event.status),
            data_status=data_status,
            season_type=event.season_type,
            provider_code=link.provider_code,
            source_url=link.external_url,
            source_observed_at=link.last_seen_at,
            lowest_all_in_price_minor=None,
            price_min_minor=link.price_min_minor,
            price_max_minor=link.price_max_minor,
            price_basis=PriceBasis.FROM_PRICE if has_price else None,
            price_granularity=Granularity.EVENT if has_price else None,
            currency=link.price_currency,
        )


@contextmanager
def session_scope() -> Iterator[SqlEventStore]:
    db = SessionLocal()
    try:
        yield SqlEventStore(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
