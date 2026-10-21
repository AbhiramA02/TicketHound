"""Health and readiness endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.db.session import check_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    db_ok = check_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.app_name,
        "version": __version__,
        "demo_mode": settings.demo_mode,
        "database": "up" if db_ok else "down",
        "checked_at": datetime.now(UTC).isoformat(),
    }
