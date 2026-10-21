"""Event list/detail/offers routes (Phase 0 demo-backed)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.events import EventSummary, Offer
from app.services.catalog import CatalogService

router = APIRouter(prefix="/events", tags=["events"])


def get_catalog(settings: Settings = Depends(get_settings)) -> CatalogService:
    return CatalogService(settings)


@router.get("")
async def list_events(
    team: str | None = Query(default=None, description="Team name, city, or abbreviation"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    catalog: CatalogService = Depends(get_catalog),
) -> ApiResponse[PaginatedData[EventSummary]]:
    return await catalog.list_events(team=team, page=page, page_size=page_size)


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    catalog: CatalogService = Depends(get_catalog),
) -> ApiResponse[EventSummary]:
    return await catalog.get_event(event_id)


@router.get("/{event_id}/offers")
async def get_offers(
    event_id: str,
    quantity: int = Query(default=2, ge=1, le=8),
    catalog: CatalogService = Depends(get_catalog),
) -> ApiResponse[list[Offer]]:
    return await catalog.get_offers(event_id, quantity=quantity)
