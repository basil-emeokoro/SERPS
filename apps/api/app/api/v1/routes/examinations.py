from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import Examination
from serps_pop.identity.schemas import AssignmentCreate, AssignmentRead, ExaminationCreate, ExaminationRead
from serps_pop.identity.services import (
    DomainConflict,
    DomainNotFound,
    ROLE_ADMIN,
    ROLE_REVIEWER,
    ROLE_SYSADMIN,
    create_assignment,
    create_examination,
)

router = APIRouter()


@router.post("/", response_model=ExaminationRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: ExaminationCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> Examination:
    institution_id = payload.institution_id if current_user.has_role(ROLE_SYSADMIN) and payload.institution_id else current_user.institution_id
    try:
        exam = create_examination(db, payload, institution_id=institution_id, actor_user_id=current_user.user_id)
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(exam)
    return exam


@router.get("/", response_model=list[ExaminationRead])
def list_exams(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[Examination]:
    stmt = select(Examination)
    if not current_user.has_role(ROLE_SYSADMIN):
        stmt = stmt.where(Examination.institution_id == current_user.institution_id)
    return list(db.scalars(stmt.order_by(Examination.created_at.desc())).all())


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_candidate(
    payload: AssignmentCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
):
    try:
        assignment = create_assignment(
            db,
            candidate_id=payload.candidate_id,
            examination_id=payload.examination_id,
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
    db.refresh(assignment)
    return assignment
