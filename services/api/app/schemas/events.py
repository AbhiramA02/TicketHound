"""Event and offer DTOs for the public API contract."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import DataStatus, Granularity, PriceBasis


class EventStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    POSTPONED = "POSTPONED"
    CANCELED = "CANCELED"
    FINAL = "FINAL"


class TeamSummary(BaseModel):
    id: UUID
    name: str
    abbreviation: str
    city: str


class VenueSummary(BaseModel):
    id: UUID
    name: str
    city: str
    state: str
    timezone: str


class EventSummary(BaseModel):
    id: UUID
    league: str = "NBA"
    home_team: TeamSummary
    away_team: TeamSummary
    venue: VenueSummary
    start_at_utc: datetime
    local_start_at: datetime
    status: EventStatus
    data_status: DataStatus
    lowest_all_in_price_minor: int | None = None
    currency: str | None = None


class Offer(BaseModel):
    id: str
    provider_code: str
    section: str | None = None
    row: str | None = None
    seat_zone: str | None = None
    ticket_count_for_price: int = Field(ge=1)
    all_in_price_minor: int | None = None
    base_price_minor: int | None = None
    currency: str = "USD"
    price_basis: PriceBasis
    granularity: Granularity
    purchase_url: HttpUrl | None = None
    observed_at: datetime
    data_status: DataStatus


class ProviderStatus(BaseModel):
    code: str
    enabled: bool
    data_status: DataStatus
    capabilities: dict[str, bool]
    notes: str | None = None
