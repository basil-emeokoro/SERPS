"""Sprint 4C institution registration configuration persistence.

Revision ID: 0007_sprint4c_config
Revises: 0006_sprint4b_identity_assurance
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_sprint4c_config"
down_revision = "0006_sprint4b_identity_assurance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("registration_requests") as batch:
        batch.add_column(sa.Column("configured_fields", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("configuration_version", sa.String(length=30), nullable=False, server_default="1.0"))
        batch.add_column(sa.Column("verification_status", sa.String(length=40), nullable=False, server_default="pending_verification"))


def downgrade() -> None:
    with op.batch_alter_table("registration_requests") as batch:
        batch.drop_column("verification_status")
        batch.drop_column("configuration_version")
        batch.drop_column("configured_fields")
