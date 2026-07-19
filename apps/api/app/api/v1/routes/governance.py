from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.governance.schemas import (
    AgentRecommendationRead,
    AssessmentCreate,
    ContextualAssessmentRead,
    PolicyEvaluationRead,
    ReviewerDecisionCreate,
    ReviewerDecisionRead,
    ReviewerQueueItem,
    SessionReportRead,
    TimelineEntry,
)
from serps_pop.governance.services import (
    GovernanceAccessDenied,
    GovernanceConflict,
    GovernanceNotFound,
    create_agent_recommendation,
    create_contextual_assessment,
    create_policy_evaluation,
    generate_report,
    get_report,
    governance_timeline,
    list_contextual_assessments,
    record_reviewer_decision,
    reviewer_queue,
)
from serps_pop.identity.services import ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN

router = APIRouter()
GOVERNANCE_ROLES = (ROLE_REVIEWER, ROLE_ADMIN, ROLE_SYSADMIN)


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, GovernanceNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, GovernanceAccessDenied):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/examination-sessions/{session_id}/contextual-assessments",
    response_model=ContextualAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
def run_contextual_assessment(
    session_id: str,
    payload: AssessmentCreate = AssessmentCreate(),
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> object:
    try:
        result = create_contextual_assessment(
            db,
            session_id=session_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
            window_seconds=payload.window_seconds,
        )
        db.commit()
        db.refresh(result)
        return result
    except (GovernanceNotFound, GovernanceAccessDenied, GovernanceConflict) as exc:
        db.rollback()
        _raise_http(exc)


@router.get(
    "/examination-sessions/{session_id}/contextual-assessments",
    response_model=list[ContextualAssessmentRead],
)
def get_contextual_assessments(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> list[object]:
    try:
        return list_contextual_assessments(
            db,
            session_id=session_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    except (GovernanceNotFound, GovernanceAccessDenied) as exc:
        _raise_http(exc)


@router.post(
    "/contextual-assessments/{assessment_id}/recommendations",
    response_model=AgentRecommendationRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_recommendation(
    assessment_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> object:
    try:
        result = create_agent_recommendation(
            db,
            assessment_id=assessment_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        db.commit()
        db.refresh(result)
        return result
    except (GovernanceNotFound, GovernanceAccessDenied, GovernanceConflict) as exc:
        db.rollback()
        _raise_http(exc)


@router.post(
    "/agent-recommendations/{recommendation_id}/policy-evaluations",
    response_model=PolicyEvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_policy(
    recommendation_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> object:
    try:
        result = create_policy_evaluation(
            db,
            recommendation_id=recommendation_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        db.commit()
        db.refresh(result)
        return result
    except (GovernanceNotFound, GovernanceAccessDenied, GovernanceConflict) as exc:
        db.rollback()
        _raise_http(exc)


@router.get("/reviewer/sessions", response_model=list[ReviewerQueueItem])
def get_reviewer_queue(
    institution: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    unresolved: bool | None = Query(default=None),
    examination: str | None = Query(default=None),
    active_session: bool | None = Query(default=None),
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> list[dict]:
    if institution and not current_user.has_role(ROLE_SYSADMIN) and institution != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for institution filter.")
    return reviewer_queue(
        db,
        actor_institution_id=current_user.institution_id,
        actor_roles=current_user.roles,
        institution_id=institution,
        risk_level=risk_level,
        unresolved=unresolved,
        examination_id=examination,
        active_session=active_session,
    )


@router.post(
    "/examination-sessions/{session_id}/reviewer-decisions",
    response_model=ReviewerDecisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reviewer_decision(
    session_id: str,
    payload: ReviewerDecisionCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> object:
    try:
        result = record_reviewer_decision(
            db,
            session_id=session_id,
            payload=payload,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        db.commit()
        db.refresh(result)
        return result
    except (GovernanceNotFound, GovernanceAccessDenied, GovernanceConflict) as exc:
        db.rollback()
        _raise_http(exc)


@router.get(
    "/examination-sessions/{session_id}/governance-timeline",
    response_model=list[TimelineEntry],
)
def get_governance_timeline(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        return governance_timeline(
            db,
            session_id=session_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    except (GovernanceNotFound, GovernanceAccessDenied) as exc:
        _raise_http(exc)


@router.post(
    "/examination-sessions/{session_id}/reports",
    response_model=SessionReportRead,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> object:
    try:
        result = generate_report(
            db,
            session_id=session_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        db.commit()
        db.refresh(result)
        return result
    except (GovernanceNotFound, GovernanceAccessDenied, GovernanceConflict) as exc:
        db.rollback()
        _raise_http(exc)


@router.get(
    "/examination-sessions/{session_id}/reports/{report_id}",
    response_model=SessionReportRead,
)
def retrieve_report(
    session_id: str,
    report_id: str,
    current_user: CurrentUser = Depends(require_roles(*GOVERNANCE_ROLES)),
    db: Session = Depends(get_db),
) -> object:
    try:
        return get_report(
            db,
            session_id=session_id,
            report_id=report_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    except (GovernanceNotFound, GovernanceAccessDenied) as exc:
        _raise_http(exc)
