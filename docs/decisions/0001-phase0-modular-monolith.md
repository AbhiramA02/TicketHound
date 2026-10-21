# ADR 0001 — Modular monolith for Phase 0

## Status

Accepted — 2026-10-21

## Context

TicketHound needs a portfolio-quality foundation that Abhiram can explain, without premature microservices.

## Decision

Ship a monorepo modular monolith: Next.js UI + FastAPI API + Postgres, with provider adapters behind a protocol. DEMO is isolated. No Redis/Celery until ingestion (Phase 3).

## Consequences

- Simple local Compose story
- Clear path to add Ticketmaster in Phase 1 without rewriting UI contracts
- Avoids ops complexity that does not teach the core domain yet
