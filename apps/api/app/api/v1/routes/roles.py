from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import Role
from serps_pop.identity.schemas import RoleRead
from serps_pop.identity.services import ROLE_SYSADMIN, ensure_roles

router = APIRouter()


@router.get("/", response_model=list[RoleRead])
def list_roles(
    current_user: CurrentUser = Depends(require_roles(ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[Role]:
    ensure_roles(db)
    db.commit()
    return list(db.scalars(select(Role).order_by(Role.name)).all())
