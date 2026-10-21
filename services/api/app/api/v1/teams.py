"""NBA team directory."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.common import ApiResponse
from app.schemas.events import TeamDirectoryEntry
from app.services.catalog import CatalogService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(
    settings: Settings = Depends(get_settings),
) -> ApiResponse[list[TeamDirectoryEntry]]:
    return CatalogService(settings).list_teams()
