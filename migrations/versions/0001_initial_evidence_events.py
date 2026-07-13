"""initial evidence events

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_events",
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_module", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("risk_weight", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("camera_id", sa.String(length=80), nullable=True),
        sa.Column("evidence_path", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("event_id", name="pk_evidence_events"),
    )
    op.create_index("ix_evidence_events_session_id", "evidence_events", ["session_id"])
    op.create_index("ix_evidence_events_candidate_id", "evidence_events", ["candidate_id"])
    op.create_index("ix_evidence_events_timestamp", "evidence_events", ["timestamp"])
    op.create_index("ix_evidence_events_source_module", "evidence_events", ["source_module"])
    op.create_index("ix_evidence_events_event_type", "evidence_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_evidence_events_event_type", table_name="evidence_events")
    op.drop_index("ix_evidence_events_source_module", table_name="evidence_events")
    op.drop_index("ix_evidence_events_timestamp", table_name="evidence_events")
    op.drop_index("ix_evidence_events_candidate_id", table_name="evidence_events")
    op.drop_index("ix_evidence_events_session_id", table_name="evidence_events")
    op.drop_table("evidence_events")
