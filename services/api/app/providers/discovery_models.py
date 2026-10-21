"""Subset of Ticketmaster Discovery v2 payloads we actually read.

Extra fields are ignored. Seat-level inventory is not part of this shape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Ignore(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class NamedRef(_Ignore):
    name: str | None = None


class DiscoveryStart(_Ignore):
    date_time: datetime | None = Field(default=None, alias="dateTime")
    local_date: str | None = Field(default=None, alias="localDate")
    local_time: str | None = Field(default=None, alias="localTime")


class DiscoveryDateStatus(_Ignore):
    code: str | None = None


class DiscoveryDates(_Ignore):
    start: DiscoveryStart | None = None
    status: DiscoveryDateStatus | None = None
    timezone: str | None = None


class DiscoveryPriceRange(_Ignore):
    type: str | None = None
    currency: str | None = None
    min: float | None = None
    max: float | None = None


class DiscoveryClassification(_Ignore):
    segment: NamedRef | None = None
    genre: NamedRef | None = None
    sub_genre: NamedRef | None = Field(default=None, alias="subGenre")

    def labels(self) -> list[str]:
        labels: list[str] = []
        for ref in (self.segment, self.genre, self.sub_genre):
            if ref is not None and ref.name:
                labels.append(ref.name)
        return labels


class DiscoveryCity(_Ignore):
    name: str | None = None


class DiscoveryState(_Ignore):
    state_code: str | None = Field(default=None, alias="stateCode")
    name: str | None = None


class DiscoveryVenue(_Ignore):
    name: str | None = None
    city: DiscoveryCity | None = None
    state: DiscoveryState | None = None
    timezone: str | None = None

    def city_name(self) -> str:
        if self.city is None or self.city.name is None:
            return ""
        return self.city.name

    def state_code(self) -> str:
        if self.state is None:
            return ""
        return self.state.state_code or self.state.name or ""


class DiscoveryEventEmbedded(_Ignore):
    venues: list[DiscoveryVenue] = Field(default_factory=list)


class DiscoveryEvent(_Ignore):
    id: str
    name: str
    url: str | None = None
    dates: DiscoveryDates | None = None
    price_ranges: list[DiscoveryPriceRange] = Field(default_factory=list, alias="priceRanges")
    classifications: list[DiscoveryClassification] = Field(default_factory=list)
    embedded: DiscoveryEventEmbedded | None = Field(default=None, alias="_embedded")

    def primary_venue(self) -> DiscoveryVenue | None:
        if self.embedded is None or not self.embedded.venues:
            return None
        return self.embedded.venues[0]


class DiscoverySearchEmbedded(_Ignore):
    events: list[DiscoveryEvent] = Field(default_factory=list)


class DiscoveryPageInfo(_Ignore):
    total_elements: int = Field(default=0, alias="totalElements")
    number: int = 0
    size: int = 0


class DiscoverySearchResponse(_Ignore):
    embedded: DiscoverySearchEmbedded | None = Field(default=None, alias="_embedded")
    page: DiscoveryPageInfo | None = None

    def events(self) -> list[DiscoveryEvent]:
        if self.embedded is None:
            return []
        return self.embedded.events

    def total(self) -> int:
        if self.page is None:
            return len(self.events())
        return self.page.total_elements
