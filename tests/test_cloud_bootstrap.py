from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from apps.api.app.main import app
from apps.api.app.api.deps.database import get_db
from serps_pop.infrastructure.database import Base
from serps_pop.identity.models import User, Institution, Candidate, ExaminationSession, AuditLog
from serps_pop.identity_assurance.models import IdentityAssuranceProfile
from serps_pop.identity.services import user_roles, ROLE_SYSADMIN
from serps_pop.operations.bootstrap import provision, BootstrapRefused
from serps_pop.config.settings import Settings


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def inputs():
    return dict(institution_code='STAGE', institution_name='Staging Fixture', email='operator@example.test',
                full_name='Staging Operator', password='test-only-bootstrap-password-123')


def test_bootstrap_is_audited_staff_only_and_non_repeatable(db):
    uid = provision(db, **inputs()); db.commit()
    user = db.get(User, uid); password_hash = user.password_hash
    assert user_roles(user) == [ROLE_SYSADMIN]
    profile = db.scalar(select(IdentityAssuranceProfile))
    assert not profile.demo_bypass and not profile.biometric_required
    assert profile.enrolment_status == 'not_required'
    assert db.scalar(select(func.count()).select_from(Candidate)) == 0
    assert db.scalar(select(func.count()).select_from(ExaminationSession)) == 0
    assert db.scalar(select(AuditLog).where(AuditLog.action == 'deployment.bootstrap')) is not None
    with pytest.raises(BootstrapRefused):
        provision(db, **inputs())
    db.rollback()
    assert db.get(User, uid).password_hash == password_hash


def test_weak_password_does_not_create_institution(db):
    with pytest.raises(BootstrapRefused):
        provision(db, **{**inputs(), 'password': 'short'})
    assert db.scalar(select(func.count()).select_from(Institution)) == 0


def test_bootstrap_login_and_rejected_login(db):
    provision(db, **inputs()); db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            payload = {'email': inputs()['email'], 'password': inputs()['password'], 'institution_code': 'STAGE'}
            response = client.post('/api/v1/auth/login', json=payload)
            assert response.status_code == 200
            assert response.json()['authentication_stage'] == 'complete'
            assert client.post('/api/v1/auth/login', json={**payload, 'password':'invalid-password'}).status_code == 401
            assert client.get('/api/v1/ready').status_code == 503
            db.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(64) NOT NULL)'))
            db.execute(text("INSERT INTO alembic_version VALUES ('0009_exam_management_courses')")); db.commit()
            assert client.get('/api/v1/ready').status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize('change', [dict(jwt_secret='short'),dict(demo_policy_controls=True),
    dict(cors_origins='https://*.example.test'),dict(cors_origins='http://public.example.test'),dict(database_url='sqlite:///native.db')])
def test_hosted_configuration_rejects_unsafe_values(change):
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{**dict(env='staging', jwt_secret='test-only-secret-of-at-least-32-characters',
            database_url='postgresql+psycopg://fixture@db/fixture',cors_origins='https://staging.example.test'),**change})
