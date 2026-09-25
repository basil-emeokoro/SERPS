from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, get_current_user, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.services import DomainConflict, DomainNotFound, ROLE_ADMIN, ROLE_CANDIDATE, ROLE_SYSADMIN, issue_tokens
from serps_pop.identity_assurance.schemas import (
    ChallengeRead,
    EnrollmentResumeCreate,
    EnrollmentSubmit,
    FaceAuthenticationSubmit,
    IdentityStatusRead,
    RegistrationCreate,
    RegistrationDecision,
    InstitutionRegistrationRead,
    RegistrationRead,
)
from serps_pop.identity_assurance.services import (
    complete_enrollment,
    decide_registration,
    list_registrations,
    profile_for_user,
    register_account,
    resume_candidate_enrollment,
    verify_facial_authentication,
)

router = APIRouter()


@router.get("/institutions", response_model=list[InstitutionRegistrationRead])
def public_registration_institutions(db: Session = Depends(get_db)) -> list[InstitutionRegistrationRead]:
    from serps_pop.identity.models import Institution
    institutions = db.scalars(select(Institution).where(Institution.is_active.is_(True)).order_by(Institution.name)).all()
    result = []
    for institution in institutions:
        config = institution.metadata_json.get("registration_configuration", {})
        if config.get("enabled", False):
            result.append(InstitutionRegistrationRead(code=institution.code, name=institution.name, **config))
    return result


def _error(exc: Exception) -> None:
    if isinstance(exc, DomainNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/registrations", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def create_registration(payload: RegistrationCreate, db: Session = Depends(get_db)) -> RegistrationRead:
    try:
        registration, enrollment_token, required_actions = register_account(db, payload)
        db.commit()
        return RegistrationRead(
            registration_id=registration.registration_id,
            account_type=registration.account_type,
            email=registration.email,
            status=registration.status,
            prototype_verified=registration.prototype_verified,
            requested_at=registration.requested_at,
            enrollment_token=enrollment_token,
            required_actions=required_actions,
            institution_code=payload.institution_code.strip().upper(),
            configuration_version=registration.configuration_version,
            configured_fields=registration.configured_fields,
            verification_status=registration.verification_status,
        )
    except (DomainConflict, DomainNotFound, ValueError) as exc:
        db.rollback()
        _error(exc)


@router.get("/registrations", response_model=list[RegistrationRead])
def registrations(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[RegistrationRead]:
    institution_id = None if current_user.has_role(ROLE_SYSADMIN) else current_user.institution_id
    return [
        RegistrationRead(
            registration_id=item.registration_id,
            account_type=item.account_type,
            email=item.email,
            status=item.status,
            prototype_verified=item.prototype_verified,
            requested_at=item.requested_at,
            configuration_version=item.configuration_version,
            configured_fields=item.configured_fields,
            verification_status=item.verification_status,
        )
        for item in list_registrations(db, institution_id)
    ]


@router.post("/registrations/{registration_id}/decision", response_model=RegistrationRead)
def registration_decision(
    registration_id: str,
    payload: RegistrationDecision,
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> RegistrationRead:
    try:
        item = decide_registration(db, registration_id, payload, current_user.user_id)
        db.commit()
        return RegistrationRead(
            registration_id=item.registration_id,
            account_type=item.account_type,
            email=item.email,
            status=item.status,
            prototype_verified=item.prototype_verified,
            requested_at=item.requested_at,
            configuration_version=item.configuration_version,
            configured_fields=item.configured_fields,
            verification_status=item.verification_status,
        )
    except (DomainConflict, DomainNotFound) as exc:
        db.rollback()
        _error(exc)


@router.post("/enrollments", status_code=status.HTTP_201_CREATED)
def enroll(payload: EnrollmentSubmit, db: Session = Depends(get_db)) -> dict:
    try:
        enrollment = complete_enrollment(db, payload)
        db.commit()
        return {
            "enrollment_id": enrollment.enrollment_id,
            "status": enrollment.status,
            "capture_count": enrollment.capture_count,
            "liveness_confidence": enrollment.liveness_confidence,
            "raw_media_stored": False,
        }
    except (DomainConflict, DomainNotFound) as exc:
        db.rollback()
        _error(exc)


@router.post("/enrollments/resume", response_model=ChallengeRead)
def resume_enrollment(payload: EnrollmentResumeCreate, db: Session = Depends(get_db)) -> ChallengeRead:
    try:
        challenge, token = resume_candidate_enrollment(db, payload.institution_code, payload.email, payload.password)
        db.commit()
        return ChallengeRead(challenge_id=challenge.challenge_id, challenge_token=token, purpose=challenge.purpose,
                             required_actions=challenge.required_actions, expires_at=challenge.expires_at)
    except (DomainConflict, DomainNotFound, ValueError) as exc:
        db.rollback()
        _error(exc)


@router.post("/facial-authentication")
def facial_authentication(payload: FaceAuthenticationSubmit, db: Session = Depends(get_db)) -> dict:
    try:
        user, confidence, outcome = verify_facial_authentication(db, payload)
        response = {"outcome": outcome, "identity_confidence": confidence}
        if outcome == "Verified":
            access_token, refresh_token, _ = issue_tokens(db, user)
            response.update(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=20 * 60,
            )
        db.commit()
        return response
    except (DomainConflict, DomainNotFound) as exc:
        db.rollback()
        _error(exc)


@router.post("/periodic/challenge")
def periodic_challenge(current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE))) -> dict:
    raise HTTPException(status_code=410, detail="Periodic identity challenges are retired. Return to the originating examination for its institutionally governed identity requirement.")


@router.post("/periodic/verify")
def periodic_verify(payload: FaceAuthenticationSubmit,
                    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE))) -> dict:
    raise HTTPException(status_code=410, detail="Unbound periodic challenges cannot verify an examination. Return to the originating session; existing challenge records are preserved for review.")


@router.get("/status", response_model=IdentityStatusRead)
def identity_status(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IdentityStatusRead:
    profile = profile_for_user(db, current_user.user_id)
    if profile is None:
        return IdentityStatusRead(
            user_id=current_user.user_id,
            biometric_required=False,
            demo_bypass=False,
            enrolment_status="legacy_account",
            authentication_result="password_only",
            identity_confidence=None,
            liveness_result="not_required",
            last_verified_at=None,
        )
    return IdentityStatusRead.model_validate(profile, from_attributes=True)
