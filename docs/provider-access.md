# Provider access status

**Last updated:** 2026-10-21 (Phase 1)  
**Rule:** Never label DEMO/fixture data as LIVE. No scraping. Secrets stay out of git.

## Summary

| Provider | Enabled flag | Credentials | Verified endpoints | Usable in Phase 0 | Notes |
| --- | --- | --- | --- | --- | --- |
| **DEMO** (fixtures) | `PROVIDER_DEMO_ENABLED` / `DEMO_MODE` | none | in-process | **Yes** | Isolated synthetic games/offers; conspicuous UI labels |
| **Ticketmaster Discovery v2** | `PROVIDER_TICKETMASTER_ENABLED` | `TICKETMASTER_API_KEY` in the operator env, never in git | `GET /discovery/v2/events.json` with `classificationName=NBA` | When `DEMO_MODE=false`, the flag is true, and a key is set | Event search and event-level `priceRanges` only. Default throttle is 2 requests/second (`TICKETMASTER_MIN_INTERVAL_SECONDS=0.5`). Seat inventory is a partner API and is not called. |
| SeatGeek | n/a | TBD | not verified | No | Check enrollment before Phase 2 |
| StubHub | n/a | TBD | not verified | No | Verify granularity before Phase 2 |

## DEMO provider

- Code: `services/api/app/providers/demo.py`
- Returns `data_status: DEMO` on every event/offer
- API meta warning: *"Synthetic demonstration data, not purchasable tickets"*
- UI: yellow **DEMO DATA** banner on home, games list, and game detail

## Ticketmaster Discovery (Phase 1)

- Code: `services/api/app/providers/ticketmaster.py`
- Official docs: [Discovery API v2](https://developer.ticketmaster.com/products-and-docs/apis/discovery/v2/)
- Server-side `GET /discovery/v2/events.json` (`apikey`, `classificationName=NBA`, optional `keyword`, `startDateTime`, `endDateTime`, `sort=date,asc`)
- Recorded contract fixture: `fixtures/ticketmaster/events_search.json` (no key)
- Throttle: configurable, default 0.5s between calls. `429` becomes HTTP 429. Other upstream failures become HTTP 503. The key is not included in error messages.
- Canonical rows land in `events` and `provider_events`. The same Discovery id updates one game across a reschedule.
- Home/away comes from `Away at Home`, checked against venue city. `vs` does not set home by word order.
- A non-NBA classification (for example a concert) is dropped. Coverage is not claimed to be the full NBA schedule.
- Credentials: set `TICKETMASTER_API_KEY` locally. Do not commit it.

## Feature accessibility (honest)

| Feature | Status |
| --- | --- |
| Browse/search demo NBA games | Available when `DEMO_MODE=true` (default) |
| Demo offer table with all-in cents | Available (DEMO) |
| Live event discovery | Available when Discovery is configured; otherwise `UNAVAILABLE`, not fake LIVE |
| Live granular listings | Phase 2 — Discovery does not provide them |
| Price history | Phase 3 |
| Auth / alerts | Phase 5 |

## How to update this file

When a credential is obtained or an endpoint is smoke-tested:

1. Record date, scopes, rate limits observed, and which DTOs can be filled honestly.
2. Flip the corresponding `PROVIDER_*_ENABLED` only after adapter tests pass with recorded fixtures.
3. Never commit the key — only document that it exists in the operator’s secret store.
