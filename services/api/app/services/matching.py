"""Map a Discovery event onto canonical NBA teams, venue, and local date.

Home team comes from "Away at Home" wording, confirmed by venue city when the
city distinguishes the two teams. "vs" wording does not set home by itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.db.nba_teams import NBA_TEAMS, NbaTeam
from app.providers.discovery_models import DiscoveryEvent
from app.schemas.events import EventStatus

_AT = re.compile(r"^(.+?)\s+at\s+(.+)$", re.IGNORECASE)
_VS = re.compile(r"^(.+?)\s+vs\.?\s+(.+)$", re.IGNORECASE)
_NON_WORD = re.compile(r"[^a-z0-9\s]")
_SPACE = re.compile(r"\s+")


def _normalize(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    cleaned = _NON_WORD.sub(" ", lowered)
    return _SPACE.sub(" ", cleaned).strip()


def _alias_index() -> dict[str, NbaTeam]:
    index: dict[str, NbaTeam] = {}
    for team in NBA_TEAMS:
        phrases = (team.name, team.abbreviation, *team.aliases)
        for phrase in phrases:
            key = _normalize(phrase)
            if len(key) < 3:
                continue
            index.setdefault(key, team)
    return index


_ALIASES = _alias_index()
_ALIAS_KEYS = sorted(_ALIASES, key=len, reverse=True)


def _contains_phrase(haystack: str, phrase: str) -> bool:
    return re.search(rf"(?:^|\s){re.escape(phrase)}(?:\s|$)", haystack) is not None


def resolve_team_text(text: str) -> NbaTeam | None:
    """Resolve one side of a title. Ambiguous text (two teams) returns None."""

    norm = _normalize(text)
    if norm in _ALIASES:
        return _ALIASES[norm]
    hits: list[NbaTeam] = []
    seen: set[str] = set()
    for key in _ALIAS_KEYS:
        team = _ALIASES[key]
        if team.abbreviation in seen:
            continue
        if _contains_phrase(norm, key):
            hits.append(team)
            seen.add(team.abbreviation)
    if len(hits) == 1:
        return hits[0]
    return None


def _season_type(event: DiscoveryEvent) -> str:
    labels = [event.name]
    for classification in event.classifications:
        labels.extend(classification.labels())
    blob = _normalize(" ".join(labels))
    if "preseason" in blob or "pre season" in blob:
        return "preseason"
    if "playoff" in blob or "play in" in blob:
        return "playoffs"
    if "exhibition" in blob or "all star" in blob:
        return "exhibition"
    return "regular"


def _is_nba(event: DiscoveryEvent) -> bool:
    if not event.classifications:
        return False
    saw_basketball = False
    for classification in event.classifications:
        labels = [_normalize(label) for label in classification.labels()]
        blob = " ".join(labels)
        if "music" in blob or "concert" in blob or "arts" in blob:
            return False
        if "nba" in blob or ("basketball" in blob and "sports" in blob):
            saw_basketball = True
    return saw_basketball


def _zone(name: str | None) -> ZoneInfo:
    if not name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _schedule(event: DiscoveryEvent) -> tuple[datetime, datetime, str] | None:
    dates = event.dates
    if dates is None or dates.start is None or dates.start.date_time is None:
        return None
    start = dates.start.date_time
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    start_utc = start.astimezone(UTC)
    tz_name = dates.timezone or "UTC"
    zone = _zone(tz_name)
    local = start_utc.astimezone(zone)
    if dates.start.local_date and dates.start.local_time:
        try:
            naive = datetime.fromisoformat(f"{dates.start.local_date}T{dates.start.local_time}")
            local = naive.replace(tzinfo=zone)
        except ValueError:
            local = start_utc.astimezone(zone)
    return start_utc, local, tz_name if tz_name else "UTC"


def _status(event: DiscoveryEvent) -> EventStatus:
    code = ""
    if event.dates is not None and event.dates.status is not None and event.dates.status.code:
        code = event.dates.status.code.lower()
    if code in {"cancelled", "canceled"}:
        return EventStatus.CANCELED
    if code == "postponed":
        return EventStatus.POSTPONED
    return EventStatus.SCHEDULED


def _dollars_to_minor(amount: float | None) -> int | None:
    if amount is None:
        return None
    return int(round(amount * 100))


def _venue_side(home: NbaTeam, away: NbaTeam, city: str) -> NbaTeam | None:
    """Return the team whose city the venue matches, when that is unique."""

    venue_city = _normalize(city)
    if not venue_city:
        return None
    home_hit = venue_city == _normalize(home.city)
    away_hit = venue_city == _normalize(away.city)
    if home_hit and not away_hit:
        return home
    if away_hit and not home_hit:
        return away
    return None


@dataclass(frozen=True)
class MatchedEvent:
    provider_event_id: str
    name: str
    home: NbaTeam
    away: NbaTeam
    venue_name: str
    venue_city: str
    venue_state: str
    venue_timezone: str
    start_at_utc: datetime
    local_start_at: datetime
    status: EventStatus
    season_type: str
    matched_method: str
    match_confidence: float
    external_url: str | None
    price_min_minor: int | None
    price_max_minor: int | None
    price_currency: str | None
    observed_at: datetime


def match_discovery_event(event: DiscoveryEvent, *, observed_at: datetime) -> MatchedEvent | None:
    if not _is_nba(event):
        return None
    venue = event.primary_venue()
    if venue is None or not venue.name or not venue.city_name():
        return None
    schedule = _schedule(event)
    if schedule is None:
        return None
    start_utc, local_start, tz_name = schedule

    at_match = _AT.match(event.name.strip())
    vs_match = _VS.match(event.name.strip())
    method: str
    confidence: float
    home: NbaTeam | None
    away: NbaTeam | None

    if at_match:
        away = resolve_team_text(at_match.group(1))
        home = resolve_team_text(at_match.group(2))
        if home is None or away is None or home.abbreviation == away.abbreviation:
            return None
        venue_home = _venue_side(home, away, venue.city_name())
        if venue_home is not None and venue_home.abbreviation != home.abbreviation:
            return None
        method = "title_at_and_venue" if venue_home is not None else "title_at"
        confidence = 0.95 if venue_home is not None else 0.75
    elif vs_match:
        left = resolve_team_text(vs_match.group(1))
        right = resolve_team_text(vs_match.group(2))
        if left is None or right is None or left.abbreviation == right.abbreviation:
            return None
        venue_home = _venue_side(left, right, venue.city_name())
        if venue_home is None:
            return None
        home = venue_home
        away = right if venue_home.abbreviation == left.abbreviation else left
        method = "title_vs_and_venue"
        confidence = 0.9
    else:
        return None

    if home is None or away is None:
        return None

    price = event.price_ranges[0] if event.price_ranges else None
    currency = price.currency if price is not None and price.currency else None
    return MatchedEvent(
        provider_event_id=event.id,
        name=event.name,
        home=home,
        away=away,
        venue_name=venue.name,
        venue_city=venue.city_name(),
        venue_state=venue.state_code() or "",
        venue_timezone=venue.timezone or tz_name,
        start_at_utc=start_utc,
        local_start_at=local_start,
        status=_status(event),
        season_type=_season_type(event),
        matched_method=method,
        match_confidence=confidence,
        external_url=event.url if event.url and event.url.startswith("https://") else None,
        price_min_minor=_dollars_to_minor(price.min) if price is not None else None,
        price_max_minor=_dollars_to_minor(price.max) if price is not None else None,
        price_currency=currency,
        observed_at=observed_at,
    )
