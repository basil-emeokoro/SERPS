"""Offline, one-time privileged provisioning. Never creates candidate bypasses."""
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from serps_pop.identity.models import Institution, User
from serps_pop.identity.schemas import InstitutionCreate, UserCreate
from serps_pop.identity.services import ROLE_SYSADMIN, audit, create_institution, create_user
from serps_pop.identity_assurance.models import IdentityAssuranceProfile


class BootstrapRefused(ValueError):
    pass


def provision(db: Session, *, institution_code: str, institution_name: str,
              email: str, full_name: str, password: str) -> str:
    if len(password) < 16 or password.lower().startswith(('replace-', 'password')):
        raise BootstrapRefused('Use a unique bootstrap password of at least 16 characters.')
    if db.bind.dialect.name == 'postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(736377001)'))
    if db.scalar(select(User.user_id).limit(1)) or db.scalar(select(Institution.institution_id).limit(1)):
        raise BootstrapRefused('Bootstrap requires an empty, migrated application database; no existing account is changed.')
    institution = create_institution(db, InstitutionCreate(code=institution_code,
        name=institution_name, institution_type='university'), actor_user_id=None)
    user = create_user(db, UserCreate(institution_id=institution.institution_id,
        email=email, full_name=full_name, password=password, roles=[ROLE_SYSADMIN]), actor_user_id=None)
    db.add(IdentityAssuranceProfile(user_id=user.user_id, biometric_required=False,
        demo_bypass=False, enrolment_status='not_required'))
    audit(db, action='deployment.bootstrap', result='success', institution_id=institution.institution_id,
          actor_user_id=user.user_id, target_type='user', target_id=user.user_id,
          metadata={'method': 'offline_one_time', 'candidate_bypass': False})
    db.flush()
    return user.user_id
