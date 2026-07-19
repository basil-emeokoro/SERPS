from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from serps_pop.infrastructure.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContextualAssessment(Base):
    __tablename__ = "contextual_assessments"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="risk_score_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="assessment_confidence_range"),
        Index("ix_contextual_assessments_institution_session", "institution_id", "session_id"),
        Index("ix_contextual_assessments_session_calculated", "session_id", "calculated_at"),
        Index("ix_contextual_assessments_status", "status"),
    )

    assessment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_event_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class AgentRecommendation(Base):
    __tablename__ = "agent_recommendations"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="recommendation_confidence_range"),
        Index("ix_agent_recommendations_institution_session", "institution_id", "session_id"),
        Index("ix_agent_recommendations_session_created", "session_id", "created_at"),
        Index("ix_agent_recommendations_status", "status"),
    )

    recommendation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("contextual_assessments.assessment_id"), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    recommended_action: Mapped[str] = mapped_column(String(60), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    requires_reviewer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class InstitutionalPolicy(Base):
    __tablename__ = "institutional_policies"
    __table_args__ = (
        CheckConstraint("automatic_exam_termination_allowed = false", name="automatic_termination_prohibited"),
        Index("ix_institutional_policies_institution_status", "institution_id", "status"),
        Index("ix_institutional_policies_created_at", "created_at"),
    )

    policy_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(40), nullable=False, default="IPIME-1.0")
    high_risk_action: Mapped[str] = mapped_column(String(60), nullable=False, default="NOTIFY_REVIEWER")
    critical_risk_action: Mapped[str] = mapped_column(String(60), nullable=False, default="ESCALATE_INCIDENT")
    reviewer_notification_threshold: Mapped[str] = mapped_column(String(20), nullable=False, default="High")
    candidate_acknowledgement_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reauthentication_threshold: Mapped[str] = mapped_column(String(20), nullable=False, default="High")
    automatic_exam_termination_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class PolicyEvaluation(Base):
    __tablename__ = "policy_evaluations"
    __table_args__ = (
        Index("ix_policy_evaluations_institution_session", "institution_id", "session_id"),
        Index("ix_policy_evaluations_session_evaluated", "session_id", "evaluated_at"),
        Index("ix_policy_evaluations_status", "status"),
    )

    evaluation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("agent_recommendations.recommendation_id"), nullable=False)
    policy_id: Mapped[str] = mapped_column(ForeignKey("institutional_policies.policy_id"), nullable=False)
    evaluated_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    approved_action: Mapped[str] = mapped_column(String(60), nullable=False)
    requires_reviewer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_candidate_acknowledgement: Mapped[bool] = mapped_column(Boolean, nullable=False)
    continue_examination: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class ReviewerDecision(Base):
    __tablename__ = "reviewer_decisions"
    __table_args__ = (
        Index("ix_reviewer_decisions_institution_session", "institution_id", "session_id"),
        Index("ix_reviewer_decisions_session_created", "session_id", "created_at"),
    )

    decision_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("contextual_assessments.assessment_id"), nullable=False)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("agent_recommendations.recommendation_id"), nullable=False)
    policy_evaluation_id: Mapped[str] = mapped_column(ForeignKey("policy_evaluations.evaluation_id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class GovernanceAuditRecord(Base):
    __tablename__ = "governance_audit_records"
    __table_args__ = (
        Index("ix_governance_audit_institution_session", "institution_id", "session_id"),
        Index("ix_governance_audit_session_timestamp", "session_id", "timestamp"),
        Index("ix_governance_audit_action", "action"),
    )

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False, default="user")
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    previous_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class SessionReportSnapshot(Base):
    __tablename__ = "session_report_snapshots"
    __table_args__ = (
        Index("ix_session_reports_institution_session", "institution_id", "session_id"),
        Index("ix_session_reports_session_generated", "session_id", "generated_at"),
    )

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    session_id: Mapped[str] = mapped_column(ForeignKey("examination_sessions.session_id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    generated_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    report_version: Mapped[str] = mapped_column(String(40), nullable=False, default="SERPS-REPORT-1.0")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    report_payload: Mapped[dict] = mapped_column(JSON, nullable=False)


IMMUTABLE_MODELS = (
    ContextualAssessment,
    AgentRecommendation,
    InstitutionalPolicy,
    PolicyEvaluation,
    ReviewerDecision,
    GovernanceAuditRecord,
    SessionReportSnapshot,
)


def _reject_mutation(_mapper: object, _connection: object, target: object) -> None:
    raise ValueError(f"{type(target).__name__} records are append-only.")


for _model in IMMUTABLE_MODELS:
    event.listen(_model, "before_update", _reject_mutation)
    event.listen(_model, "before_delete", _reject_mutation)
