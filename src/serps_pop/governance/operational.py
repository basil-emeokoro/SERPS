from __future__ import annotations

from typing import Any, Iterable
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from serps_pop.candidate_workflow.models import CameraSelectionRecord
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.models import (
    AgentRecommendation,
    ContextualAssessment,
    GovernanceAuditRecord,
    InstitutionalPolicy,
    PolicyEvaluation,
    ReviewerDecision,
    SessionReportSnapshot,
)
from serps_pop.governance.services import (
    _authorised_session,
    governance_timeline,
    governance_timeline_count,
    reviewer_queue,
)
from serps_pop.identity.models import Candidate, Examination, ExaminationSession, Institution
from serps_pop.identity.services import ROLE_SYSADMIN
from serps_pop.identity_assurance.models import IdentityAssuranceProfile


def _record(record: Any, fields: tuple[str, ...]) -> dict[str, Any] | None:
    if record is None:
        return None
    return {field: getattr(record, field) for field in fields}


def camera_status(db: Session, session: ExaminationSession, role: str) -> dict[str, Any]:
    selection_id = session.camera_selection_id if role == "primary" else session.secondary_camera_selection_id
    selection = db.get(CameraSelectionRecord, selection_id) if selection_id else None
    events = db.scalars(
        select(EvidenceEventRecord)
        .where(
            EvidenceEventRecord.session_id == session.session_id,
            EvidenceEventRecord.event_type.in_(("camera_connected", "camera_disconnected", "camera_heartbeat", "camera_reconnected")),
        )
        .order_by(EvidenceEventRecord.timestamp.desc(), EvidenceEventRecord.event_id.desc())
    ).all()
    latest = next((event for event in events if (event.camera_id or "primary") == role), None)
    connection = "not_seen"
    failure = None
    if latest:
        connection = "connected" if latest.event_type in {"camera_connected", "camera_heartbeat", "camera_reconnected"} else "disconnected"
        observed_at = latest.timestamp if latest.timestamp.tzinfo else latest.timestamp.replace(tzinfo=timezone.utc)
        if connection == "connected" and observed_at < datetime.now(timezone.utc) - timedelta(seconds=35):
            connection = "unavailable"
            failure = "Candidate camera state is stale; no heartbeat was received within 35 seconds."
        if connection == "disconnected":
            failure = latest.description
    elif selection:
        connection = "configured"
    return {
        "role": role,
        "configured": selection is not None,
        "connection_status": connection,
        "last_seen_at": latest.timestamp if latest else None,
        "label": selection.label if selection else None,
        "stream_mode": "metadata_only",
        "failure_reason": failure,
        "freshness_seconds": max(0, int((datetime.now(timezone.utc) - observed_at).total_seconds())) if latest else None,
    }


def operational_session_detail(
    db: Session,
    *,
    session_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> dict[str, Any]:
    timeline_limit = 200
    session = _authorised_session(db, session_id, actor_institution_id, actor_roles)
    candidate = db.get(Candidate, session.candidate_id)
    examination = db.get(Examination, session.examination_id)
    institution = db.get(Institution, session.institution_id)
    identity_profile = db.scalar(
        select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == candidate.user_id)
    ) if candidate and candidate.user_id else None
    assessment = db.scalar(
        select(ContextualAssessment)
        .where(ContextualAssessment.session_id == session_id)
        .order_by(ContextualAssessment.calculated_at.desc())
        .limit(1)
    )
    recommendation = db.scalar(
        select(AgentRecommendation)
        .where(AgentRecommendation.session_id == session_id)
        .order_by(AgentRecommendation.created_at.desc())
        .limit(1)
    )
    evaluation = db.scalar(
        select(PolicyEvaluation)
        .where(PolicyEvaluation.session_id == session_id)
        .order_by(PolicyEvaluation.evaluated_at.desc())
        .limit(1)
    )
    decisions = db.scalars(
        select(ReviewerDecision)
        .where(ReviewerDecision.session_id == session_id)
        .order_by(ReviewerDecision.created_at.asc())
    ).all()
    reports = db.scalars(
        select(SessionReportSnapshot)
        .where(SessionReportSnapshot.session_id == session_id)
        .order_by(SessionReportSnapshot.generated_at.desc())
    ).all()
    timeline_total = governance_timeline_count(db, session_id=session_id)
    return {
        "session": _record(session, ("session_id", "institution_id", "candidate_id", "examination_id", "status", "deployment_mode", "started_at", "ended_at", "monitoring_status")),
        "candidate": _record(candidate, ("candidate_id", "candidate_identifier", "full_name", "email", "status")),
        "identity_assurance": _record(
            identity_profile,
            (
                "enrolment_status",
                "authentication_result",
                "identity_confidence",
                "liveness_result",
                "last_verified_at",
                "demo_bypass",
            ),
        ) or {
            "enrolment_status": "legacy_account",
            "authentication_result": "password_only",
            "identity_confidence": None,
            "liveness_result": "not_required",
            "last_verified_at": None,
            "demo_bypass": False,
        },
        "institution": _record(institution, ("institution_id", "code", "name")),
        "examination": _record(examination, ("examination_id", "exam_code", "title", "status", "duration_minutes")),
        "primary_camera": camera_status(db, session, "primary"),
        "secondary_camera": camera_status(db, session, "secondary"),
        "latest_assessment": _record(assessment, ("assessment_id", "risk_score", "risk_level", "confidence", "explanation", "evidence_event_ids", "calculated_at")),
        "latest_recommendation": _record(recommendation, ("recommendation_id", "assessment_id", "recommended_action", "priority", "confidence", "explanation", "requires_reviewer", "created_at")),
        "latest_policy_evaluation": _record(evaluation, ("evaluation_id", "recommendation_id", "policy_id", "approved_action", "requires_reviewer", "requires_candidate_acknowledgement", "continue_examination", "explanation", "policy_version", "evaluated_at")),
        "reviewer_decisions": [
            _record(item, ("decision_id", "reviewer_user_id", "assessment_id", "recommendation_id", "policy_evaluation_id", "decision", "rationale", "created_at"))
            for item in decisions
        ],
        "timeline": governance_timeline(
            db,
            session_id=session_id,
            actor_institution_id=actor_institution_id,
            actor_roles=actor_roles,
            limit=timeline_limit,
        ),
        "timeline_total_entries": timeline_total,
        "timeline_truncated": timeline_total > timeline_limit,
        "reports": [
            _record(item, ("report_id", "generated_at", "generated_by", "report_version", "summary"))
            for item in reports
        ],
    }


def administrator_metrics(
    db: Session,
    *,
    actor_institution_id: str,
    actor_roles: Iterable[str],
    institution_id: str | None = None,
) -> dict[str, Any]:
    target_institution = institution_id if ROLE_SYSADMIN in set(actor_roles) and institution_id else actor_institution_id
    sessions = db.scalars(
        select(ExaminationSession).where(ExaminationSession.institution_id == target_institution)
    ).all()
    active = [item for item in sessions if item.status == "active"]
    completed = [item for item in sessions if item.status == "completed"]
    risk_counts = {level: 0 for level in ("Low", "Moderate", "High", "Critical")}
    for session in sessions:
        assessment = db.scalar(
            select(ContextualAssessment)
            .where(ContextualAssessment.session_id == session.session_id)
            .order_by(ContextualAssessment.calculated_at.desc())
            .limit(1)
        )
        if assessment:
            risk_counts[assessment.risk_level] += 1
    unresolved = reviewer_queue(
        db,
        actor_institution_id=target_institution,
        actor_roles=actor_roles,
        institution_id=target_institution,
        unresolved=True,
    )
    primary_states = [camera_status(db, item, "primary") for item in sessions]
    secondary_states = [camera_status(db, item, "secondary") for item in sessions]
    recent_audits = db.scalars(
        select(GovernanceAuditRecord)
        .where(GovernanceAuditRecord.institution_id == target_institution)
        .order_by(GovernanceAuditRecord.timestamp.desc())
        .limit(10)
    ).all()
    return {
        "institution_id": target_institution,
        "active_candidates": len({item.candidate_id for item in active}),
        "active_sessions": len(active),
        "completed_sessions": len(completed),
        "risk_counts": risk_counts,
        "unresolved_reviewer_cases": len(unresolved),
        "connected_primary_cameras": sum(item["connection_status"] == "connected" for item in primary_states),
        "connected_secondary_cameras": sum(item["connection_status"] == "connected" for item in secondary_states),
        "camera_failure_count": sum(
            item["connection_status"] in {"disconnected", "unavailable"} for item in primary_states + secondary_states
        ),
        "last_updated_at": datetime.now(timezone.utc),
        "recent_audit_activity": [
            _record(item, ("audit_id", "session_id", "actor_id", "action", "entity_type", "entity_id", "timestamp"))
            for item in recent_audits
        ],
    }


def current_policy(db: Session, institution_id: str) -> InstitutionalPolicy | None:
    return db.scalar(
        select(InstitutionalPolicy)
        .where(InstitutionalPolicy.institution_id == institution_id, InstitutionalPolicy.status == "active")
        .order_by(InstitutionalPolicy.created_at.desc())
        .limit(1)
    )
