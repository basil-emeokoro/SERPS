"""Add privacy-safe structured metadata to EvidenceEvents.

Revision ID: 0008_core_multimodal_evidence
Revises: 0007_sprint4c_config
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_core_multimodal_evidence"
down_revision = "0007_sprint4c_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("evidence_events") as batch_op:
        batch_op.add_column(
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
        )


def downgrade() -> None:
    with op.batch_alter_table("evidence_events") as batch_op:
        batch_op.drop_column("metadata")
