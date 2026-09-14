from __future__ import annotations

import hashlib
import json
import math
import random
import secrets
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from serps_pop.identity.models import Candidate, Institution, User, UserRole
from serps_pop.identity.services import (
    DomainConflict,
    DomainNotFound,
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_REVIEWER,
    audit,
    ensure_roles,
    issue_tokens,
    user_roles,
    validate_email,
)
from serps_pop.security.passwords import hash_password, verify_password

from .models import BiometricEnrollment, IdentityAssuranceProfile, IdentityChallenge, RegistrationRequest, utc_now
from .schemas import EnrollmentSubmit, FaceAuthenticationSubmit, RegistrationCreate, RegistrationDecision

POSE_SEQUENCE = ["forward", "left", "right", "up", "down", "centre_confirmation"]
LIVENESS_ACTIONS = ["turn_left", "turn_right", "look_up", "look_down", "return_to_centre"]
CHALLENGE_MINUTES = 10


def _validated_configured_fields(institution: Institution, payload: RegistrationCreate) -> tuple[dict, str | None]:
    configuration = institution.metadata_json.get("registration_configuration", {})
    if not configuration.get("enabled", False):
        raise DomainConflict("Registration is disabled for this institution.")
    version = str(configuration.get("version", ""))
    if payload.configuration_version != version:
        raise DomainConflict("Registration configuration changed. Refresh the form and try again.")
    definitions = {
        item["name"]: item for item in configuration.get("fields", [])
        if item.get("active", True) and payload.account_type in item.get("applies_to", ["candidate"])
    }
    unknown = set(payload.configured_fields) - set(definitions)
    if unknown:
        raise DomainConflict(f"Unknown configured registration field: {sorted(unknown)[0]}.")
    cleaned = {}
    for name, definition in definitions.items():
        value = payload.configured_fields.get(name)
        missing = value is None or value == "" or value is False
        if definition.get("required") and missing:
            raise DomainConflict(f"{definition.get('label', name)} is required.")
        if missing:
            continue
        field_type = definition.get("type", "text")
        if field_type == "checkbox" and not isinstance(value, bool):
            raise DomainConflict(f"{definition.get('label', name)} must be a checkbox value.")
        if field_type == "number" and not str(value).isdigit():
            raise DomainConflict(f"{definition.get('label', name)} must be numeric.")
        if field_type == "email":
            value = validate_email(str(value))
        if field_type == "select" and value not in definition.get("options", []):
            raise DomainConflict(f"{definition.get('label', name)} contains an unsupported option.")
        pattern = definition.get("pattern")
        if pattern and not re.fullmatch(pattern, str(value)):
            raise DomainConflict(f"{definition.get('label', name)} has an invalid format.")
        cleaned[name] = value
    identifier_name = configuration.get("candidate_identifier_field")
    return cleaned, str(cleaned.get(identifier_name)) if identifier_name and cleaned.get(identifier_name) is not None else None


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_challenge(db: Session, user_id: str, purpose: str, actions: list[str]) -> tuple[IdentityChallenge, str]:
    token = secrets.token_urlsafe(32)
    challenge = IdentityChallenge(
        user_id=user_id,
        purpose=purpose,
        token_hash=_token_hash(token),
        required_actions=actions,
        expires_at=utc_now() + timedelta(minutes=CHALLENGE_MINUTES),
    )
    db.add(challenge)
    db.flush()
    return challenge, token


def _load_challenge(db: Session, token: str, purpose: str) -> IdentityChallenge:
    challenge = db.scalar(
        select(IdentityChallenge).where(
            IdentityChallenge.token_hash == _token_hash(token),
            IdentityChallenge.purpose == purpose,
        )
    )
    if challenge is None or challenge.status != "pending":
        raise DomainNotFound("Identity challenge is invalid or already used.")
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < utc_now():
        challenge.status = "expired"
        raise DomainConflict("Identity challenge has expired.")
    return challenge


def _create_user(
    db: Session,
    registration: RegistrationRequest,
    role_name: str,
    *,
    status: str,
) -> User:
    roles = ensure_roles(db)
    if db.scalar(select(User).where(User.institution_id == registration.institution_id, User.email == registration.email)):
        raise DomainConflict("An account already exists for this institution and email.")
    user = User(
        institution_id=registration.institution_id,
        email=registration.email,
        full_name=registration.full_name,
        password_hash=registration.password_hash,
        status=status,
    )
    user.roles.append(UserRole(role=roles[role_name]))
    db.add(user)
    db.flush()
    registration.user_id = user.user_id
    return user


def register_account(db: Session, payload: RegistrationCreate) -> tuple[RegistrationRequest, str | None, list[str]]:
    institution = db.scalar(
        select(Institution).where(
            Institution.code == payload.institution_code.strip().upper(),
            Institution.is_active.is_(True),
        )
    )
    if institution is None:
        raise DomainNotFound("Active institution not found.")
    configured_fields, configured_identifier = _validated_configured_fields(institution, payload)
    email = validate_email(payload.email)
    if db.scalar(select(User).where(User.institution_id == institution.institution_id, User.email == email)):
        raise DomainConflict("An account already exists for this institution and email.")
    if payload.account_type == "candidate" and db.scalar(
        select(Candidate).where(
            Candidate.institution_id == institution.institution_id,
            (Candidate.email == email) | (Candidate.candidate_identifier == (configured_identifier or payload.candidate_identifier)),
        )
    ):
        raise DomainConflict("A candidate identity already exists for this institution.")
    registration = RegistrationRequest(
        institution_id=institution.institution_id,
        account_type=payload.account_type,
        email=email,
        full_name=payload.full_name.strip(),
        candidate_identifier=configured_identifier or (payload.candidate_identifier.strip() if payload.candidate_identifier else None),
        password_hash=hash_password(payload.password),
        configured_fields=configured_fields,
        configuration_version=payload.configuration_version,
    )
    db.add(registration)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("A registration request already exists for this account.") from exc

    enrollment_token = None
    required_actions: list[str] = []
    if payload.account_type == "candidate":
        registration.prototype_verified = True
        registration.verification_status = "prototype_verified"
        registration.verified_at = utc_now()
        registration.status = "pending_facial_enrolment"
        user = _create_user(db, registration, ROLE_CANDIDATE, status="pending_facial_enrolment")
        registration.password_hash = "retired_after_account_creation"
        candidate = Candidate(
            user_id=user.user_id,
            institution_id=institution.institution_id,
            candidate_identifier=registration.candidate_identifier or "",
            full_name=registration.full_name,
            email=registration.email,
            status="pending_facial_enrolment",
            profile_metadata={"prototype_email_verification": True, "configured_registration_fields": configured_fields, "configuration_version": payload.configuration_version},
        )
        db.add(candidate)
        profile = IdentityAssuranceProfile(
            user_id=user.user_id,
            registration_id=registration.registration_id,
            biometric_required=True,
            enrolment_status="pending",
        )
        db.add(profile)
        challenge, enrollment_token = _new_challenge(
            db,
            user.user_id,
            "enrollment",
            random.sample(LIVENESS_ACTIONS[:-1], 2) + ["return_to_centre"],
        )
        required_actions = challenge.required_actions
        audit(
            db,
            action="identity.registration.prototype_verify",
            result="success",
            institution_id=institution.institution_id,
            actor_user_id=user.user_id,
            target_type="registration",
            target_id=registration.registration_id,
            metadata={"challenge_id": challenge.challenge_id, "method": "bounded_prototype_verification"},
        )
    else:
        registration.status = "pending_approval"

    audit(
        db,
        action="identity.registration.request",
        result="success",
        institution_id=institution.institution_id,
        actor_user_id=registration.user_id,
        target_type="registration",
        target_id=registration.registration_id,
        metadata={"account_type": payload.account_type, "status": registration.status},
    )
    return registration, enrollment_token, required_actions


def resume_candidate_enrollment(db: Session, institution_code: str | None, email: str, password: str) -> tuple[IdentityChallenge, str]:
    normalised_email = validate_email(email)
    query = select(User, Institution).join(Institution, Institution.institution_id == User.institution_id).where(
        User.email == normalised_email,
        Institution.is_active.is_(True),
    )
    if institution_code:
        query = query.where(Institution.code == institution_code.strip().upper())
    matches = db.execute(query).all()
    valid_matches = [
        (user, institution)
        for user, institution in matches
        if user.status == "pending_facial_enrolment" and verify_password(password, user.password_hash)
    ]
    if len(valid_matches) != 1:
        raise DomainNotFound("Pending candidate enrolment not found or credentials are invalid.")
    user, institution = valid_matches[0]
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == user.user_id))
    if profile is None or profile.enrolment_status != "pending":
        raise DomainConflict("Candidate facial enrolment is not resumable.")
    pending = db.scalars(select(IdentityChallenge).where(
        IdentityChallenge.user_id == user.user_id,
        IdentityChallenge.purpose == "enrollment",
        IdentityChallenge.status == "pending",
    )).all()
    for item in pending:
        item.status = "superseded"
    actions = random.sample(LIVENESS_ACTIONS[:-1], 2) + ["return_to_centre"]
    challenge, token = _new_challenge(db, user.user_id, "enrollment", actions)
    audit(db, action="identity.enrollment.resume", result="success", institution_id=institution.institution_id,
          actor_user_id=user.user_id, target_type="identity_challenge", target_id=challenge.challenge_id,
          metadata={"prior_pending_challenges_superseded": len(pending)})
    return challenge, token


def decide_registration(
    db: Session,
    registration_id: str,
    decision: RegistrationDecision,
    actor_user_id: str,
) -> RegistrationRequest:
    registration = db.get(RegistrationRequest, registration_id)
    if registration is None:
        raise DomainNotFound("Registration request not found.")
    if registration.status != "pending_approval":
        raise DomainConflict("Only pending approval requests can be reviewed.")
    registration.reviewed_by = actor_user_id
    registration.reviewed_at = utc_now()
    if decision.decision == "reject":
        registration.status = "rejected"
        registration.rejection_reason = decision.rationale
    else:
        role = ROLE_REVIEWER if registration.account_type == "reviewer" else ROLE_ADMIN
        user = _create_user(db, registration, role, status="active")
        registration.password_hash = "retired_after_account_creation"
        db.add(
            IdentityAssuranceProfile(
                user_id=user.user_id,
                registration_id=registration.registration_id,
                biometric_required=False,
                enrolment_status="not_required",
            )
        )
        registration.status = "active"
    audit(
        db,
        action="identity.registration.decision",
        result="success",
        institution_id=registration.institution_id,
        actor_user_id=actor_user_id,
        target_type="registration",
        target_id=registration.registration_id,
        metadata={"decision": decision.decision, "rationale": decision.rationale},
    )
    return registration


def list_registrations(db: Session, institution_id: str | None = None) -> list[RegistrationRequest]:
    stmt = select(RegistrationRequest).order_by(RegistrationRequest.requested_at.desc())
    if institution_id:
        stmt = stmt.where(RegistrationRequest.institution_id == institution_id)
    return list(db.scalars(stmt).all())


def _mean_descriptor(descriptors: list[list[float]]) -> list[float]:
    length = len(descriptors[0])
    if any(len(item) != length for item in descriptors):
        raise DomainConflict("Facial descriptors must use a consistent representation length.")
    return [round(sum(item[index] for item in descriptors) / len(descriptors), 6) for index in range(length)]


def _validate_actions(required: list[str], submitted) -> float:
    actions = [item.action for item in submitted if item.completed]
    if actions != required:
        raise DomainConflict("The dynamic liveness sequence was not completed in the required order.")
    intervals = [(submitted[index].timestamp - submitted[index - 1].timestamp).total_seconds() for index in range(1, len(submitted))]
    if any(interval < 0.35 for interval in intervals) or sum(intervals) < 1.0:
        raise DomainConflict("The liveness sequence was completed too quickly to demonstrate ordered movement.")
    confidence = sum(item.confidence for item in submitted) / len(submitted)
    if confidence < 0.6:
        raise DomainConflict("Liveness confidence is insufficient; retry in stable lighting.")
    return confidence


def complete_enrollment(db: Session, payload: EnrollmentSubmit) -> BiometricEnrollment:
    challenge = _load_challenge(db, payload.enrollment_token, "enrollment")
    existing = db.scalar(
        select(BiometricEnrollment).where(
            BiometricEnrollment.user_id == challenge.user_id,
            BiometricEnrollment.status == "active",
        )
    )
    if existing:
        raise DomainConflict("An active facial enrolment already exists for this account.")
    if [capture.pose for capture in payload.captures] != POSE_SEQUENCE:
        raise DomainConflict("All six directional poses must be completed in the required order.")
    if any(not item.one_face or not item.pose_validated for item in payload.captures):
        raise DomainConflict("Each capture must contain exactly one face and satisfy its directional prompt.")
    if any(item.lighting_score < 0.45 or item.distance_score < 0.45 or item.confidence < 0.55 for item in payload.captures):
        raise DomainConflict("One or more captures do not meet lighting, distance, or confidence requirements.")
    liveness_confidence = _validate_actions(challenge.required_actions, payload.liveness_actions)
    liveness_duration = max(0.0, (payload.liveness_actions[-1].timestamp - payload.liveness_actions[0].timestamp).total_seconds())
    centre = [payload.captures[0].descriptor, payload.captures[-1].descriptor]
    representation = _mean_descriptor(centre)
    representation_hash = hashlib.sha256(json.dumps(representation, separators=(",", ":")).encode()).hexdigest()
    enrollment = BiometricEnrollment(
        user_id=challenge.user_id,
        representation_json=representation,
        representation_hash=representation_hash,
        capture_summary={
            "poses": POSE_SEQUENCE,
            "method": "local_mediapipe_landmarks_and_experimental_luminance_similarity_descriptor",
            "detector": "MediaPipe Tasks Vision Face Landmarker 0.10.35",
            "liveness_actions": [item.action for item in payload.liveness_actions],
            "liveness_completion_seconds": round(liveness_duration, 3),
            "retry_count": payload.retry_count,
            "raw_media_stored": False,
        },
        capture_count=6,
        liveness_confidence=liveness_confidence,
        retry_count=payload.retry_count,
    )
    db.add(enrollment)
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == challenge.user_id))
    user = db.get(User, challenge.user_id)
    if profile is None or user is None:
        raise DomainNotFound("Identity-assurance profile not found.")
    profile.enrolment_status = "enrolled"
    profile.liveness_result = "passed"
    user.status = "active"
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == user.user_id))
    if candidate:
        candidate.status = "active"
    registration = db.get(RegistrationRequest, profile.registration_id) if profile.registration_id else None
    if registration:
        registration.status = "active"
    challenge.status = "completed"
    challenge.confidence = liveness_confidence
    challenge.retry_count = payload.retry_count
    challenge.completed_at = utc_now()
    audit(
        db,
        action="identity.biometric.enrol",
        result="success",
        institution_id=user.institution_id,
        actor_user_id=user.user_id,
        target_type="biometric_enrollment",
        target_id=enrollment.enrollment_id,
        metadata={"capture_count": 6, "liveness_confidence": liveness_confidence, "raw_media_stored": False},
    )
    return enrollment


def begin_facial_authentication(db: Session, user: User) -> tuple[IdentityChallenge, str] | None:
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == user.user_id))
    if profile is None or not profile.biometric_required or profile.demo_bypass:
        return None
    enrollment = db.scalar(
        select(BiometricEnrollment).where(
            BiometricEnrollment.user_id == user.user_id,
            BiometricEnrollment.status == "active",
        )
    )
    if enrollment is None:
        raise DomainConflict("Facial enrolment is required before this account can sign in.")
    actions = random.sample(LIVENESS_ACTIONS[:-1], 2) + ["return_to_centre"]
    challenge, token = _new_challenge(db, user.user_id, "authentication", actions)
    audit(
        db,
        action="identity.password_stage",
        result="success",
        institution_id=user.institution_id,
        actor_user_id=user.user_id,
        target_type="identity_challenge",
        target_id=challenge.challenge_id,
    )
    return challenge, token


def _similarity(enrolled: list[float], observed: list[float]) -> float:
    if len(enrolled) != len(observed):
        return 0.0
    rmse = math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(enrolled, observed)) / len(enrolled))
    return max(0.0, min(1.0, 1.0 - rmse))


def verify_facial_authentication(
    db: Session, payload: FaceAuthenticationSubmit, *, purpose: str = "authentication"
) -> tuple[User, float, str]:
    challenge = _load_challenge(db, payload.challenge_token, purpose)
    user = db.scalar(
        select(User).options(selectinload(User.roles).selectinload(UserRole.role)).where(User.user_id == challenge.user_id)
    )
    enrollment = db.scalar(
        select(BiometricEnrollment).where(
            BiometricEnrollment.user_id == challenge.user_id,
            BiometricEnrollment.status == "active",
        )
    )
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == challenge.user_id))
    if user is None or enrollment is None or profile is None:
        raise DomainNotFound("Active facial enrolment not found.")
    challenge.retry_count = payload.retry_count
    if not payload.one_face or payload.lighting_score < 0.45 or payload.distance_score < 0.45:
        challenge.status = "pending"
        profile.authentication_result = "retry_required"
        profile.liveness_result = "retry_required"
        return user, 0.0, "Retry Required"
    liveness_confidence = _validate_actions(challenge.required_actions, payload.liveness_actions)
    confidence = _similarity(enrollment.representation_json, payload.descriptor)
    if confidence >= 0.72:
        outcome = "Verified"
        challenge.status = "completed"
        challenge.completed_at = utc_now()
        profile.authentication_result = "verified"
        profile.liveness_result = "passed"
        profile.identity_confidence = confidence
        profile.last_verified_at = utc_now()
    elif confidence >= 0.58:
        outcome = "Manual Review"
        challenge.status = "manual_review"
        profile.authentication_result = "manual_review"
        profile.liveness_result = "passed"
    else:
        outcome = "Authentication Failed"
        challenge.status = "failed"
        profile.authentication_result = "failed"
        profile.liveness_result = "passed"
    challenge.confidence = confidence
    challenge.metadata_json = {"liveness_confidence": liveness_confidence, "raw_media_stored": False}
    audit(
        db,
        action="identity.facial_authentication",
        result="success" if outcome == "Verified" else "failure",
        institution_id=user.institution_id,
        actor_user_id=user.user_id,
        target_type="identity_challenge",
        target_id=challenge.challenge_id,
        metadata={"outcome": outcome, "confidence": confidence, "liveness_confidence": liveness_confidence},
    )
    return user, confidence, outcome


def begin_periodic_verification(db: Session, user: User) -> tuple[IdentityChallenge, str]:
    actions = random.sample(LIVENESS_ACTIONS[:-1], 2) + ["return_to_centre"]
    challenge, token = _new_challenge(db, user.user_id, "periodic", actions)
    audit(
        db,
        action="identity.periodic_challenge",
        result="success",
        institution_id=user.institution_id,
        actor_user_id=user.user_id,
        target_type="identity_challenge",
        target_id=challenge.challenge_id,
    )
    return challenge, token


def profile_for_user(db: Session, user_id: str) -> IdentityAssuranceProfile | None:
    return db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == user_id))


def identity_ready(db: Session, user_id: str) -> bool:
    profile = profile_for_user(db, user_id)
    if profile is None or profile.demo_bypass or not profile.biometric_required:
        return True
    if profile.authentication_result != "verified" or profile.last_verified_at is None:
        return False
    verified_at = profile.last_verified_at
    if verified_at.tzinfo is None:
        verified_at = verified_at.replace(tzinfo=timezone.utc)
    return verified_at >= utc_now() - timedelta(minutes=20)


def create_demo_profile(db: Session, user_id: str) -> IdentityAssuranceProfile:
    profile = profile_for_user(db, user_id)
    if profile is None:
        profile = IdentityAssuranceProfile(
            user_id=user_id,
            biometric_required=False,
            demo_bypass=True,
            enrolment_status="demonstration_bypass",
            authentication_result="demonstration_bypass",
            liveness_result="demonstration_bypass",
        )
        db.add(profile)
    else:
        profile.biometric_required = False
        profile.demo_bypass = True
        profile.enrolment_status = "demonstration_bypass"
        profile.authentication_result = "demonstration_bypass"
        profile.liveness_result = "demonstration_bypass"
    return profile
