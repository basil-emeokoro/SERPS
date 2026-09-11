from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.candidate_workflow.models import CandidateConsent, DeviceCheckRecord
from serps_pop.candidate_workflow.schemas import (
    AssignedExaminationRead,
    CameraPermissionCreate,
    CameraPermissionRead,
    CameraSelectionCreate,
    CameraSelectionRead,
    CandidateDashboardRead,
    CandidateRegistrationCreate,
    CandidateRegistrationRead,
    CandidateSessionRead,
    CandidateSessionStart,
    CandidateWorkspaceRead,
    CandidateProtectionRead,
    ConsentCreate,
    ConsentRead,
    DeviceCheckCreate,
    DeviceCheckRead,
)
from serps_pop.candidate_workflow.services import (
    CandidatePrerequisiteMissing,
    CandidateAccessDenied,
    assigned_examinations,
    candidate_dashboard,
    candidate_for_user,
    candidate_workspace,
    candidate_protection_state,
    complete_candidate_session,
    record_camera_permission,
    record_camera_selection,
    record_consent,
    record_device_check,
    register_candidate,
    start_examination_session,
)
from serps_pop.identity.services import DomainConflict, DomainNotFound, ROLE_CANDIDATE

router = APIRouter()


def _candidate(db: Session, current_user: CurrentUser):
    try:
        return candidate_for_user(db, current_user.user_id, current_user.institution_id)
    except DomainNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/register", response_model=CandidateRegistrationRead, status_code=status.HTTP_201_CREATED)
def register(payload: CandidateRegistrationCreate, db: Session = Depends(get_db)) -> object:
    try:
        candidate = register_candidate(db, payload)
        db.commit()
        db.refresh(candidate)
        return candidate
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DomainConflict, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/examinations", response_model=list[AssignedExaminationRead])
def examinations(
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> list[dict]:
    return assigned_examinations(db, _candidate(db, current_user))


@router.get("/dashboard", response_model=CandidateDashboardRead)
def dashboard(
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> dict:
    return candidate_dashboard(db, _candidate(db, current_user))


@router.post("/consents", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
def create_consent(
    payload: ConsentCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    candidate = _candidate(db, current_user)
    record = record_consent(
        db,
        candidate=candidate,
        user_id=current_user.user_id,
        payload=payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/consents", response_model=list[ConsentRead])
def list_consents(
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> list[CandidateConsent]:
    candidate = _candidate(db, current_user)
    return list(
        db.scalars(
            select(CandidateConsent)
            .where(CandidateConsent.candidate_id == candidate.candidate_id)
            .order_by(CandidateConsent.accepted_at.asc())
        ).all()
    )


@router.post("/device-checks", response_model=DeviceCheckRead, status_code=status.HTTP_201_CREATED)
def create_device_check(
    payload: DeviceCheckCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    record = record_device_check(
        db, candidate=_candidate(db, current_user), user_id=current_user.user_id, payload=payload
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/device-checks", response_model=list[DeviceCheckRead])
def list_device_checks(
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> list[DeviceCheckRecord]:
    candidate = _candidate(db, current_user)
    return list(
        db.scalars(
            select(DeviceCheckRecord)
            .where(DeviceCheckRecord.candidate_id == candidate.candidate_id)
            .order_by(DeviceCheckRecord.checked_at.asc())
        ).all()
    )


@router.post("/cameras", response_model=CameraSelectionRead, status_code=status.HTTP_201_CREATED)
def select_camera(
    payload: CameraSelectionCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    try:
        record = record_camera_selection(
            db, candidate=_candidate(db, current_user), user_id=current_user.user_id, payload=payload
        )
    except CandidatePrerequisiteMissing as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    db.refresh(record)
    return record


@router.post("/camera-permissions", response_model=CameraPermissionRead, status_code=status.HTTP_201_CREATED)
def camera_permission(
    payload: CameraPermissionCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    record = record_camera_permission(
        db, candidate=_candidate(db, current_user), user_id=current_user.user_id, payload=payload
    )
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/examinations/{examination_id}/start",
    response_model=CandidateSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def start_session(
    examination_id: str,
    payload: CandidateSessionStart,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    try:
        session = start_examination_session(
            db,
            candidate=_candidate(db, current_user),
            examination_id=examination_id,
            user_id=current_user.user_id,
            deployment_mode=payload.deployment_mode,
        )
        db.commit()
        db.refresh(session)
        return session
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DomainConflict, CandidatePrerequisiteMissing) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_model=CandidateWorkspaceRead)
def get_workspace(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return candidate_workspace(db, _candidate(db, current_user), session_id)
    except DomainNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except CandidatePrerequisiteMissing as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/protection", response_model=CandidateProtectionRead)
def get_protection_state(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return candidate_protection_state(db, _candidate(db, current_user), session_id)
    except DomainNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/complete", response_model=CandidateSessionRead)
def complete_session(
    session_id: str,
    current_user: CurrentUser = Depends(require_roles(ROLE_CANDIDATE)),
    db: Session = Depends(get_db),
) -> object:
    try:
        session = complete_candidate_session(
            db, _candidate(db, current_user), session_id, current_user.user_id
        )
        db.commit()
        db.refresh(session)
        return session
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateAccessDenied as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (DomainConflict, CandidatePrerequisiteMissing) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
