"""Phase 1 discovery: season type, provider events, NBA team seed.

Revision ID: 20261021_0002
Revises: 20261021_0001
Create Date: 2026-10-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.db.nba_teams import NBA_TEAMS

revision: str = "20261021_0002"
down_revision: str | None = "20261021_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("season_type", sa.String(16), server_default="regular", nullable=False),
    )
    op.create_table(
        "provider_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("provider_code", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(128), nullable=False),
        sa.Column("external_url", sa.String(512), nullable=True),
        sa.Column("matched_method", sa.String(64), nullable=False),
        sa.Column("match_confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_min_minor", sa.Integer(), nullable=True),
        sa.Column("price_max_minor", sa.Integer(), nullable=True),
        sa.Column("price_currency", sa.String(8), nullable=True),
        sa.UniqueConstraint(
            "provider_code",
            "provider_event_id",
            name="uq_provider_events_provider_event",
        ),
    )
    op.create_index("ix_provider_events_event_id", "provider_events", ["event_id"])

    teams = sa.table(
        "teams",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("nba_team_id", sa.String),
        sa.column("name", sa.String),
        sa.column("abbreviation", sa.String),
        sa.column("city", sa.String),
        sa.column("aliases", sa.Text),
        sa.column("active", sa.String),
    )
    op.bulk_insert(teams, [team.row() for team in NBA_TEAMS])


def downgrade() -> None:
    op.drop_index("ix_provider_events_event_id", table_name="provider_events")
    op.drop_table("provider_events")
    op.drop_column("events", "season_type")
    conn = op.get_bind()
    for team in NBA_TEAMS:
        conn.execute(
            sa.text("DELETE FROM events WHERE home_team_id = :id OR away_team_id = :id"),
            {"id": team.id},
        )
        conn.execute(sa.text("DELETE FROM teams WHERE id = :id"), {"id": team.id})
