from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.domain.evidence import EvidenceEvent, EvidenceEventCreate
from serps_pop.evidence.services import (
    EvidenceAccessDenied,
    EvidenceCandidateMismatch,
    EvidenceSessionNotFound,
    create_evidence_event as persist_evidence_event,
)
from serps_pop.identity.services import ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN

router = APIRouter()


@router.post("/", response_model=EvidenceEvent, status_code=status.HTTP_201_CREATED)
def create_evidence_event(
    payload: EvidenceEventCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> EvidenceEvent:
    try:
        event = persist_evidence_event(
            db,
            payload,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    except EvidenceSessionNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination session not found.") from exc
    except EvidenceAccessDenied as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this session.") from exc
    except EvidenceCandidateMismatch as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence candidate does not match the examination session candidate.",
        ) from exc
    db.commit()
    return event
