from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from serps_pop.config.settings import get_settings
from serps_pop.identity.models import (
    AuditLog,
    Candidate,
    CandidateExaminationAssignment,
    Examination,
    ExaminationSession,
    Institution,
    RefreshToken,
    Role,
    User,
    UserRole,
    utc_now,
)
from serps_pop.identity.schemas import (
    CandidateCreate,
    CandidateUpdate,
    ExaminationCreate,
    InstitutionCreate,
    UserCreate,
)
from serps_pop.security.passwords import hash_password, verify_password
from serps_pop.security.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)

ROLE_CANDIDATE = "Candidate"
ROLE_REVIEWER = "Reviewer/Proctor"
ROLE_ADMIN = "Administrator"
ROLE_SYSADMIN = "System Administrator"
DEFAULT_ROLES = [ROLE_CANDIDATE, ROLE_REVIEWER, ROLE_ADMIN, ROLE_SYSADMIN]

ACTIVE_SESSION_STATUSES = {"authentication_pending", "device_check_pending", "ready", "active", "paused"}
VALID_TRANSITIONS = {
    "authentication_pending": {"device_check_pending", "terminated"},
    "device_check_pending": {"ready", "terminated"},
    "ready": {"active", "terminated"},
    "active": {"paused", "completed", "terminated"},
    "paused": {"active", "completed", "terminated"},
    "completed": set(),
    "terminated": set(),
}


class DomainConflict(ValueError):
    pass


class DomainNotFound(ValueError):
    pass


class InvalidTransition(ValueError):
    pass


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
        raise ValueError("Invalid email address.")
    return normalized


def audit(
    db: Session,
    *,
    action: str,
    result: str,
    institution_id: str | None = None,
    actor_user_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    record = AuditLog(
        institution_id=institution_id,
        actor_user_id=actor_user_id,
        action=action,
        result=result,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )
    db.add(record)
    return record


def ensure_roles(db: Session) -> dict[str, Role]:
    existing = {role.name: role for role in db.scalars(select(Role)).all()}
    for role_name in DEFAULT_ROLES:
        if role_name not in existing:
            role = Role(name=role_name, description=f"SERPS {role_name} role")
            db.add(role)
            existing[role_name] = role
    db.flush()
    return existing


def create_institution(db: Session, payload: InstitutionCreate, actor_user_id: str | None = None) -> Institution:
    institution = Institution(
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        institution_type=payload.institution_type.strip().lower(),
        metadata_json=payload.metadata_json,
    )
    db.add(institution)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Institution code already exists.") from exc
    audit(
        db,
        action="institution.create",
        result="success",
        institution_id=institution.institution_id,
        actor_user_id=actor_user_id,
        target_type="institution",
        target_id=institution.institution_id,
    )
    return institution


def create_user(db: Session, payload: UserCreate, actor_user_id: str | None = None) -> User:
    roles = ensure_roles(db)
    email = validate_email(payload.email)
    if not db.get(Institution, payload.institution_id):
        raise DomainNotFound("Institution not found.")
    user = User(
        institution_id=payload.institution_id,
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    for role_name in payload.roles:
        if role_name not in roles:
            raise DomainNotFound(f"Role not found: {role_name}")
        user.roles.append(UserRole(role=roles[role_name]))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("User email already exists for this institution.") from exc
    audit(
        db,
        action="user.create",
        result="success",
        institution_id=user.institution_id,
        actor_user_id=actor_user_id,
        target_type="user",
        target_id=user.user_id,
        metadata={"roles": payload.roles},
    )
    return user


def user_roles(user: User) -> list[str]:
    return [association.role.name for association in user.roles]


def authenticate_user(db: Session, *, email: str, password: str, institution_code: str | None = None) -> User | None:
    email = validate_email(email)
    stmt = select(User).options(selectinload(User.roles).selectinload(UserRole.role)).where(User.email == email)
    if institution_code:
        stmt = stmt.join(Institution).where(Institution.code == institution_code.strip().upper())
    users = db.scalars(stmt).all()
    for user in users:
        if user.status != "active":
            continue
        if verify_password(password, user.password_hash):
            user.failed_login_count = 0
            user.last_login_at = utc_now()
            audit(
                db,
                action="auth.login",
                result="success",
                institution_id=user.institution_id,
                actor_user_id=user.user_id,
                target_type="user",
                target_id=user.user_id,
            )
            return user
        user.failed_login_count += 1
    audit(db, action="auth.login", result="failure", metadata={"email": email})
    return None


def issue_tokens(db: Session, user: User) -> tuple[str, str, RefreshToken]:
    roles = user_roles(user)
    access_token = create_access_token(subject=user.user_id, institution_id=user.institution_id, roles=roles)
    refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days)
    record = RefreshToken(
        user_id=user.user_id,
        institution_id=user.institution_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    return access_token, refresh_token, record


def rotate_refresh_token(db: Session, token: str) -> tuple[str, str] | None:
    token_hash = hash_refresh_token(token)
    record = db.scalar(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user).selectinload(User.roles).selectinload(UserRole.role))
        .where(RefreshToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    expires_at = None
    if record is not None:
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    if record is None or record.revoked_at is not None or expires_at < now or record.user.status != "active":
        return None
    new_access, new_refresh, new_record = issue_tokens(db, record.user)
    record.revoked_at = now
    record.replaced_by_token_hash = new_record.token_hash
    audit(
        db,
        action="auth.refresh",
        result="success",
        institution_id=record.institution_id,
        actor_user_id=record.user_id,
        target_type="refresh_token",
        target_id=record.refresh_token_id,
    )
    return new_access, new_refresh


def revoke_refresh_token(db: Session, token: str, actor_user_id: str | None = None) -> bool:
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token)))
    if record is None or record.revoked_at is not None:
        return False
    record.revoked_at = datetime.now(timezone.utc)
    audit(
        db,
        action="auth.logout",
        result="success",
        institution_id=record.institution_id,
        actor_user_id=actor_user_id or record.user_id,
        target_type="refresh_token",
        target_id=record.refresh_token_id,
    )
    return True


def create_candidate(db: Session, payload: CandidateCreate, institution_id: str, actor_user_id: str | None) -> Candidate:
    candidate = Candidate(
        institution_id=institution_id,
        candidate_identifier=payload.candidate_identifier.strip(),
        identifier_type=payload.identifier_type.strip(),
        full_name=payload.full_name.strip(),
        email=validate_email(payload.email),
        matric_number=payload.matric_number,
        registration_number=payload.registration_number,
        centre_number=payload.centre_number,
        candidate_number=payload.candidate_number,
        programme=payload.programme,
        department=payload.department,
        profile_metadata=payload.profile_metadata,
    )
    db.add(candidate)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Candidate identifier, email or institution-specific registration value already exists.") from exc
    audit(
        db,
        action="candidate.create",
        result="success",
        institution_id=institution_id,
        actor_user_id=actor_user_id,
        target_type="candidate",
        target_id=candidate.candidate_id,
    )
    return candidate


def update_candidate(db: Session, candidate: Candidate, payload: CandidateUpdate, actor_user_id: str | None) -> Candidate:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "email" and value is not None:
            value = validate_email(value)
        setattr(candidate, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Candidate email already exists for this institution.") from exc
    audit(
        db,
        action="candidate.update",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=actor_user_id,
        target_type="candidate",
        target_id=candidate.candidate_id,
    )
    return candidate


def create_examination(db: Session, payload: ExaminationCreate, institution_id: str, actor_user_id: str | None) -> Examination:
    exam = Examination(
        institution_id=institution_id,
        exam_code=payload.exam_code.strip(),
        title=payload.title.strip(),
        status=payload.status,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        duration_minutes=payload.duration_minutes,
        monitoring_mode=payload.monitoring_mode,
        policy_profile=payload.policy_profile,
    )
    db.add(exam)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Examination code already exists for this institution.") from exc
    audit(
        db,
        action="examination.create",
        result="success",
        institution_id=institution_id,
        actor_user_id=actor_user_id,
        target_type="examination",
        target_id=exam.examination_id,
    )
    return exam


def create_assignment(
    db: Session, *, candidate_id: str, examination_id: str, institution_id: str, actor_user_id: str | None
) -> CandidateExaminationAssignment:
    candidate = db.get(Candidate, candidate_id)
    exam = db.get(Examination, examination_id)
    if not candidate or not exam or candidate.institution_id != institution_id or exam.institution_id != institution_id:
        raise DomainNotFound("Candidate or examination not found in authorised institution.")
    if candidate.status != "active" or not candidate.user_id:
        raise DomainConflict("Only an active enrolled candidate can be assigned to an examination.")
    from serps_pop.identity_assurance.models import IdentityAssuranceProfile
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == candidate.user_id))
    if profile is None or profile.enrolment_status != "enrolled":
        raise DomainConflict("Only an active enrolled candidate can be assigned to an examination.")
    if not exam.is_active or exam.status != "active":
        raise DomainConflict("Only an active examination can be assigned.")
    assignment = CandidateExaminationAssignment(
        institution_id=institution_id,
        candidate_id=candidate_id,
        examination_id=examination_id,
        status="eligible",
    )
    db.add(assignment)
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Candidate is already assigned to this examination.") from exc
    audit(
        db,
        action="assignment.create",
        result="success",
        institution_id=institution_id,
        actor_user_id=actor_user_id,
        target_type="assignment",
        target_id=assignment.assignment_id,
    )
    return assignment


def create_examination_session(
    db: Session, *, assignment_id: str, deployment_mode: str, institution_id: str, actor_user_id: str | None
) -> ExaminationSession:
    assignment = db.get(CandidateExaminationAssignment, assignment_id)
    if assignment is None or assignment.institution_id != institution_id or assignment.status != "eligible":
        raise DomainNotFound("Eligible assignment not found.")
    active = db.scalar(
        select(ExaminationSession).where(
            ExaminationSession.assignment_id == assignment_id,
            ExaminationSession.status.in_(ACTIVE_SESSION_STATUSES),
        )
    )
    if active is not None:
        raise DomainConflict("An active session already exists for this assignment.")
    session = ExaminationSession(
        institution_id=institution_id,
        candidate_id=assignment.candidate_id,
        examination_id=assignment.examination_id,
        assignment_id=assignment.assignment_id,
        deployment_mode=deployment_mode,
    )
    db.add(session)
    db.flush()
    audit(
        db,
        action="session.create",
        result="success",
        institution_id=institution_id,
        actor_user_id=actor_user_id,
        target_type="examination_session",
        target_id=session.session_id,
    )
    return session


def transition_session(db: Session, session: ExaminationSession, new_status: str, actor_user_id: str | None) -> ExaminationSession:
    allowed = VALID_TRANSITIONS.get(session.status, set())
    if new_status not in allowed:
        raise InvalidTransition(f"Cannot transition session from {session.status} to {new_status}.")
    session.status = new_status
    now = utc_now()
    if new_status == "active":
        session.started_at = now
        session.monitoring_status = "active"
    if new_status in {"completed", "terminated"}:
        session.ended_at = now
        session.monitoring_status = new_status
    db.flush()
    audit(
        db,
        action="session.transition",
        result="success",
        institution_id=session.institution_id,
        actor_user_id=actor_user_id,
        target_type="examination_session",
        target_id=session.session_id,
        metadata={"status": new_status},
    )
    return session
