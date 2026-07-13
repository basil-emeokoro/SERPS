from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import AuditLog
from serps_pop.identity.schemas import AuditLogRead
from serps_pop.identity.services import ROLE_ADMIN, ROLE_SYSADMIN

router = APIRouter()


@router.get("/", response_model=list[AuditLogRead])
def list_audit_logs(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    stmt = select(AuditLog)
    if not current_user.has_role(ROLE_SYSADMIN):
        stmt = stmt.where(AuditLog.institution_id == current_user.institution_id)
    return list(db.scalars(stmt.order_by(AuditLog.timestamp.desc()).limit(100)).all())
