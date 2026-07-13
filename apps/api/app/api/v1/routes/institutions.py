from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import Institution
from serps_pop.identity.schemas import InstitutionCreate, InstitutionRead
from serps_pop.identity.services import DomainConflict, ROLE_SYSADMIN, create_institution

router = APIRouter()


@router.post("/", response_model=InstitutionRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: InstitutionCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> Institution:
    try:
        institution = create_institution(db, payload, actor_user_id=current_user.user_id)
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(institution)
    return institution


@router.get("/", response_model=list[InstitutionRead])
def list_institutions(
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[Institution]:
    return list(db.scalars(select(Institution).order_by(Institution.name)).all())
