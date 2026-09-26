from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from serps_pop.evidence.repository import EvidenceEventRepository
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.engine import DEFAULT_WINDOW_SECONDS, RISK_LEVEL_ORDER, assess_events
from serps_pop.governance.demo_policy import phone_protection_armed_at
from serps_pop.governance.models import (
    AgentRecommendation,
    ContextualAssessment,
    GovernanceAuditRecord,
    InstitutionalPolicy,
    PolicyEvaluation,
    ReviewerDecision,
    SessionReportSnapshot,
    new_uuid,
    utc_now,
)
from serps_pop.governance.schemas import ReviewerDecisionCreate
from serps_pop.identity.models import Candidate, Examination, ExaminationSession
from serps_pop.identity.services import ROLE_SYSADMIN


class GovernanceNotFound(Exception):
    pass


class GovernanceAccessDenied(Exception):
    pass


class GovernanceConflict(Exception):
    pass


def _has_sysadmin(roles: Iterable[str]) -> bool:
    return ROLE_SYSADMIN in set(roles)


def _authorised_session(
    db: Session,
    session_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> ExaminationSession:
    examination_session = db.get(ExaminationSession, session_id)
    if examination_session is None:
        raise GovernanceNotFound("Examination session not found.")
    if not _has_sysadmin(actor_roles) and examination_session.institution_id != actor_institution_id:
        raise GovernanceAccessDenied("Insufficient permissions for this examination session.")
    return examination_session


def _authorised_entity(entity: Any, actor_institution_id: str, actor_roles: Iterable[str]) -> Any:
    if entity is None:
        raise GovernanceNotFound("Governance record not found.")
    if not _has_sysadmin(actor_roles) and entity.institution_id != actor_institution_id:
        raise GovernanceAccessDenied("Insufficient permissions for this governance record.")
    return entity


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _model_payload(record: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: _json_value(getattr(record, field)) for field in fields}


def _append_audit(
    db: Session,
    *,
    institution_id: str,
    session_id: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any],
    previous_entity_id: str | None = None,
    audit_id: str | None = None,
    timestamp: datetime | None = None,
) -> GovernanceAuditRecord:
    canonical = json.dumps(_json_value(details), sort_keys=True, separators=(",", ":"))
    record = GovernanceAuditRecord(
        audit_id=audit_id or new_uuid(),
        institution_id=institution_id,
        session_id=session_id,
        actor_id=actor_id,
        actor_type="user",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_entity_id=previous_entity_id,
        timestamp=timestamp or utc_now(),
        payload_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        details=_json_value(details),
    )
    db.add(record)
    return record


def create_contextual_assessment(
    db: Session,
    *,
    session_id: str,
    actor_user_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> ContextualAssessment:
    examination_session = _authorised_session(db, session_id, actor_institution_id, actor_roles)
    events = EvidenceEventRepository(db).list_by_session(session_id)
    result = assess_events(events, window_seconds)
    from serps_pop.governance.camera_monitoring import camera_condition
    camera_context = camera_condition(events, examination_session.deployment_mode)
    previous_id = db.scalar(
        select(ContextualAssessment.assessment_id)
        .where(ContextualAssessment.session_id == session_id)
        .order_by(ContextualAssessment.calculated_at.desc(), ContextualAssessment.assessment_id.desc())
        .limit(1)
    )
    assessment = ContextualAssessment(
        institution_id=examination_session.institution_id,
        session_id=session_id,
        candidate_id=examination_session.candidate_id,
        created_by=actor_user_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        confidence=result.confidence,
        explanation=result.explanation,
        evidence_window_start=result.evidence_window_start,
        evidence_window_end=result.evidence_window_end,
        evidence_event_ids=result.evidence_event_ids,
        rule_version=result.rule_version,
        metadata_json={**result.metadata, "required_camera_condition": camera_context},
    )
    db.add(assessment)
    db.flush()
    _append_audit(
        db,
        institution_id=assessment.institution_id,
        session_id=session_id,
        actor_id=actor_user_id,
        action="CONTEXTUAL_ASSESSMENT_CREATED",
        entity_type="ContextualAssessment",
        entity_id=assessment.assessment_id,
        previous_entity_id=previous_id,
        details={
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "evidence_event_ids": assessment.evidence_event_ids,
            "rule_version": assessment.rule_version,
        },
    )
    db.flush()
    return assessment


def list_contextual_assessments(
    db: Session, *, session_id: str, actor_institution_id: str, actor_roles: Iterable[str]
) -> list[ContextualAssessment]:
    _authorised_session(db, session_id, actor_institution_id, actor_roles)
    return list(
        db.scalars(
            select(ContextualAssessment)
            .where(ContextualAssessment.session_id == session_id)
            .order_by(ContextualAssessment.calculated_at.asc(), ContextualAssessment.assessment_id.asc())
        ).all()
    )


def create_agent_recommendation(
    db: Session,
    *,
    assessment_id: str,
    actor_user_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> AgentRecommendation:
    assessment = _authorised_entity(db.get(ContextualAssessment, assessment_id), actor_institution_id, actor_roles)
    examination_session = db.get(ExaminationSession, assessment.session_id)
    mapping = {
        "Low": ("CONTINUE_MONITORING", "low", False),
        "Moderate": ("REQUEST_CANDIDATE_ACKNOWLEDGEMENT", "medium", False),
        "High": ("NOTIFY_REVIEWER", "high", True),
        "Critical": ("ESCALATE_INCIDENT", "critical", True),
    }
    action, priority, requires_reviewer = mapping[assessment.risk_level]
    unresolved_count = db.scalar(
        select(AgentRecommendation)
        .where(AgentRecommendation.session_id == assessment.session_id, AgentRecommendation.status == "open")
        .with_only_columns(AgentRecommendation.recommendation_id)
    )
    explanation = (
        f"Assessment {assessment.assessment_id} recorded {assessment.risk_level} contextual risk "
        f"({assessment.risk_score:.2f}); bounded workflow rules recommend {action}. "
        "This is advisory and makes no misconduct determination."
    )
    recommendation = AgentRecommendation(
        institution_id=assessment.institution_id,
        session_id=assessment.session_id,
        assessment_id=assessment.assessment_id,
        created_by=actor_user_id,
        recommended_action=action,
        priority=priority,
        confidence=assessment.confidence,
        explanation=explanation,
        requires_reviewer=requires_reviewer,
        metadata_json={
            "session_status": examination_session.status if examination_session else "unknown",
            "existing_open_recommendation": unresolved_count is not None,
        },
    )
    db.add(recommendation)
    db.flush()
    _append_audit(
        db,
        institution_id=recommendation.institution_id,
        session_id=recommendation.session_id,
        actor_id=actor_user_id,
        action="AGENT_RECOMMENDATION_CREATED",
        entity_type="AgentRecommendation",
        entity_id=recommendation.recommendation_id,
        previous_entity_id=assessment.assessment_id,
        details={"recommended_action": action, "requires_reviewer": requires_reviewer},
    )
    db.flush()
    return recommendation


def get_or_create_default_policy(db: Session, institution_id: str, actor_user_id: str) -> InstitutionalPolicy:
    policy = db.scalar(
        select(InstitutionalPolicy)
        .where(InstitutionalPolicy.institution_id == institution_id, InstitutionalPolicy.status == "active")
        .order_by(InstitutionalPolicy.created_at.desc())
        .limit(1)
    )
    if policy is None:
        policy = InstitutionalPolicy(
            institution_id=institution_id,
            created_by=actor_user_id,
            automatic_exam_termination_allowed=False,
            metadata_json={"source": "Sprint 3B default policy"},
        )
        db.add(policy)
        db.flush()
    if policy.automatic_exam_termination_allowed:
        raise GovernanceConflict("Automatic examination termination is prohibited in Sprint 3B.")
    return policy


def create_policy_evaluation(
    db: Session,
    *,
    recommendation_id: str,
    actor_user_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> PolicyEvaluation:
    recommendation = _authorised_entity(
        db.get(AgentRecommendation, recommendation_id), actor_institution_id, actor_roles
    )
    assessment = db.get(ContextualAssessment, recommendation.assessment_id)
    if assessment is None:
        raise GovernanceConflict("Recommendation assessment is unavailable.")
    policy = get_or_create_default_policy(db, recommendation.institution_id, actor_user_id)
    level_rank = RISK_LEVEL_ORDER[assessment.risk_level]
    notification_rank = RISK_LEVEL_ORDER[policy.reviewer_notification_threshold]
    approved_action = recommendation.recommended_action
    if assessment.risk_level == "High":
        approved_action = policy.high_risk_action
    elif assessment.risk_level == "Critical":
        approved_action = policy.critical_risk_action
    armed_at = phone_protection_armed_at(assessment.session_id)
    phone_protection_enabled = armed_at is not None
    phone_count = 0
    if armed_at is not None:
        window_start = assessment.evidence_window_start
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=armed_at.tzinfo)
        window_end = assessment.evidence_window_end
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=armed_at.tzinfo)
        effective_start = max(window_start, armed_at)
        phone_count = len(db.scalars(select(EvidenceEventRecord).where(
            EvidenceEventRecord.session_id == assessment.session_id,
            EvidenceEventRecord.event_type == "mobile_phone_detected",
            EvidenceEventRecord.timestamp >= effective_start,
            EvidenceEventRecord.timestamp <= window_end,
        )).all())
    if phone_protection_enabled and phone_count >= 2 and assessment.risk_level in {"High", "Critical"}:
        approved_action = "PROTECT_AND_PAUSE"
    requires_reviewer = recommendation.requires_reviewer or level_rank >= notification_rank
    from serps_pop.governance.camera_monitoring import camera_loss_action
    camera_context = assessment.metadata_json.get("required_camera_condition", {})
    camera_action = camera_loss_action(policy.metadata_json, camera_context)
    # Explicit operational policy is independent of phone-demo arming and identity checks.
    # Preserve a concurrently required phone protective pause.
    other_context = any(count for name, count in assessment.metadata_json.get("event_counts", {}).items()
                        if name != "camera_disconnected")
    if camera_action and approved_action != "PROTECT_AND_PAUSE":
        if not other_context or camera_action == "PROTECT_AND_PAUSE":
            approved_action = camera_action
        elif camera_action == "NOTIFY_REVIEWER" and approved_action in {"CONTINUE_MONITORING", "REQUEST_CANDIDATE_ACKNOWLEDGEMENT"}:
            approved_action = camera_action
    if camera_action in {"NOTIFY_REVIEWER", "PROTECT_AND_PAUSE"}:
        requires_reviewer = True
    requires_ack = policy.candidate_acknowledgement_required and level_rank >= RISK_LEVEL_ORDER["Moderate"]
    from serps_pop.identity_assurance.reauthentication import identity_conditions, require_from_evaluation
    reauth_conditions = identity_conditions(assessment, policy)
    reauthentication_expected = bool(reauth_conditions)
    if reauthentication_expected:
        requires_reviewer = True
        if approved_action in {"CONTINUE_MONITORING", "REQUEST_CANDIDATE_ACKNOWLEDGEMENT"}:
            approved_action = "REQUEST_REAUTHENTICATION"
    explanation = (
        f"Policy {policy.policy_version} evaluated {recommendation.recommended_action} at "
        f"{assessment.risk_level} risk and approved {approved_action}. "
        f"Reviewer required: {str(requires_reviewer).lower()}; candidate acknowledgement required: "
        f"{str(requires_ack).lower()}; the session is not terminated. A policy-controlled protective pause may apply. "
        "Automatic termination and misconduct determination are prohibited. "
        f"Required camera operational response: {camera_action or 'not configured'}; no misconduct determination. "
        f"Identity re-authentication conditions: {', '.join(reauth_conditions) or 'none'}."
    )
    evaluation = PolicyEvaluation(
        institution_id=recommendation.institution_id,
        session_id=recommendation.session_id,
        recommendation_id=recommendation.recommendation_id,
        policy_id=policy.policy_id,
        evaluated_by=actor_user_id,
        approved_action=approved_action,
        requires_reviewer=requires_reviewer,
        requires_candidate_acknowledgement=requires_ack,
        continue_examination=True,
        explanation=explanation,
        policy_version=policy.policy_version,
        metadata_json={
            "reauthentication_expected": reauthentication_expected,
            "identity_conditions": reauth_conditions,
            "identity_reauthentication_policy": policy.metadata_json.get("identity_reauthentication", {}),
            "protection_required": approved_action == "PROTECT_AND_PAUSE",
            "protection_trigger": ("required_camera_unavailable" if camera_action == "PROTECT_AND_PAUSE" else
                                   "persistent_mobile_phone_evidence" if approved_action == "PROTECT_AND_PAUSE" else None),
            "required_camera_condition": camera_context,
            "required_camera_loss_action": camera_action,
            "phone_protection_required": phone_protection_enabled and phone_count >= 2 and assessment.risk_level in {"High", "Critical"},
            "misconduct_determination": False,
            "prototype_demo_phone_policy_armed": phone_protection_enabled,
            "phone_persistence_rule": "at_least_2_mobile_phone_detected_events_in_contextual_window" if phone_protection_enabled else None,
        },
    )
    db.add(evaluation)
    db.flush()
    _append_audit(
        db,
        institution_id=evaluation.institution_id,
        session_id=evaluation.session_id,
        actor_id=actor_user_id,
        action="POLICY_EVALUATION_CREATED",
        entity_type="PolicyEvaluation",
        entity_id=evaluation.evaluation_id,
        previous_entity_id=recommendation.recommendation_id,
        details={
            "approved_action": approved_action,
            "requires_reviewer": requires_reviewer,
            "continue_examination": True,
            "policy_version": policy.policy_version,
        },
    )
    require_from_evaluation(db, evaluation, assessment, policy)
    db.flush()
    return evaluation


def record_reviewer_decision(
    db: Session,
    *,
    session_id: str,
    payload: ReviewerDecisionCreate,
    actor_user_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> ReviewerDecision:
    examination_session = _authorised_session(db, session_id, actor_institution_id, actor_roles)
    assessment = db.get(ContextualAssessment, payload.assessment_id)
    recommendation = db.get(AgentRecommendation, payload.recommendation_id)
    evaluation = db.get(PolicyEvaluation, payload.policy_evaluation_id)
    if not assessment or not recommendation or not evaluation:
        raise GovernanceNotFound("Referenced governance chain was not found.")
    if any(item.session_id != session_id for item in (assessment, recommendation, evaluation)):
        raise GovernanceConflict("Referenced governance records do not belong to this session.")
    if recommendation.assessment_id != assessment.assessment_id or evaluation.recommendation_id != recommendation.recommendation_id:
        raise GovernanceConflict("Referenced governance records do not form a valid chain.")
    if any(item.institution_id != examination_session.institution_id for item in (assessment, recommendation, evaluation)):
        raise GovernanceAccessDenied("Governance chain is outside the authorised institution.")
    previous_id = db.scalar(
        select(ReviewerDecision.decision_id)
        .where(ReviewerDecision.session_id == session_id)
        .order_by(ReviewerDecision.created_at.desc(), ReviewerDecision.decision_id.desc())
        .limit(1)
    )
    decision = ReviewerDecision(
        institution_id=examination_session.institution_id,
        session_id=session_id,
        reviewer_user_id=actor_user_id,
        assessment_id=assessment.assessment_id,
        recommendation_id=recommendation.recommendation_id,
        policy_evaluation_id=evaluation.evaluation_id,
        decision=payload.decision,
        rationale=payload.rationale,
        metadata_json=payload.metadata,
    )
    db.add(decision)
    db.flush()
    _append_audit(
        db,
        institution_id=decision.institution_id,
        session_id=session_id,
        actor_id=actor_user_id,
        action="REVIEWER_DECISION_RECORDED",
        entity_type="ReviewerDecision",
        entity_id=decision.decision_id,
        previous_entity_id=previous_id or evaluation.evaluation_id,
        details={"decision": decision.decision, "rationale": decision.rationale},
    )
    from serps_pop.identity_assurance.reauthentication import apply_reviewer_decision
    apply_reviewer_decision(db, decision)
    db.flush()
    return decision


def _queue_camera_status(db: Session, session_id: str, role: str) -> str:
    events = db.scalars(
        select(EvidenceEventRecord)
        .where(
            EvidenceEventRecord.session_id == session_id,
            EvidenceEventRecord.event_type.in_(("camera_connected", "camera_disconnected", "camera_reconnected")),
        )
        .order_by(EvidenceEventRecord.timestamp.desc(), EvidenceEventRecord.event_id.desc())
    ).all()
    for event in events:
        event_role = event.camera_id or "primary"
        if event_role == role:
            return "connected" if event.event_type in {"camera_connected", "camera_reconnected"} else "disconnected"
    return "not_seen"


def reviewer_queue(
    db: Session,
    *,
    actor_institution_id: str,
    actor_roles: Iterable[str],
    institution_id: str | None = None,
    risk_level: str | None = None,
    unresolved: bool | None = None,
    examination_id: str | None = None,
    active_session: bool | None = None,
) -> list[dict[str, Any]]:
    stmt = select(ExaminationSession, Candidate, Examination).join(Candidate).join(Examination)
    scoped_institution = institution_id if _has_sysadmin(actor_roles) and institution_id else actor_institution_id
    if not _has_sysadmin(actor_roles) or institution_id:
        stmt = stmt.where(ExaminationSession.institution_id == scoped_institution)
    if examination_id:
        stmt = stmt.where(ExaminationSession.examination_id == examination_id)
    if active_session is True:
        stmt = stmt.where(ExaminationSession.status == "active")
    if active_session is False:
        stmt = stmt.where(ExaminationSession.status != "active")
    items: list[dict[str, Any]] = []
    for session_record, candidate, examination in db.execute(stmt).all():
        assessment = db.scalar(
            select(ContextualAssessment)
            .where(ContextualAssessment.session_id == session_record.session_id)
            .order_by(ContextualAssessment.calculated_at.desc(), ContextualAssessment.assessment_id.desc())
            .limit(1)
        )
        if risk_level and (assessment is None or assessment.risk_level != risk_level):
            continue
        recommendation = None
        evaluation = None
        if assessment:
            recommendation = db.scalar(
                select(AgentRecommendation)
                .where(AgentRecommendation.assessment_id == assessment.assessment_id)
                .order_by(AgentRecommendation.created_at.desc())
                .limit(1)
            )
        if recommendation:
            evaluation = db.scalar(
                select(PolicyEvaluation)
                .where(PolicyEvaluation.recommendation_id == recommendation.recommendation_id)
                .order_by(PolicyEvaluation.evaluated_at.desc())
                .limit(1)
            )
        decision = None
        if evaluation:
            decision = db.scalar(
                select(ReviewerDecision)
                .where(ReviewerDecision.policy_evaluation_id == evaluation.evaluation_id)
                .order_by(ReviewerDecision.created_at.desc())
                .limit(1)
            )
        is_unresolved = evaluation is not None and evaluation.requires_reviewer and decision is None
        if unresolved is not None and is_unresolved != unresolved:
            continue
        latest_evidence = db.scalar(
            select(EvidenceEventRecord)
            .where(EvidenceEventRecord.session_id == session_record.session_id)
            .order_by(EvidenceEventRecord.timestamp.desc(), EvidenceEventRecord.event_id.desc())
            .limit(1)
        )
        items.append(
            {
                "session_id": session_record.session_id,
                "institution_id": session_record.institution_id,
                "candidate_id": candidate.candidate_id,
                "candidate_name": candidate.full_name,
                "examination_id": examination.examination_id,
                "examination": examination.title,
                "session_status": session_record.status,
                "latest_risk_score": assessment.risk_score if assessment else None,
                "latest_risk_level": assessment.risk_level if assessment else None,
                "latest_evidence": (
                    {
                        "event_id": latest_evidence.event_id,
                        "event_type": latest_evidence.event_type,
                        "timestamp": latest_evidence.timestamp,
                        "source_module": latest_evidence.source_module,
                        "camera_id": latest_evidence.camera_id,
                        "confidence": latest_evidence.confidence,
                        "metadata_json": latest_evidence.metadata_json,
                    }
                    if latest_evidence
                    else None
                ),
                "assessment_explanation": assessment.explanation if assessment else None,
                "agent_recommendation": recommendation.recommended_action if recommendation else None,
                "policy_outcome": evaluation.approved_action if evaluation else None,
                "review_status": "resolved" if decision else "unresolved" if is_unresolved else "not_required",
                "latest_event_timestamp": latest_evidence.timestamp if latest_evidence else None,
                "primary_camera_status": _queue_camera_status(db, session_record.session_id, "primary"),
                "secondary_camera_status": _queue_camera_status(db, session_record.session_id, "secondary"),
                "reviewer_action_status": "resolved" if decision else "action_required" if is_unresolved else "not_required",
            }
        )
    return items


ASSESSMENT_FIELDS = (
    "assessment_id", "institution_id", "session_id", "candidate_id", "created_by", "calculated_at",
    "risk_score", "risk_level", "confidence", "explanation", "evidence_window_start", "evidence_window_end",
    "evidence_event_ids", "rule_version", "status", "metadata_json",
)
RECOMMENDATION_FIELDS = (
    "recommendation_id", "institution_id", "session_id", "assessment_id", "created_by", "created_at",
    "recommended_action", "priority", "confidence", "explanation", "requires_reviewer", "status", "metadata_json",
)
EVALUATION_FIELDS = (
    "evaluation_id", "institution_id", "session_id", "recommendation_id", "policy_id", "evaluated_by",
    "evaluated_at", "approved_action", "requires_reviewer", "requires_candidate_acknowledgement",
    "continue_examination", "explanation", "policy_version", "status", "metadata_json",
)
DECISION_FIELDS = (
    "decision_id", "institution_id", "session_id", "reviewer_user_id", "assessment_id", "recommendation_id",
    "policy_evaluation_id", "decision", "rationale", "created_at", "metadata_json",
)
AUDIT_FIELDS = (
    "audit_id", "institution_id", "session_id", "actor_id", "actor_type", "action", "entity_type", "entity_id",
    "previous_entity_id", "timestamp", "payload_hash", "details",
)


def governance_timeline(
    db: Session, *, session_id: str, actor_institution_id: str, actor_roles: Iterable[str], limit: int | None = None
) -> list[dict[str, Any]]:
    _authorised_session(db, session_id, actor_institution_id, actor_roles)
    entries: list[dict[str, Any]] = []
    evidence_stmt = select(EvidenceEventRecord).where(EvidenceEventRecord.session_id == session_id)
    if limit is not None:
        evidence_stmt = evidence_stmt.order_by(
            EvidenceEventRecord.timestamp.desc(), EvidenceEventRecord.event_id.desc()
        ).limit(limit)
    evidence = db.scalars(evidence_stmt).all()
    for item in evidence:
        entries.append({
            "entry_type": "EvidenceEvent",
            "entity_id": item.event_id,
            "timestamp": item.timestamp,
            "payload": _model_payload(item, ("event_id", "candidate_id", "event_type", "source_module", "risk_weight", "confidence", "camera_id", "description", "metadata_json")),
        })
    collections = (
        (ContextualAssessment, "ContextualAssessment", "assessment_id", "calculated_at", ASSESSMENT_FIELDS),
        (AgentRecommendation, "AgentRecommendation", "recommendation_id", "created_at", RECOMMENDATION_FIELDS),
        (PolicyEvaluation, "PolicyEvaluation", "evaluation_id", "evaluated_at", EVALUATION_FIELDS),
        (ReviewerDecision, "ReviewerDecision", "decision_id", "created_at", DECISION_FIELDS),
        (GovernanceAuditRecord, "GovernanceAuditRecord", "audit_id", "timestamp", AUDIT_FIELDS),
    )
    for model, entry_type, id_field, time_field, fields in collections:
        statement = select(model).where(model.session_id == session_id)
        if limit is not None:
            statement = statement.order_by(getattr(model, time_field).desc(), getattr(model, id_field).desc()).limit(limit)
        for item in db.scalars(statement).all():
            entries.append({
                "entry_type": entry_type,
                "entity_id": getattr(item, id_field),
                "timestamp": getattr(item, time_field),
                "payload": _model_payload(item, fields),
            })
    entries.sort(key=lambda item: (item["timestamp"], item["entry_type"], item["entity_id"]))
    return entries[-limit:] if limit is not None else entries


def governance_timeline_count(db: Session, *, session_id: str) -> int:
    models = (
        EvidenceEventRecord,
        ContextualAssessment,
        AgentRecommendation,
        PolicyEvaluation,
        ReviewerDecision,
        GovernanceAuditRecord,
    )
    return sum(
        db.scalar(select(func.count()).select_from(model).where(model.session_id == session_id)) or 0
        for model in models
    )


def _report_payload(db: Session, examination_session: ExaminationSession) -> dict[str, Any]:
    candidate = db.get(Candidate, examination_session.candidate_id)
    examination = db.get(Examination, examination_session.examination_id)
    events = db.scalars(
        select(EvidenceEventRecord)
        .where(EvidenceEventRecord.session_id == examination_session.session_id)
        .order_by(EvidenceEventRecord.timestamp.asc())
    ).all()
    assessments = db.scalars(select(ContextualAssessment).where(ContextualAssessment.session_id == examination_session.session_id)).all()
    recommendations = db.scalars(select(AgentRecommendation).where(AgentRecommendation.session_id == examination_session.session_id)).all()
    evaluations = db.scalars(select(PolicyEvaluation).where(PolicyEvaluation.session_id == examination_session.session_id)).all()
    decisions = db.scalars(select(ReviewerDecision).where(ReviewerDecision.session_id == examination_session.session_id)).all()
    audits = db.scalars(select(GovernanceAuditRecord).where(GovernanceAuditRecord.session_id == examination_session.session_id)).all()
    event_counts: dict[str, int] = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
    return {
        "candidate": _model_payload(candidate, ("candidate_id", "candidate_identifier", "full_name", "email", "status")),
        "examination": _model_payload(examination, ("examination_id", "exam_code", "title", "status", "duration_minutes")),
        "session": _model_payload(examination_session, ("session_id", "institution_id", "candidate_id", "examination_id", "status", "started_at", "ended_at", "created_at")),
        "evidence_event_summary": {"total": len(events), "counts_by_type": event_counts, "event_ids": [event.event_id for event in events]},
        "evidence_events": [
            _model_payload(
                event,
                (
                    "event_id", "timestamp", "event_type", "source_module", "risk_weight",
                    "confidence", "camera_id", "description", "metadata_json",
                ),
            )
            for event in events
        ],
        "risk_history": [{"assessment_id": item.assessment_id, "calculated_at": _json_value(item.calculated_at), "risk_score": item.risk_score, "risk_level": item.risk_level} for item in assessments],
        "contextual_assessments": [_model_payload(item, ASSESSMENT_FIELDS) for item in assessments],
        "agent_recommendations": [_model_payload(item, RECOMMENDATION_FIELDS) for item in recommendations],
        "policy_evaluations": [_model_payload(item, EVALUATION_FIELDS) for item in evaluations],
        "reviewer_decisions": [_model_payload(item, DECISION_FIELDS) for item in decisions],
        "audit_history": [_model_payload(item, AUDIT_FIELDS) for item in audits],
    }


def generate_report(
    db: Session,
    *,
    session_id: str,
    actor_user_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> SessionReportSnapshot:
    examination_session = _authorised_session(db, session_id, actor_institution_id, actor_roles)
    report_id = new_uuid()
    generated_at = utc_now()
    previous_id = db.scalar(
        select(SessionReportSnapshot.report_id)
        .where(SessionReportSnapshot.session_id == session_id)
        .order_by(SessionReportSnapshot.generated_at.desc())
        .limit(1)
    )
    audit_id = new_uuid()
    _append_audit(
        db,
        audit_id=audit_id,
        timestamp=generated_at,
        institution_id=examination_session.institution_id,
        session_id=session_id,
        actor_id=actor_user_id,
        action="SESSION_REPORT_GENERATED",
        entity_type="SessionReportSnapshot",
        entity_id=report_id,
        previous_entity_id=previous_id,
        details={"report_version": "SERPS-REPORT-1.0"},
    )
    db.flush()
    payload = _report_payload(db, examination_session)
    assessment_count = len(payload["contextual_assessments"])
    decision_count = len(payload["reviewer_decisions"])
    report = SessionReportSnapshot(
        report_id=report_id,
        institution_id=examination_session.institution_id,
        session_id=session_id,
        generated_at=generated_at,
        generated_by=actor_user_id,
        report_version="SERPS-REPORT-1.0",
        summary=(
            f"Session {session_id}: {payload['evidence_event_summary']['total']} evidence events, "
            f"{assessment_count} contextual assessments and {decision_count} reviewer decisions."
        ),
        report_payload=payload,
    )
    db.add(report)
    db.flush()
    return report


def get_report(
    db: Session,
    *,
    session_id: str,
    report_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> SessionReportSnapshot:
    _authorised_session(db, session_id, actor_institution_id, actor_roles)
    report = db.get(SessionReportSnapshot, report_id)
    if report is None or report.session_id != session_id:
        raise GovernanceNotFound("Session report not found.")
    return _authorised_entity(report, actor_institution_id, actor_roles)


def configure_camera_policy(db: Session, institution_id: str, actor_user_id: str, action: str | None) -> InstitutionalPolicy:
    from serps_pop.governance.camera_monitoring import CameraMonitoringPolicy
    CameraMonitoringPolicy(required_camera_loss_action=action)
    old = get_or_create_default_policy(db, institution_id, actor_user_id)
    policy = InstitutionalPolicy(institution_id=institution_id, created_by=actor_user_id,
        policy_version="IPIME-CAMERA-1.0", high_risk_action=old.high_risk_action,
        critical_risk_action=old.critical_risk_action, reviewer_notification_threshold=old.reviewer_notification_threshold,
        candidate_acknowledgement_required=old.candidate_acknowledgement_required,
        reauthentication_threshold=old.reauthentication_threshold, automatic_exam_termination_allowed=False,
        metadata_json={**old.metadata_json, "required_camera_loss_action": action, "previous_policy_id": old.policy_id})
    db.add(policy)
    db.flush()
    from serps_pop.identity.services import audit
    audit(db, institution_id=institution_id, actor_user_id=actor_user_id,
          action="camera_monitoring_policy.configure", result="success", target_type="InstitutionalPolicy",
          target_id=policy.policy_id, metadata={"previous_policy_id": old.policy_id,
          "required_camera_loss_action": action, "misconduct_determination": False})
    return policy
