# TicketHound API

FastAPI backend for TicketHound (Phase 0 foundation).

## Local (without Docker)

```bash
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://tickethound:tickethound@localhost:5432/tickethound
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest
ruff check app tests
```
