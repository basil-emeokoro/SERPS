from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.domain.evidence import EvidenceEvent, EvidenceEventCreate
from serps_pop.evidence.services import (
    EvidenceAccessDenied,
    EvidenceCandidateMismatch,
    EvidenceEventTypeDenied,
    EvidenceSessionNotFound,
    EvidenceSessionNotActive,
    create_evidence_event as persist_evidence_event,
)
from serps_pop.governance.engine import SUPPORTED_EVENT_TYPES
from serps_pop.governance.services import (
    create_agent_recommendation,
    create_contextual_assessment,
    create_policy_evaluation,
)
from serps_pop.identity.services import ROLE_CANDIDATE

router = APIRouter()


@router.post("/", response_model=EvidenceEvent, status_code=status.HTTP_201_CREATED)
def create_evidence_event(
    payload: EvidenceEventCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> EvidenceEvent:
    try:
        event = persist_evidence_event(
            db,
            payload,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
            actor_user_id=current_user.user_id,
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
    except EvidenceSessionNotActive as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate evidence requires an active session.") from exc
    except EvidenceEventTypeDenied as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    if event.event_type in SUPPORTED_EVENT_TYPES:
        assessment = create_contextual_assessment(
            db,
            session_id=event.session_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        recommendation = create_agent_recommendation(
            db,
            assessment_id=assessment.assessment_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
        create_policy_evaluation(
            db,
            recommendation_id=recommendation.recommendation_id,
            actor_user_id=current_user.user_id,
            actor_institution_id=current_user.institution_id,
            actor_roles=current_user.roles,
        )
    db.commit()
    return event
