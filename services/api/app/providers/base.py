"""Provider capability contract (Phase 0 — protocol + capabilities only)."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas.events import EventSummary, Offer


class ProviderCapabilities(BaseModel):
    search_events: bool = False
    event_price_summary: bool = False
    granular_offers: bool = False
    all_in_prices: bool = False
    seat_locations: bool = False
    purchase_deep_links: bool = False


class TicketProvider(Protocol):
    name: str
    code: str
    capabilities: ProviderCapabilities

    async def list_events(
        self,
        *,
        team: str | None = None,
        start: date | None = None,
        end: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[EventSummary], int]: ...

    async def get_event(self, event_id: str) -> EventSummary | None: ...

    async def get_offers(self, event_id: str, quantity: int = 2) -> list[Offer]: ...


class ProviderRegistryEntry(BaseModel):
    code: str
    name: str
    enabled: bool
    capabilities: ProviderCapabilities
    notes: str | None = Field(default=None)
