"""Provider status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.common import ApiResponse
from app.schemas.events import ProviderStatus
from app.services.catalog import CatalogService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status")
def providers_status(
    settings: Settings = Depends(get_settings),
) -> ApiResponse[list[ProviderStatus]]:
    return CatalogService(settings).provider_status()
