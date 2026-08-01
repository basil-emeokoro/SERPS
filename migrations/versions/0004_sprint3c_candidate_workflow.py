"""Sprint 3C candidate pre-examination workflow.

Revision ID: 0004_sprint3c_candidate
Revises: 0003_sprint3b_governance
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_sprint3c_candidate"
down_revision = "0003_sprint3b_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("candidates") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_candidates_user_id_users", "users", ["user_id"], ["user_id"])
        batch_op.create_unique_constraint("uq_candidates_user_id", ["user_id"])

    op.create_table(
        "candidate_consents",
        sa.Column("consent_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("consent_version", sa.String(length=40), nullable=False),
        sa.Column("monitoring_consent", sa.Boolean(), nullable=False),
        sa.Column("privacy_notice_accepted", sa.Boolean(), nullable=False),
        sa.Column("institutional_policy_accepted", sa.Boolean(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_candidate_consents_candidate_id_candidates"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_candidate_consents_institution_id_institutions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_candidate_consents_user_id_users"),
        sa.PrimaryKeyConstraint("consent_id", name="pk_candidate_consents"),
    )
    op.create_index("ix_candidate_consents_candidate_timestamp", "candidate_consents", ["candidate_id", "accepted_at"])
    op.create_index("ix_candidate_consents_institution_candidate", "candidate_consents", ["institution_id", "candidate_id"])

    op.create_table(
        "device_check_records",
        sa.Column("device_check_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("supported_browser", sa.Boolean(), nullable=False),
        sa.Column("secure_context", sa.Boolean(), nullable=False),
        sa.Column("camera_available", sa.Boolean(), nullable=False),
        sa.Column("microphone_available", sa.Boolean(), nullable=False),
        sa.Column("browser_name", sa.String(length=80), nullable=False),
        sa.Column("browser_version", sa.String(length=40), nullable=True),
        sa.Column("operating_system", sa.String(length=120), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_device_check_records_candidate_id_candidates"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_device_check_records_institution_id_institutions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_device_check_records_user_id_users"),
        sa.PrimaryKeyConstraint("device_check_id", name="pk_device_check_records"),
    )
    op.create_index("ix_device_checks_candidate_checked", "device_check_records", ["candidate_id", "checked_at"])
    op.create_index("ix_device_checks_institution_candidate", "device_check_records", ["institution_id", "candidate_id"])
    op.create_index("ix_device_checks_passed", "device_check_records", ["passed"])

    op.create_table(
        "camera_selection_records",
        sa.Column("camera_selection_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("group_id", sa.String(length=255), nullable=True),
        sa.Column("camera_count", sa.Integer(), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("camera_count >= 1", name="ck_camera_selection_records_camera_count_positive"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_camera_selection_records_candidate_id_candidates"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_camera_selection_records_institution_id_institutions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_camera_selection_records_user_id_users"),
        sa.PrimaryKeyConstraint("camera_selection_id", name="pk_camera_selection_records"),
    )
    op.create_index("ix_camera_selections_candidate_selected", "camera_selection_records", ["candidate_id", "selected_at"])
    op.create_index("ix_camera_selections_institution_candidate", "camera_selection_records", ["institution_id", "candidate_id"])

    op.create_table(
        "camera_permission_records",
        sa.Column("camera_permission_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_camera_permission_records_candidate_id_candidates"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_camera_permission_records_institution_id_institutions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_camera_permission_records_user_id_users"),
        sa.PrimaryKeyConstraint("camera_permission_id", name="pk_camera_permission_records"),
    )
    op.create_index("ix_camera_permissions_candidate_checked", "camera_permission_records", ["candidate_id", "checked_at"])
    op.create_index("ix_camera_permissions_institution_candidate", "camera_permission_records", ["institution_id", "candidate_id"])
    op.create_index("ix_camera_permissions_status", "camera_permission_records", ["status"])

    with op.batch_alter_table("examination_sessions") as batch_op:
        batch_op.add_column(sa.Column("consent_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("device_check_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("camera_selection_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("camera_permission_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_sessions_consent", "candidate_consents", ["consent_id"], ["consent_id"])
        batch_op.create_foreign_key("fk_sessions_device_check", "device_check_records", ["device_check_id"], ["device_check_id"])
        batch_op.create_foreign_key("fk_sessions_camera_selection", "camera_selection_records", ["camera_selection_id"], ["camera_selection_id"])
        batch_op.create_foreign_key("fk_sessions_camera_permission", "camera_permission_records", ["camera_permission_id"], ["camera_permission_id"])


def downgrade() -> None:
    with op.batch_alter_table("examination_sessions") as batch_op:
        batch_op.drop_constraint("fk_sessions_camera_permission", type_="foreignkey")
        batch_op.drop_constraint("fk_sessions_camera_selection", type_="foreignkey")
        batch_op.drop_constraint("fk_sessions_device_check", type_="foreignkey")
        batch_op.drop_constraint("fk_sessions_consent", type_="foreignkey")
        batch_op.drop_column("camera_permission_id")
        batch_op.drop_column("camera_selection_id")
        batch_op.drop_column("device_check_id")
        batch_op.drop_column("consent_id")

    op.drop_index("ix_camera_permissions_status", table_name="camera_permission_records")
    op.drop_index("ix_camera_permissions_institution_candidate", table_name="camera_permission_records")
    op.drop_index("ix_camera_permissions_candidate_checked", table_name="camera_permission_records")
    op.drop_table("camera_permission_records")
    op.drop_index("ix_camera_selections_institution_candidate", table_name="camera_selection_records")
    op.drop_index("ix_camera_selections_candidate_selected", table_name="camera_selection_records")
    op.drop_table("camera_selection_records")
    op.drop_index("ix_device_checks_passed", table_name="device_check_records")
    op.drop_index("ix_device_checks_institution_candidate", table_name="device_check_records")
    op.drop_index("ix_device_checks_candidate_checked", table_name="device_check_records")
    op.drop_table("device_check_records")
    op.drop_index("ix_candidate_consents_institution_candidate", table_name="candidate_consents")
    op.drop_index("ix_candidate_consents_candidate_timestamp", table_name="candidate_consents")
    op.drop_table("candidate_consents")

    with op.batch_alter_table("candidates") as batch_op:
        batch_op.drop_constraint("uq_candidates_user_id", type_="unique")
        batch_op.drop_constraint("fk_candidates_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
