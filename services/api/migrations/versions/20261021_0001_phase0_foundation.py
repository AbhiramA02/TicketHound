"""Phase 0 foundation tables

Revision ID: 20261021_0001
Revises:
Create Date: 2026-10-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261021_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nba_team_id", sa.String(32), unique=True, nullable=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("abbreviation", sa.String(8), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("active", sa.String(8), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "venues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("state", sa.String(64), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("league", sa.String(16), server_default="NBA"),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("away_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), server_default="SCHEDULED"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "home_team_id",
            "away_team_id",
            "start_at_utc",
            name="uq_events_home_away_start",
        ),
    )
    op.create_index("ix_events_start_at_utc", "events", ["start_at_utc"])


def downgrade() -> None:
    op.drop_index("ix_events_start_at_utc", table_name="events")
    op.drop_table("events")
    op.drop_table("venues")
    op.drop_table("teams")
