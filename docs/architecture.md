# TicketHound architecture (Phase 0)

```text
Next.js (apps/web)  --HTTP JSON-->  FastAPI (services/api)
                                         |
                                         +--> DEMO provider (fixtures)
                                         +--> Postgres (schema scaffold)
                                         +--> Ticketmaster stub (disabled)
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
| `services/api/app/providers` | Adapter protocol + DEMO |
| `services/api/app/services` | Orchestration / flags |
| `services/api/migrations` | Alembic |
| `compose.yaml` | Postgres + API + web |

## Phase 0 intentionally deferred

Redis, Celery, auth, live Ticketmaster client, scoring, alerts, ML.
