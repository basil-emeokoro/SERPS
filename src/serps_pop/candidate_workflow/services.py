from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from serps_pop.candidate_workflow.models import (
    CameraPermissionRecord,
    CameraSelectionRecord,
    CandidateConsent,
    DeviceCheckRecord,
)
from serps_pop.candidate_workflow.schemas import (
    CameraPermissionCreate,
    CameraSelectionCreate,
    CandidateRegistrationCreate,
    ConsentCreate,
    DeviceCheckCreate,
)
from serps_pop.identity.models import (
    Candidate,
    CandidateExaminationAssignment,
    Examination,
    ExaminationSession,
    Institution,
)
from serps_pop.identity.schemas import CandidateCreate, UserCreate
from serps_pop.identity.services import (
    ACTIVE_SESSION_STATUSES,
    DomainConflict,
    DomainNotFound,
    ROLE_CANDIDATE,
    audit,
    create_candidate,
    create_user,
    utc_now,
)

CURRENT_CONSENT_VERSION = "CONSENT-1.0"


class CandidateAccessDenied(Exception):
    pass


class CandidatePrerequisiteMissing(ValueError):
    pass


T = TypeVar("T")


def _latest(db: Session, model: type[T], candidate_id: str, timestamp_column: Any) -> T | None:
    return db.scalar(
        select(model)
        .where(model.candidate_id == candidate_id)
        .order_by(timestamp_column.desc())
        .limit(1)
    )


def candidate_for_user(db: Session, user_id: str, institution_id: str) -> Candidate:
    candidate = db.scalar(
        select(Candidate).where(Candidate.user_id == user_id, Candidate.institution_id == institution_id)
    )
    if candidate is None:
        raise DomainNotFound("Candidate account is not linked to a candidate profile.")
    return candidate


def register_candidate(db: Session, payload: CandidateRegistrationCreate) -> Candidate:
    institution = db.scalar(
        select(Institution).where(
            Institution.code == payload.institution_code.strip().upper(), Institution.is_active.is_(True)
        )
    )
    if institution is None:
        raise DomainNotFound("Active institution not found.")
    user = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            roles=[ROLE_CANDIDATE],
        ),
    )
    candidate = create_candidate(
        db,
        CandidateCreate(
            candidate_identifier=payload.candidate_identifier,
            identifier_type=payload.identifier_type,
            full_name=payload.full_name,
            email=payload.email,
            matric_number=payload.matric_number,
            registration_number=payload.registration_number,
            programme=payload.programme,
            department=payload.department,
        ),
        institution_id=institution.institution_id,
        actor_user_id=user.user_id,
    )
    candidate.user_id = user.user_id
    try:
        db.flush()
    except IntegrityError as exc:
        raise DomainConflict("Candidate account already exists.") from exc
    audit(
        db,
        action="candidate.account.register",
        result="success",
        institution_id=institution.institution_id,
        actor_user_id=user.user_id,
        target_type="candidate",
        target_id=candidate.candidate_id,
    )
    return candidate


def assigned_examinations(db: Session, candidate: Candidate) -> list[dict[str, Any]]:
    rows = db.execute(
        select(CandidateExaminationAssignment, Examination)
        .join(Examination, Examination.examination_id == CandidateExaminationAssignment.examination_id)
        .where(
            CandidateExaminationAssignment.candidate_id == candidate.candidate_id,
            CandidateExaminationAssignment.institution_id == candidate.institution_id,
        )
        .order_by(Examination.starts_at.asc().nullslast(), Examination.created_at.desc())
    ).all()
    return [
        {
            "assignment_id": assignment.assignment_id,
            "assignment_status": assignment.status,
            "examination_id": exam.examination_id,
            "exam_code": exam.exam_code,
            "title": exam.title,
            "status": exam.status,
            "starts_at": exam.starts_at,
            "ends_at": exam.ends_at,
            "duration_minutes": exam.duration_minutes,
            "monitoring_mode": exam.monitoring_mode,
        }
        for assignment, exam in rows
    ]


def record_consent(
    db: Session,
    *,
    candidate: Candidate,
    user_id: str,
    payload: ConsentCreate,
    ip_address: str | None,
    user_agent: str | None,
) -> CandidateConsent:
    accepted = all(
        (payload.monitoring_consent, payload.privacy_notice_accepted, payload.institutional_policy_accepted)
    )
    consent = CandidateConsent(
        institution_id=candidate.institution_id,
        candidate_id=candidate.candidate_id,
        user_id=user_id,
        consent_version=payload.consent_version,
        monitoring_consent=payload.monitoring_consent,
        privacy_notice_accepted=payload.privacy_notice_accepted,
        institutional_policy_accepted=payload.institutional_policy_accepted,
        accepted=accepted,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=payload.metadata,
    )
    db.add(consent)
    db.flush()
    audit(
        db,
        action="candidate.consent.record",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=user_id,
        target_type="candidate_consent",
        target_id=consent.consent_id,
        metadata={"accepted": accepted, "consent_version": payload.consent_version},
    )
    return consent


def record_device_check(
    db: Session, *, candidate: Candidate, user_id: str, payload: DeviceCheckCreate
) -> DeviceCheckRecord:
    passed = all(
        (payload.supported_browser, payload.secure_context, payload.camera_available, payload.microphone_available)
    )
    record = DeviceCheckRecord(
        institution_id=candidate.institution_id,
        candidate_id=candidate.candidate_id,
        user_id=user_id,
        supported_browser=payload.supported_browser,
        secure_context=payload.secure_context,
        camera_available=payload.camera_available,
        microphone_available=payload.microphone_available,
        browser_name=payload.browser_name,
        browser_version=payload.browser_version,
        operating_system=payload.operating_system,
        passed=passed,
        user_agent=payload.user_agent,
        metadata_json=payload.metadata,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        action="candidate.device_check.record",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=user_id,
        target_type="device_check",
        target_id=record.device_check_id,
        metadata={"passed": passed},
    )
    return record


def record_camera_selection(
    db: Session, *, candidate: Candidate, user_id: str, payload: CameraSelectionCreate
) -> CameraSelectionRecord:
    record = CameraSelectionRecord(
        institution_id=candidate.institution_id,
        candidate_id=candidate.candidate_id,
        user_id=user_id,
        device_id=payload.device_id,
        label=payload.label,
        group_id=payload.group_id,
        camera_count=payload.camera_count,
        metadata_json=payload.metadata,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        action="candidate.camera.select",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=user_id,
        target_type="camera_selection",
        target_id=record.camera_selection_id,
        metadata={"camera_count": record.camera_count},
    )
    return record


def record_camera_permission(
    db: Session, *, candidate: Candidate, user_id: str, payload: CameraPermissionCreate
) -> CameraPermissionRecord:
    record = CameraPermissionRecord(
        institution_id=candidate.institution_id,
        candidate_id=candidate.candidate_id,
        user_id=user_id,
        status=payload.status,
        granted=payload.status == "granted",
        user_agent=payload.user_agent,
        metadata_json=payload.metadata,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        action="candidate.camera_permission.record",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=user_id,
        target_type="camera_permission",
        target_id=record.camera_permission_id,
        metadata={"status": record.status, "granted": record.granted},
    )
    return record


def latest_readiness(db: Session, candidate: Candidate) -> dict[str, Any]:
    consent = _latest(db, CandidateConsent, candidate.candidate_id, CandidateConsent.accepted_at)
    device = _latest(db, DeviceCheckRecord, candidate.candidate_id, DeviceCheckRecord.checked_at)
    selection = _latest(db, CameraSelectionRecord, candidate.candidate_id, CameraSelectionRecord.selected_at)
    permission = _latest(db, CameraPermissionRecord, candidate.candidate_id, CameraPermissionRecord.checked_at)
    consent_valid = bool(
        consent
        and consent.accepted
        and consent.consent_version == CURRENT_CONSENT_VERSION
        and consent.monitoring_consent
        and consent.privacy_notice_accepted
        and consent.institutional_policy_accepted
    )
    readiness = {
        "authenticated": True,
        "consent_valid": consent_valid,
        "device_check_passed": bool(device and device.passed),
        "camera_selected": selection is not None,
        "camera_permission_granted": bool(permission and permission.granted),
    }
    readiness["ready_to_start"] = all(readiness.values())
    return {
        "consent": consent,
        "device_check": device,
        "camera_selection": selection,
        "camera_permission": permission,
        "readiness": readiness,
    }


def start_examination_session(
    db: Session,
    *,
    candidate: Candidate,
    examination_id: str,
    user_id: str,
    deployment_mode: str,
) -> ExaminationSession:
    assignment = db.scalar(
        select(CandidateExaminationAssignment).where(
            CandidateExaminationAssignment.candidate_id == candidate.candidate_id,
            CandidateExaminationAssignment.examination_id == examination_id,
            CandidateExaminationAssignment.institution_id == candidate.institution_id,
            CandidateExaminationAssignment.status == "eligible",
        )
    )
    if assignment is None:
        raise DomainNotFound("Eligible examination assignment not found.")
    active = db.scalar(
        select(ExaminationSession).where(
            ExaminationSession.assignment_id == assignment.assignment_id,
            ExaminationSession.status.in_(ACTIVE_SESSION_STATUSES),
        )
    )
    if active is not None:
        raise DomainConflict("An active examination session already exists for this assignment.")
    state = latest_readiness(db, candidate)
    missing = [name for name, passed in state["readiness"].items() if name != "ready_to_start" and not passed]
    if missing:
        raise CandidatePrerequisiteMissing(f"Examination start prerequisites are incomplete: {', '.join(missing)}.")
    now = utc_now()
    session = ExaminationSession(
        institution_id=candidate.institution_id,
        candidate_id=candidate.candidate_id,
        examination_id=examination_id,
        assignment_id=assignment.assignment_id,
        consent_id=state["consent"].consent_id,
        device_check_id=state["device_check"].device_check_id,
        camera_selection_id=state["camera_selection"].camera_selection_id,
        camera_permission_id=state["camera_permission"].camera_permission_id,
        status="active",
        deployment_mode=deployment_mode,
        authentication_gate_status="passed",
        device_check_status="passed",
        monitoring_status="active",
        started_at=now,
    )
    db.add(session)
    db.flush()
    audit(
        db,
        action="candidate.session.start",
        result="success",
        institution_id=candidate.institution_id,
        actor_user_id=user_id,
        target_type="examination_session",
        target_id=session.session_id,
        metadata={
            "assignment_id": assignment.assignment_id,
            "consent_id": session.consent_id,
            "device_check_id": session.device_check_id,
            "camera_selection_id": session.camera_selection_id,
            "camera_permission_id": session.camera_permission_id,
        },
    )
    return session


def candidate_dashboard(db: Session, candidate: Candidate) -> dict[str, Any]:
    state = latest_readiness(db, candidate)
    active_session = db.scalar(
        select(ExaminationSession)
        .where(
            ExaminationSession.candidate_id == candidate.candidate_id,
            ExaminationSession.status.in_(ACTIVE_SESSION_STATUSES),
        )
        .order_by(ExaminationSession.created_at.desc())
        .limit(1)
    )
    return {
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "candidate_identifier": candidate.candidate_identifier,
            "institution_id": candidate.institution_id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "status": candidate.status,
        },
        "assigned_examinations": assigned_examinations(db, candidate),
        "consent": state["consent"],
        "device_check": state["device_check"],
        "camera_selection": state["camera_selection"],
        "camera_permission": state["camera_permission"],
        "active_session": active_session,
        "readiness": state["readiness"],
    }
