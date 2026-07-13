from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import User, UserRole
from serps_pop.identity.schemas import UserCreate, UserRead
from serps_pop.identity.services import DomainConflict, DomainNotFound, ROLE_SYSADMIN, create_user, user_roles

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: UserCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> UserRead:
    try:
        user = create_user(db, payload, actor_user_id=current_user.user_id)
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    db.commit()
    db.refresh(user)
    return UserRead(
        user_id=user.user_id,
        institution_id=user.institution_id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        roles=user_roles(user),
    )


@router.get("/", response_model=list[UserRead])
def list_users(
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    users = db.scalars(select(User).options(selectinload(User.roles).selectinload(UserRole.role))).all()
    return [
        UserRead(
            user_id=user.user_id,
            institution_id=user.institution_id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            roles=user_roles(user),
        )
        for user in users
    ]
