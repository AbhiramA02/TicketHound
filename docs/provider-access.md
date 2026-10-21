# Provider access status

**Last updated:** 2026-10-21 (Phase 0)  
**Rule:** Never label DEMO/fixture data as LIVE. No scraping. Secrets stay out of git.

## Summary

| Provider | Enabled flag | Credentials | Verified endpoints | Usable in Phase 0 | Notes |
| --- | --- | --- | --- | --- | --- |
| **DEMO** (fixtures) | `PROVIDER_DEMO_ENABLED` / `DEMO_MODE` | none | in-process | **Yes** | Isolated synthetic games/offers; conspicuous UI labels |
| **Ticketmaster Discovery v2** | `PROVIDER_TICKETMASTER_ENABLED` | `TICKETMASTER_API_KEY` **TBD** | not verified in this repo yet | No (Phase 1) | Official Discovery API for events; seat inventory needs partner APIs |
| SeatGeek | n/a | TBD | not verified | No | Check enrollment before Phase 2 |
| StubHub | n/a | TBD | not verified | No | Verify granularity before Phase 2 |

## DEMO provider

- Code: `services/api/app/providers/demo.py`
- Returns `data_status: DEMO` on every event/offer
- API meta warning: *"Synthetic demonstration data, not purchasable tickets"*
- UI: yellow **DEMO DATA** banner on home, games list, and game detail

## Ticketmaster (Phase 1 stub)

- Official docs: [Discovery API v2](https://developer.ticketmaster.com/products-and-docs/apis/discovery/v2/)
- Documented rate limits vary (FAQ vs main docs); implement configurable throttling when integrating
- Listing/seat inventory typically requires partner-enabled APIs — Discovery alone is **not** seat-by-seat inventory
- Credentials: not configured in Phase 0; leave `TICKETMASTER_API_KEY` empty and `PROVIDER_TICKETMASTER_ENABLED=false`

## Feature accessibility (honest)

| Feature | Status |
| --- | --- |
| Browse/search demo NBA games | Available (DEMO) |
| Demo offer table with all-in cents | Available (DEMO) |
| Live event discovery | Phase 1 — needs API key |
| Live granular listings | Phase 2 — needs permitted offer API |
| Price history | Phase 3 |
| Auth / alerts | Phase 5 |

## How to update this file

When a credential is obtained or an endpoint is smoke-tested:

1. Record date, scopes, rate limits observed, and which DTOs can be filled honestly.
2. Flip the corresponding `PROVIDER_*_ENABLED` only after adapter tests pass with recorded fixtures.
3. Never commit the key — only document that it exists in the operator’s secret store.
