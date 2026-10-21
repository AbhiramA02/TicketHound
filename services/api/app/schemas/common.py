"""Shared response envelope and provenance types."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class DataStatus(StrEnum):
    LIVE = "LIVE"
    CACHED = "CACHED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class PriceBasis(StrEnum):
    ALL_IN = "ALL_IN"
    BASE = "BASE"
    FROM_PRICE = "FROM_PRICE"
    UNKNOWN = "UNKNOWN"


class Granularity(StrEnum):
    EVENT = "EVENT"
    SECTION = "SECTION"
    LISTING = "LISTING"


class ResponseMeta(BaseModel):
    data_status: DataStatus
    fetched_at: datetime
    warning: str | None = None
    demo_mode: bool = False


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
