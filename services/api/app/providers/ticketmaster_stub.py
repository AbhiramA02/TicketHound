"""Ticketmaster Discovery stub — Phase 1 placeholder only.

Do not call external APIs from this module in Phase 0.
"""

from __future__ import annotations

from app.providers.base import ProviderCapabilities


class TicketmasterDiscoveryStub:
    """Disabled until PROVIDER_TICKETMASTER_ENABLED and a real API key exist."""

    name = "Ticketmaster Discovery"
    code = "ticketmaster"
    capabilities = ProviderCapabilities(
        search_events=False,
        event_price_summary=False,
        granular_offers=False,
        all_in_prices=False,
        seat_locations=False,
        purchase_deep_links=False,
    )

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    @property
    def configured(self) -> bool:
        return bool(self._api_key)
