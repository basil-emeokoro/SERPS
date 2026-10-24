from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.governance.models import InstitutionalPolicy
from serps_pop.governance.services import get_or_create_default_policy
from serps_pop.identity.services import DomainConflict, DomainNotFound, ROLE_ADMIN, ROLE_SYSADMIN, ROLE_CANDIDATE
from serps_pop.identity_assurance import reauthentication as lifecycle
from serps_pop.identity_assurance.schemas import FaceAuthenticationSubmit

router = APIRouter()


@router.get("/policy")
def read_policy(user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    policy = db.scalar(select(InstitutionalPolicy).where(
        InstitutionalPolicy.institution_id == user.institution_id, InstitutionalPolicy.status == "active"
    ).order_by(InstitutionalPolicy.created_at.desc()).limit(1))
    return lifecycle.configured_policy(policy) if policy else lifecycle.IdentityReauthenticationPolicy()


@router.put("/policy")
def configure_policy(payload: lifecycle.IdentityReauthenticationPolicy,
                     user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    old = get_or_create_default_policy(db, user.institution_id, user.user_id)
    # Institutional policies are immutable. Configuration creates a new version.
    policy = InstitutionalPolicy(institution_id=user.institution_id, created_by=user.user_id,
        policy_version="IPIME-IDENTITY-1.0", high_risk_action=old.high_risk_action,
        critical_risk_action=old.critical_risk_action, reviewer_notification_threshold=old.reviewer_notification_threshold,
        candidate_acknowledgement_required=old.candidate_acknowledgement_required,
        reauthentication_threshold=old.reauthentication_threshold, automatic_exam_termination_allowed=False,
        metadata_json={**old.metadata_json, "identity_reauthentication": payload.model_dump(), "previous_policy_id": old.policy_id})
    db.add(policy)
    db.commit()
    return {"policy_id": policy.policy_id, "identity_reauthentication": payload.model_dump()}


def invoke(db, operation):
    try:
        result = operation()
        db.commit()
        return result
    except (DomainConflict, DomainNotFound) as exc:
        db.rollback()
        raise HTTPException(status_code=404 if isinstance(exc, DomainNotFound) else 409, detail=str(exc)) from exc


@router.get("/sessions/{session_id}")
def status(session_id: str, user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)), db: Session = Depends(get_db)):
    def read():
        lifecycle.candidate_session(db, session_id, user.user_id, user.institution_id)
        return lifecycle.state(lifecycle.latest_requirement(db, session_id), session_id)
    return invoke(db, read)


@router.post("/sessions/{session_id}/challenge")
def challenge(session_id: str, user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)), db: Session = Depends(get_db)):
    return invoke(db, lambda: lifecycle.begin(db, session_id, user.user_id, user.institution_id))


@router.post("/sessions/{session_id}/verify")
def verify(session_id: str, payload: FaceAuthenticationSubmit,
           user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)), db: Session = Depends(get_db)):
    return invoke(db, lambda: lifecycle.verify(db, session_id, user.user_id, user.institution_id, payload))
