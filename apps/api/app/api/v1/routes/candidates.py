from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, get_current_user, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import Candidate
from serps_pop.identity.schemas import CandidateCreate, CandidateRead, CandidateUpdate
from serps_pop.identity.services import (
    DomainConflict,
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_REVIEWER,
    ROLE_SYSADMIN,
    create_candidate,
    update_candidate,
)

router = APIRouter()


@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: CandidateCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> Candidate:
    institution_id = payload.institution_id if current_user.has_role(ROLE_SYSADMIN) and payload.institution_id else current_user.institution_id
    try:
        candidate = create_candidate(db, payload, institution_id=institution_id, actor_user_id=current_user.user_id)
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/", response_model=list[CandidateRead])
def list_candidates(
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN, ROLE_REVIEWER)),
    db: Session = Depends(get_db),
) -> list[Candidate]:
    stmt = select(Candidate)
    if not current_user.has_role(ROLE_SYSADMIN):
        stmt = stmt.where(Candidate.institution_id == current_user.institution_id)
    if status_filter:
        stmt = stmt.where(Candidate.status == status_filter)
    return list(db.scalars(stmt.order_by(Candidate.full_name)).all())


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(
    candidate_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    if not current_user.has_role(ROLE_SYSADMIN) and candidate.institution_id != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    if current_user.has_role(ROLE_CANDIDATE) and not current_user.has_role(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Candidate self-profile binding is pending.")
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateRead)
def patch_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    if not current_user.has_role(ROLE_SYSADMIN) and candidate.institution_id != current_user.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    try:
        candidate = update_candidate(db, candidate, payload, actor_user_id=current_user.user_id)
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(candidate)
    return candidate
