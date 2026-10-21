# TicketHound architecture (Phase 1)

Discovery search is `GET https://app.ticketmaster.com/discovery/v2/events.json` from the API process only. The browser calls `/api/v1/events`. `/v2` is Ticketmaster's API version, not ours.

`DEMO_MODE=true` keeps the synthetic catalog even if a key is present. With demo mode off, the Ticketmaster flag on, and a key set, list results are `LIVE` and a later read of the same canonical id is `CACHED`. A missing key or upstream failure is `UNAVAILABLE` and does not fall back to demo rows.

Seat listings are out of scope. A Discovery `priceRanges` value is stored as an event-level `FROM_PRICE` range.

```text
Next.js (apps/web)  --HTTP JSON-->  FastAPI (services/api)
                                         |
                                         +--> DEMO provider (fixtures), when DEMO_MODE
                                         +--> Ticketmaster Discovery v2, when flagged on with a key
                                         +--> Postgres (teams, venues, events, provider_events)
```

## Boundaries

- Browser never talks to marketplace APIs; only to our API.
- Providers normalize into shared Pydantic DTOs (`EventSummary`, `Offer`).
- Response envelope always includes `meta.data_status` (`LIVE`/`CACHED`/`DEMO`/`UNAVAILABLE`).
- DEMO is a separate module — not a branch inside a “live” client.

## Key packages

| Path | Role |
| --- | --- |
| `apps/web` | App Router UI, typed `lib/api.ts` client |
| `services/api/app/api/v1` | HTTP routes |
| `services/api/app/providers` | DEMO adapter and Ticketmaster Discovery client |
| `services/api/app/services` | Catalog mode, NBA matching, event upsert |
| `services/api/migrations` | Alembic |
| `compose.yaml` | Postgres + API + web |

## Phase 1 intentionally deferred

Redis, Celery, auth, seat-level inventory, scoring, alerts, ML. A second schedule feed is not included; missing Discovery games stay missing.
