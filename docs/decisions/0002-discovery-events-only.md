# ADR 0002 — Discovery is event search, not inventory

## Status

Accepted — 2026-10-21

## Context

Phase 1 needs real NBA games. Ticketmaster Discovery v2 can search events and sometimes returns an event-level price range. Seat and listing inventory is a separate partner API this project does not have.

## Decision

Call Discovery only from the API process, behind `DEMO_MODE=false`, `PROVIDER_TICKETMASTER_ENABLED`, and `TICKETMASTER_API_KEY`. Persist canonical games plus `provider_events`. Surface a price only as `FROM_PRICE` at `EVENT` granularity. Keep the demo catalog on its own path so fixture rows are never labeled LIVE.

Throttle at 2 requests/second by default because Discovery's FAQ is stricter than the main rate-limit page.

## Consequences

- Users can search a team and open a future game when Discovery returns one.
- Missing games stay missing. There is no second schedule feed in this phase.
- Offer comparison across marketplaces remains Phase 2.
