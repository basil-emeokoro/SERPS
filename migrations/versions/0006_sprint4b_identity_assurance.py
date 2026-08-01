"""Sprint 4B identity assurance and registration lifecycle.

Revision ID: 0006_sprint4b_identity_assurance
Revises: 0005_sprint3d_dual_camera
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_sprint4b_identity_assurance"
down_revision = "0005_sprint3d_dual_camera"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registration_requests",
        sa.Column("registration_id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.institution_id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("account_type", sa.String(30), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("candidate_identifier", sa.String(80), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("prototype_verified", sa.Boolean(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("institution_id", "email", "account_type", name="uq_registration_identity_type"),
    )
    op.create_index("ix_registration_institution_status", "registration_requests", ["institution_id", "status"])
    op.create_table(
        "identity_assurance_profiles",
        sa.Column("profile_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("registration_id", sa.String(36), sa.ForeignKey("registration_requests.registration_id"), nullable=True),
        sa.Column("biometric_required", sa.Boolean(), nullable=False),
        sa.Column("demo_bypass", sa.Boolean(), nullable=False),
        sa.Column("enrolment_status", sa.String(30), nullable=False),
        sa.Column("authentication_result", sa.String(30), nullable=False),
        sa.Column("identity_confidence", sa.Float(), nullable=True),
        sa.Column("liveness_result", sa.String(30), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "biometric_enrollments",
        sa.Column("enrollment_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("representation_json", sa.JSON(), nullable=False),
        sa.Column("representation_hash", sa.String(64), nullable=False),
        sa.Column("capture_summary", sa.JSON(), nullable=False),
        sa.Column("capture_count", sa.Integer(), nullable=False),
        sa.Column("liveness_confidence", sa.Float(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_biometric_enrollment_user_status", "biometric_enrollments", ["user_id", "status"])
    op.create_table(
        "identity_challenges",
        sa.Column("challenge_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("required_actions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_identity_challenge_user_purpose", "identity_challenges", ["user_id", "purpose", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_identity_challenge_user_purpose", table_name="identity_challenges")
    op.drop_table("identity_challenges")
    op.drop_index("ix_biometric_enrollment_user_status", table_name="biometric_enrollments")
    op.drop_table("biometric_enrollments")
    op.drop_table("identity_assurance_profiles")
    op.drop_index("ix_registration_institution_status", table_name="registration_requests")
    op.drop_table("registration_requests")
