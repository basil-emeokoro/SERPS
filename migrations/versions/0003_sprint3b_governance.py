"""Sprint 3B governance backend records.

Revision ID: 0003_sprint3b_governance
Revises: 0002_auth_rbac_exam
Create Date: 2026-07-19
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_sprint3b_governance"
down_revision = "0002_auth_rbac_exam"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contextual_assessments",
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_event_ids", sa.JSON(), nullable=False),
        sa.Column("rule_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_contextual_assessments_assessment_confidence_range"),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="ck_contextual_assessments_risk_score_range"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], name="fk_contextual_assessments_candidate_id_candidates"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], name="fk_contextual_assessments_created_by_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_contextual_assessments_institution_id_institutions"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_contextual_assessments_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("assessment_id", name="pk_contextual_assessments"),
    )
    op.create_index("ix_contextual_assessments_institution_session", "contextual_assessments", ["institution_id", "session_id"])
    op.create_index("ix_contextual_assessments_session_calculated", "contextual_assessments", ["session_id", "calculated_at"])
    op.create_index("ix_contextual_assessments_status", "contextual_assessments", ["status"])

    op.create_table(
        "agent_recommendations",
        sa.Column("recommendation_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recommended_action", sa.String(length=60), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("requires_reviewer", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_agent_recommendations_recommendation_confidence_range"),
        sa.ForeignKeyConstraint(["assessment_id"], ["contextual_assessments.assessment_id"], name="fk_agent_recommendations_assessment_id_contextual_assessments"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], name="fk_agent_recommendations_created_by_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_agent_recommendations_institution_id_institutions"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_agent_recommendations_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("recommendation_id", name="pk_agent_recommendations"),
    )
    op.create_index("ix_agent_recommendations_institution_session", "agent_recommendations", ["institution_id", "session_id"])
    op.create_index("ix_agent_recommendations_session_created", "agent_recommendations", ["session_id", "created_at"])
    op.create_index("ix_agent_recommendations_status", "agent_recommendations", ["status"])

    op.create_table(
        "institutional_policies",
        sa.Column("policy_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("policy_version", sa.String(length=40), nullable=False),
        sa.Column("high_risk_action", sa.String(length=60), nullable=False),
        sa.Column("critical_risk_action", sa.String(length=60), nullable=False),
        sa.Column("reviewer_notification_threshold", sa.String(length=20), nullable=False),
        sa.Column("candidate_acknowledgement_required", sa.Boolean(), nullable=False),
        sa.Column("reauthentication_threshold", sa.String(length=20), nullable=False),
        sa.Column("automatic_exam_termination_allowed", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.CheckConstraint("automatic_exam_termination_allowed = false", name="ck_institutional_policies_automatic_termination_prohibited"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], name="fk_institutional_policies_created_by_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_institutional_policies_institution_id_institutions"),
        sa.PrimaryKeyConstraint("policy_id", name="pk_institutional_policies"),
    )
    op.create_index("ix_institutional_policies_created_at", "institutional_policies", ["created_at"])
    op.create_index("ix_institutional_policies_institution_status", "institutional_policies", ["institution_id", "status"])

    op.create_table(
        "policy_evaluations",
        sa.Column("evaluation_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("recommendation_id", sa.String(length=36), nullable=False),
        sa.Column("policy_id", sa.String(length=36), nullable=False),
        sa.Column("evaluated_by", sa.String(length=36), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_action", sa.String(length=60), nullable=False),
        sa.Column("requires_reviewer", sa.Boolean(), nullable=False),
        sa.Column("requires_candidate_acknowledgement", sa.Boolean(), nullable=False),
        sa.Column("continue_examination", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["evaluated_by"], ["users.user_id"], name="fk_policy_evaluations_evaluated_by_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_policy_evaluations_institution_id_institutions"),
        sa.ForeignKeyConstraint(["policy_id"], ["institutional_policies.policy_id"], name="fk_policy_evaluations_policy_id_institutional_policies"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["agent_recommendations.recommendation_id"], name="fk_policy_evaluations_recommendation_id_agent_recommendations"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_policy_evaluations_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("evaluation_id", name="pk_policy_evaluations"),
    )
    op.create_index("ix_policy_evaluations_institution_session", "policy_evaluations", ["institution_id", "session_id"])
    op.create_index("ix_policy_evaluations_session_evaluated", "policy_evaluations", ["session_id", "evaluated_at"])
    op.create_index("ix_policy_evaluations_status", "policy_evaluations", ["status"])

    op.create_table(
        "reviewer_decisions",
        sa.Column("decision_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("reviewer_user_id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("recommendation_id", sa.String(length=36), nullable=False),
        sa.Column("policy_evaluation_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["contextual_assessments.assessment_id"], name="fk_reviewer_decisions_assessment_id_contextual_assessments"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_reviewer_decisions_institution_id_institutions"),
        sa.ForeignKeyConstraint(["policy_evaluation_id"], ["policy_evaluations.evaluation_id"], name="fk_reviewer_decisions_policy_evaluation_id_policy_evaluations"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["agent_recommendations.recommendation_id"], name="fk_reviewer_decisions_recommendation_id_agent_recommendations"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.user_id"], name="fk_reviewer_decisions_reviewer_user_id_users"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_reviewer_decisions_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("decision_id", name="pk_reviewer_decisions"),
    )
    op.create_index("ix_reviewer_decisions_institution_session", "reviewer_decisions", ["institution_id", "session_id"])
    op.create_index("ix_reviewer_decisions_session_created", "reviewer_decisions", ["session_id", "created_at"])

    op.create_table(
        "governance_audit_records",
        sa.Column("audit_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("previous_entity_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.user_id"], name="fk_governance_audit_records_actor_id_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_governance_audit_records_institution_id_institutions"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_governance_audit_records_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("audit_id", name="pk_governance_audit_records"),
    )
    op.create_index("ix_governance_audit_action", "governance_audit_records", ["action"])
    op.create_index("ix_governance_audit_institution_session", "governance_audit_records", ["institution_id", "session_id"])
    op.create_index("ix_governance_audit_session_timestamp", "governance_audit_records", ["session_id", "timestamp"])

    op.create_table(
        "session_report_snapshots",
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_by", sa.String(length=36), nullable=False),
        sa.Column("report_version", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("report_payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["generated_by"], ["users.user_id"], name="fk_session_report_snapshots_generated_by_users"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.institution_id"], name="fk_session_report_snapshots_institution_id_institutions"),
        sa.ForeignKeyConstraint(["session_id"], ["examination_sessions.session_id"], name="fk_session_report_snapshots_session_id_examination_sessions"),
        sa.PrimaryKeyConstraint("report_id", name="pk_session_report_snapshots"),
    )
    op.create_index("ix_session_reports_institution_session", "session_report_snapshots", ["institution_id", "session_id"])
    op.create_index("ix_session_reports_session_generated", "session_report_snapshots", ["session_id", "generated_at"])


def downgrade() -> None:
    op.drop_index("ix_session_reports_session_generated", table_name="session_report_snapshots")
    op.drop_index("ix_session_reports_institution_session", table_name="session_report_snapshots")
    op.drop_table("session_report_snapshots")
    op.drop_index("ix_governance_audit_session_timestamp", table_name="governance_audit_records")
    op.drop_index("ix_governance_audit_institution_session", table_name="governance_audit_records")
    op.drop_index("ix_governance_audit_action", table_name="governance_audit_records")
    op.drop_table("governance_audit_records")
    op.drop_index("ix_reviewer_decisions_session_created", table_name="reviewer_decisions")
    op.drop_index("ix_reviewer_decisions_institution_session", table_name="reviewer_decisions")
    op.drop_table("reviewer_decisions")
    op.drop_index("ix_policy_evaluations_status", table_name="policy_evaluations")
    op.drop_index("ix_policy_evaluations_session_evaluated", table_name="policy_evaluations")
    op.drop_index("ix_policy_evaluations_institution_session", table_name="policy_evaluations")
    op.drop_table("policy_evaluations")
    op.drop_index("ix_institutional_policies_institution_status", table_name="institutional_policies")
    op.drop_index("ix_institutional_policies_created_at", table_name="institutional_policies")
    op.drop_table("institutional_policies")
    op.drop_index("ix_agent_recommendations_status", table_name="agent_recommendations")
    op.drop_index("ix_agent_recommendations_session_created", table_name="agent_recommendations")
    op.drop_index("ix_agent_recommendations_institution_session", table_name="agent_recommendations")
    op.drop_table("agent_recommendations")
    op.drop_index("ix_contextual_assessments_status", table_name="contextual_assessments")
    op.drop_index("ix_contextual_assessments_session_calculated", table_name="contextual_assessments")
    op.drop_index("ix_contextual_assessments_institution_session", table_name="contextual_assessments")
    op.drop_table("contextual_assessments")
