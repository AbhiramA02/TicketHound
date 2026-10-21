"""Aggregate v1 routers."""

from fastapi import APIRouter

from app.api.v1 import events, health, providers, teams

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(teams.router)
api_router.include_router(events.router)
api_router.include_router(providers.router)
