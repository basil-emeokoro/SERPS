"""auth rbac examination session foundation

Revision ID: 0002_auth_rbac_exam
Revises: 0001_initial
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth_rbac_exam"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("institution_type", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("institution_id", name="pk_institutions"),
        sa.UniqueConstraint("code", name="uq_institutions_code"),
    )
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("role_id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_users_institution_id_institutions"),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.UniqueConstraint("institution_id", "email", name="uq_users_institution_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_institution_status", "users", ["institution_id", "status"])
    op.create_table(
        "user_roles",
        sa.Column("user_role_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], name="fk_user_roles_role_id_roles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_role_id", name="pk_user_roles"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_table(
        "candidates",
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_identifier", sa.String(length=80), nullable=False),
        sa.Column("identifier_type", sa.String(length=40), nullable=False),
        sa.Column("full_name", sa.String(length=180), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("matric_number", sa.String(length=80), nullable=True),
        sa.Column("registration_number", sa.String(length=120), nullable=True),
        sa.Column("centre_number", sa.String(length=20), nullable=True),
        sa.Column("candidate_number", sa.String(length=20), nullable=True),
        sa.Column("programme", sa.String(length=120), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("profile_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_candidates_institution_id_institutions"),
        sa.PrimaryKeyConstraint("candidate_id", name="pk_candidates"),
        sa.UniqueConstraint("institution_id", "candidate_identifier", name="uq_candidates_institution_identifier"),
        sa.UniqueConstraint("institution_id", "email", name="uq_candidates_institution_email"),
        sa.UniqueConstraint("institution_id", "matric_number", name="uq_candidates_institution_matric_number"),
        sa.UniqueConstraint("institution_id", "registration_number", name="uq_candidates_institution_registration_number"),
    )
    op.create_index("ix_candidates_institution_status", "candidates", ["institution_id", "status"])
    op.create_table(
        "examinations",
        sa.Column("examination_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("exam_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("monitoring_mode", sa.String(length=10), nullable=False),
        sa.Column("policy_profile", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_examinations_institution_id_institutions"),
        sa.PrimaryKeyConstraint("examination_id", name="pk_examinations"),
        sa.UniqueConstraint("institution_id", "exam_code", name="uq_examinations_institution_exam_code"),
    )
    op.create_index("ix_examinations_institution_status", "examinations", ["institution_id", "status"])
    op.create_table(
        "candidate_examination_assignments",
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("examination_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_assignments_candidate"),
        sa.ForeignKeyConstraint(["examination_id"], ["examinations.examination_id"], name="fk_assignments_exam"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_assignments_institution"),
        sa.PrimaryKeyConstraint("assignment_id", name="pk_assignments"),
        sa.UniqueConstraint("candidate_id", "examination_id", name="uq_candidate_exam_assignment"),
    )
    op.create_index("ix_assignments_institution_status", "candidate_examination_assignments", ["institution_id", "status"])
    op.create_table(
        "examination_sessions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("examination_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("deployment_mode", sa.String(length=10), nullable=False),
        sa.Column("authentication_gate_status", sa.String(length=40), nullable=False),
        sa.Column("device_check_status", sa.String(length=40), nullable=False),
        sa.Column("monitoring_status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["candidate_examination_assignments.assignment_id"], name="fk_sessions_assignment"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_sessions_candidate"),
        sa.ForeignKeyConstraint(["examination_id"], ["examinations.examination_id"], name="fk_sessions_exam"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_sessions_institution"),
        sa.PrimaryKeyConstraint("session_id", name="pk_examination_sessions"),
    )
    op.create_index("ix_examination_sessions_candidate_status", "examination_sessions", ["candidate_id", "status"])
    op.create_index("ix_examination_sessions_institution_status", "examination_sessions", ["institution_id", "status"])
    op.create_table(
        "authentication_sessions",
        sa.Column("authentication_session_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("candidate_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_auth_sessions_candidate"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_auth_sessions_institution"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_authentication_sessions_user_id_users"),
        sa.PrimaryKeyConstraint("authentication_session_id", name="pk_authentication_sessions"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("refresh_token_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("replaced_by_token_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_refresh_tokens_institution_id_institutions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_refresh_tokens_user_id_users"),
        sa.PrimaryKeyConstraint("refresh_token_id", name="pk_refresh_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_table(
        "audit_logs",
        sa.Column("audit_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.user_id"], name="fk_audit_logs_actor_user_id_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_audit_logs_institution_id_institutions"),
        sa.PrimaryKeyConstraint("audit_id", name="pk_audit_logs"),
    )
    op.create_index("ix_audit_logs_action_result", "audit_logs", ["action", "result"])
    op.create_index("ix_audit_logs_institution_timestamp", "audit_logs", ["institution_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_institution_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_result", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("authentication_sessions")
    op.drop_index("ix_examination_sessions_institution_status", table_name="examination_sessions")
    op.drop_index("ix_examination_sessions_candidate_status", table_name="examination_sessions")
    op.drop_table("examination_sessions")
    op.drop_index("ix_assignments_institution_status", table_name="candidate_examination_assignments")
    op.drop_table("candidate_examination_assignments")
    op.drop_index("ix_examinations_institution_status", table_name="examinations")
    op.drop_table("examinations")
    op.drop_index("ix_candidates_institution_status", table_name="candidates")
    op.drop_table("candidates")
    op.drop_table("user_roles")
    op.drop_index("ix_users_institution_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("institutions")
