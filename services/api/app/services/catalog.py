"""Catalog orchestration.

DEMO_MODE keeps the synthetic catalog even if a Ticketmaster key is present.
Discovery is queried only when demo mode is off, the provider flag is on, and a key is set.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from app.core.config import Settings
from app.core.errors import AppError
from app.db.nba_teams import NBA_TEAMS
from app.providers.demo import DemoProvider
from app.providers.ticketmaster import TicketmasterDiscoveryClient
from app.schemas.common import (
    ApiResponse,
    DataStatus,
    Granularity,
    PaginatedData,
    PaginationMeta,
    PriceBasis,
    ResponseMeta,
)
from app.schemas.events import EventSummary, Offer, ProviderStatus, TeamDirectoryEntry
from app.services.event_store import MemoryEventStore, SqlEventStore, session_scope
from app.services.matching import MatchedEvent, match_discovery_event

CatalogMode = Literal["demo", "live", "unavailable"]

LIVE_WARNING = (
    "Ticketmaster Discovery event data. This is not a complete NBA schedule, "
    "and prices are event-level ranges, not seat listings."
)
DEMO_WARNING = "Synthetic demonstration data, not purchasable tickets"


class CatalogService:
    def __init__(
        self,
        settings: Settings,
        *,
        store: MemoryEventStore | SqlEventStore | None = None,
        discovery: TicketmasterDiscoveryClient | None = None,
    ) -> None:
        self.settings = settings
        self.demo = DemoProvider()
        self._store = store
        self._discovery = discovery

    def catalog_mode(self) -> CatalogMode:
        if self.settings.demo_mode:
            return "demo"
        if self.settings.provider_ticketmaster_enabled:
            if self.settings.ticketmaster_api_key:
                return "live"
            return "unavailable"
        if self.settings.provider_demo_enabled:
            return "demo"
        return "unavailable"

    def _meta(self, *, status: DataStatus, warning: str | None, demo: bool) -> ResponseMeta:
        return ResponseMeta(
            data_status=status,
            fetched_at=datetime.now(UTC),
            warning=warning,
            demo_mode=demo,
        )

    def _discovery_client(self) -> TicketmasterDiscoveryClient:
        if self._discovery is not None:
            return self._discovery
        key = self.settings.ticketmaster_api_key or ""
        return TicketmasterDiscoveryClient(
            key,
            base_url=self.settings.ticketmaster_base_url,
            min_interval_seconds=self.settings.ticketmaster_min_interval_seconds,
            timeout_seconds=self.settings.ticketmaster_timeout_seconds,
        )

    @contextmanager
    def _store_scope(self) -> Iterator[MemoryEventStore | SqlEventStore]:
        if self._store is not None:
            yield self._store
            return
        with session_scope() as store:
            yield store

    def provider_status(self) -> ApiResponse[list[ProviderStatus]]:
        mode = self.catalog_mode()
        demo_on = mode == "demo"
        statuses = [
            ProviderStatus(
                code="demo",
                enabled=demo_on,
                data_status=DataStatus.DEMO if demo_on else DataStatus.UNAVAILABLE,
                capabilities=self.demo.capabilities.model_dump(),
                notes="Isolated fixture provider for local/portfolio demos",
            ),
            self._ticketmaster_status(mode),
        ]
        if mode == "live":
            meta = self._meta(status=DataStatus.LIVE, warning=LIVE_WARNING, demo=False)
        elif mode == "demo":
            meta = self._meta(status=DataStatus.DEMO, warning=DEMO_WARNING, demo=True)
        else:
            meta = self._meta(
                status=DataStatus.UNAVAILABLE,
                warning=self._unavailable_message(),
                demo=False,
            )
        return ApiResponse(data=statuses, meta=meta)

    def _ticketmaster_status(self, mode: CatalogMode) -> ProviderStatus:
        configured = bool(self.settings.ticketmaster_api_key)
        if mode == "live":
            notes = (
                "Discovery supplies events and event-level price ranges. "
                "It does not supply seat listings."
            )
            status = DataStatus.LIVE
        elif self.settings.provider_ticketmaster_enabled and not configured:
            notes = "Enabled, but TICKETMASTER_API_KEY is empty."
            status = DataStatus.UNAVAILABLE
        elif self.settings.provider_ticketmaster_enabled and self.settings.demo_mode:
            notes = "A key is set, but DEMO_MODE is on so Discovery is not queried."
            status = DataStatus.UNAVAILABLE
        else:
            notes = (
                "Disabled. Set PROVIDER_TICKETMASTER_ENABLED=true and DEMO_MODE=false "
                "to query Discovery."
            )
            status = DataStatus.UNAVAILABLE
        return ProviderStatus(
            code="ticketmaster",
            enabled=self.settings.provider_ticketmaster_enabled and configured and mode == "live",
            data_status=status,
            capabilities=TicketmasterDiscoveryClient.capabilities.model_dump(),
            notes=notes,
        )

    def list_teams(self) -> ApiResponse[list[TeamDirectoryEntry]]:
        teams = [
            TeamDirectoryEntry(
                id=team.id,
                nba_team_id=team.nba_team_id,
                name=team.name,
                abbreviation=team.abbreviation,
                city=team.city,
                aliases=list(team.aliases),
            )
            for team in NBA_TEAMS
        ]
        return ApiResponse(
            data=teams,
            meta=self._meta(
                status=DataStatus.LIVE,
                warning="Canonical NBA team directory used for event matching.",
                demo=self.settings.demo_mode,
            ),
        )

    async def list_events(
        self,
        *,
        team: str | None,
        start: date | None,
        end: date | None,
        page: int,
        page_size: int,
    ) -> ApiResponse[PaginatedData[EventSummary]]:
        self._check_range(start, end)
        mode = self.catalog_mode()
        if mode == "unavailable":
            raise AppError(
                code="provider_unavailable",
                message=self._unavailable_message(),
                status_code=503,
            )
        if mode == "demo":
            items, total = await self.demo.list_events(
                team=team,
                start=start,
                end=end,
                page=page,
                page_size=page_size,
            )
            return ApiResponse(
                data=PaginatedData(
                    items=items,
                    pagination=PaginationMeta(page=page, page_size=page_size, total=total),
                ),
                meta=self._meta(status=DataStatus.DEMO, warning=DEMO_WARNING, demo=True),
            )
        return await self._list_live(
            team=team, start=start, end=end, page=page, page_size=page_size
        )

    async def _list_live(
        self,
        *,
        team: str | None,
        start: date | None,
        end: date | None,
        page: int,
        page_size: int,
    ) -> ApiResponse[PaginatedData[EventSummary]]:
        raw_events, total = await self._discovery_client().search_nba_events(
            keyword=team,
            start=start,
            end=end,
            page=page,
            page_size=page_size,
        )
        observed = datetime.now(UTC)
        stored: list[EventSummary] = []
        omitted = 0
        with self._store_scope() as store:
            store.ensure_teams()
            for raw in raw_events:
                matched = match_discovery_event(raw, observed_at=observed)
                if matched is None:
                    omitted += 1
                    continue
                if not _mentions_team(team, matched):
                    continue
                summary = store.upsert(matched, data_status=DataStatus.LIVE)
                if summary is None:
                    omitted += 1
                    continue
                stored.append(summary)
        stored.sort(key=lambda event: event.start_at_utc)
        warning = LIVE_WARNING
        if omitted:
            warning = (
                f"{warning} {omitted} Discovery result(s) on this page were omitted "
                "because they are not a matched NBA game."
            )
        if not stored:
            warning = (
                f"{warning} No games matched this search. Missing games are omitted "
                "rather than filled from the demo catalog."
            )
        return ApiResponse(
            data=PaginatedData(
                items=stored,
                pagination=PaginationMeta(page=page, page_size=page_size, total=total),
            ),
            meta=self._meta(status=DataStatus.LIVE, warning=warning, demo=False),
        )

    async def get_event(self, event_id: str) -> ApiResponse[EventSummary]:
        mode = self.catalog_mode()
        if mode == "unavailable":
            raise AppError(
                code="provider_unavailable",
                message=self._unavailable_message(),
                status_code=503,
            )
        if mode == "demo":
            event = await self.demo.get_event(event_id)
            if event is None:
                raise AppError(
                    code="event_not_found",
                    message=f"Event {event_id} not found",
                    status_code=404,
                )
            return ApiResponse(
                data=event,
                meta=self._meta(status=DataStatus.DEMO, warning=DEMO_WARNING, demo=True),
            )
        try:
            uid = UUID(event_id)
        except ValueError as exc:
            raise AppError(
                code="event_not_found",
                message=f"Event {event_id} not found",
                status_code=404,
            ) from exc
        with self._store_scope() as store:
            event = store.get(uid)
        if event is None:
            raise AppError(
                code="event_not_found",
                message=f"Event {event_id} not found",
                status_code=404,
            )
        return ApiResponse(
            data=event,
            meta=self._meta(status=DataStatus.CACHED, warning=LIVE_WARNING, demo=False),
        )

    async def get_offers(self, event_id: str, quantity: int) -> ApiResponse[list[Offer]]:
        mode = self.catalog_mode()
        if mode == "unavailable":
            raise AppError(
                code="provider_unavailable",
                message=self._unavailable_message(),
                status_code=503,
            )
        if mode == "demo":
            event = await self.demo.get_event(event_id)
            if event is None:
                raise AppError(
                    code="event_not_found",
                    message=f"Event {event_id} not found",
                    status_code=404,
                )
            offers = await self.demo.get_offers(event_id, quantity=quantity)
            return ApiResponse(
                data=offers,
                meta=self._meta(status=DataStatus.DEMO, warning=DEMO_WARNING, demo=True),
            )
        detail = await self.get_event(event_id)
        event = detail.data
        if event.price_min_minor is None:
            return ApiResponse(
                data=[],
                meta=self._meta(
                    status=DataStatus.CACHED,
                    warning=(
                        "Ticketmaster Discovery did not include a price range for this event. "
                        "Seat listings are not available from Discovery."
                    ),
                    demo=False,
                ),
            )
        observed = event.source_observed_at or datetime.now(UTC)
        offer = Offer.model_validate(
            {
                "id": f"tm-{event.id}-event-range",
                "provider_code": "ticketmaster",
                "section": None,
                "row": None,
                "seat_zone": None,
                "ticket_count_for_price": quantity,
                "all_in_price_minor": None,
                "base_price_minor": event.price_min_minor,
                "currency": event.currency or "USD",
                "price_basis": PriceBasis.FROM_PRICE,
                "granularity": Granularity.EVENT,
                "purchase_url": event.source_url,
                "observed_at": observed,
                "data_status": DataStatus.CACHED,
            }
        )
        return ApiResponse(
            data=[offer],
            meta=self._meta(
                status=DataStatus.CACHED,
                warning=(
                    "Event-level price range from Ticketmaster Discovery. "
                    "This is not a section, row, or seat listing, and it is not an all-in price."
                ),
                demo=False,
            ),
        )

    def _unavailable_message(self) -> str:
        if self.settings.provider_ticketmaster_enabled and not self.settings.ticketmaster_api_key:
            return (
                "Ticketmaster Discovery is enabled but TICKETMASTER_API_KEY is not configured."
            )
        return "No enabled event providers"

    def _check_range(self, start: date | None, end: date | None) -> None:
        if start is not None and end is not None and start > end:
            raise AppError(
                code="invalid_filters",
                message="start must be on or before end",
                status_code=400,
            )


def _mentions_team(team: str | None, matched: MatchedEvent) -> bool:
    if not team or not team.strip():
        return True
    needle = team.strip().lower()
    haystack = " ".join(
        (
            matched.home.name,
            matched.away.name,
            matched.home.abbreviation,
            matched.away.abbreviation,
            matched.home.city,
            matched.away.city,
            " ".join(matched.home.aliases),
            " ".join(matched.away.aliases),
        )
    ).lower()
    return needle in haystack
