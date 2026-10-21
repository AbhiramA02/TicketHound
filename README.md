# TicketHound

> Stop opening five tabs to buy NBA tickets. TicketHound helps fans find affordable NBA game tickets across supported marketplaces, compares seat value, tracks price history, and eventually estimates when buying may be advantageous.

**Phase:** 1 — NBA event discovery (DEMO by default; Ticketmaster Discovery when configured)  
**Stack:** Next.js (TypeScript) · FastAPI · PostgreSQL · Docker Compose

## Quick start

```bash
git clone <this-repo> TicketHound && cd TicketHound
cp .env.example .env
docker compose up --build
```

Then open:

- Web UI: [http://127.0.0.1:43123](http://127.0.0.1:43123) — conspicuously labeled **DEMO DATA**
- API health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Default Compose credentials are local-only (`tickethound` / `tickethound`). Never put real API keys in git.

**Compose networking:** the default `compose.yaml` uses Linux **host networking** so API↔Postgres works in constrained Docker environments. On Docker Desktop (macOS/Windows), use:

```bash
docker compose -f compose.bridge.yaml up --build
```

### Verified locally (Phase 0)

```text
curl http://127.0.0.1:8000/api/v1/health
→ status=ok, demo_mode=true, database=up

curl http://127.0.0.1:8000/api/v1/events
→ meta.data_status=DEMO, 3 synthetic games

curl -I http://127.0.0.1:43123/
→ 200, page contains "DEMO DATA" + TicketHound brand

cd services/api && ruff check app tests && pytest -q
→ All checks passed; 6 passed
```

## Without rebuilding the web image (dev)

```bash
# Terminal A — database
docker compose up db -d

# Terminal B — API
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://tickethound:tickethound@localhost:5432/tickethound
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal C — Web
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

## Tests & checks

```bash
# API
cd services/api && pip install -e ".[dev]" && ruff check app tests && pytest -q

# Web
cd apps/web && npm ci && npm run lint && npm run typecheck && npm run build
```

CI runs the same gates on push/PR (see `.github/workflows/ci.yml`).

## Data integrity

| Status | Meaning |
| --- | --- |
| `LIVE` | Authenticated provider response for this request |
| `CACHED` | Real provider data with observed timestamp |
| `DEMO` | Synthetic fixtures (Phase 0 default) |
| `UNAVAILABLE` | Disabled / failing / not integrated |

Flags: `DEMO_MODE`, `PROVIDER_DEMO_ENABLED`, `PROVIDER_TICKETMASTER_ENABLED`.

Discovery runs only when `DEMO_MODE=false`, `PROVIDER_TICKETMASTER_ENABLED=true`, and `TICKETMASTER_API_KEY` is set. Otherwise the UI stays on the labeled DEMO catalog. Discovery returns events and, at most, an event-level price range. It does not return seat listings.

## Docs

- [`docs/provider-access.md`](docs/provider-access.md) — credentials TBD, DEMO vs live
- [`docs/architecture.md`](docs/architecture.md) — boundaries
- [`docs/roadmap.md`](docs/roadmap.md) — phases 0→8

## Repo layout

```text
apps/web/           Next.js UI
services/api/       FastAPI + Alembic + DEMO provider
docs/               In-repo engineering docs
fixtures/           Shared fixture notes
compose.yaml        Postgres + API + web
.env.example        Safe sample env
```

## What Phase 0 does **not** include

Live Ticketmaster seat inventory, real marketplace listings, auth, alerts, Redis/Celery, ML. Discovery event search is included when a key is configured; without one, the app stays on DEMO.
