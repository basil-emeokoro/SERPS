from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.domain.evidence import EvidenceEvent
from serps_pop.evidence.services import (
    EvidenceAccessDenied,
    EvidenceSessionNotFound,
    list_session_evidence_events,
)
from serps_pop.identity.models import ExaminationSession
from serps_pop.identity.schemas import ExaminationSessionCreate, ExaminationSessionRead, ExaminationSessionTransition
from serps_pop.identity.services import (
    DomainConflict,
    DomainNotFound,
    InvalidTransition,
    ROLE_ADMIN,
    ROLE_REVIEWER,
    ROLE_SYSADMIN,
    create_examination_session,
    transition_session,
)

router = APIRouter()


@router.post("/", response_model=ExaminationSessionRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: ExaminationSessionCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> ExaminationSession:
    try:
        session = create_examination_session(
            db,
            assignment_id=payload.assignment_id,
            deployment_mode=payload.deployment_mode,
            institution_id=current_user.institution_id,
            actor_user_id=current_user.user_id,
        )
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    db.commit()
    db.refresh(session)
    return session


@router.get("/", response_model=list[ExaminationSessionRead])
def list_sessions(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[ExaminationSession]:
    stmt = select(ExaminationSession)
    if not current_user.has_role(ROLE_SYSADMIN):
        stmt = stmt.where(ExaminationSession.institution_id == current_user.institution_id)
    return list(db.scalars(stmt.order_by(ExaminationSession.created_at.desc())).all())


@router.post("/{session_id}/transition", response_model=ExaminationSessionRead)
def transition(
    session_id: str,
    payload: ExaminationSessionTransition,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> ExaminationSession:
    session = db.get(ExaminationSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if not current_user.has_role(ROLE_SYSADMIN) and session.institution_id != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    try:
        session = transition_session(db, session, payload.status, actor_user_id=current_user.user_id)
    except InvalidTransition as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/evidence-events", response_model=list[EvidenceEvent])
def list_evidence_events(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[EvidenceEvent]:
    try:
        return list_session_evidence_events(
            db,
            session_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    except EvidenceSessionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination session not found.") from exc
    except EvidenceAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this session.") from exc
