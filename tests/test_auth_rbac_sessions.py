from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.evidence import models as evidence_models  # noqa: F401
from serps_pop.identity import models as identity_models  # noqa: F401
from serps_pop.identity.models import AuditLog, Candidate, Examination, Institution, User
from serps_pop.identity.services import ROLE_ADMIN, ROLE_CANDIDATE, ROLE_REVIEWER, ROLE_SYSADMIN, create_institution, create_user
from serps_pop.identity.schemas import InstitutionCreate, UserCreate
from serps_pop.identity_assurance.models import IdentityAssuranceProfile
from serps_pop.infrastructure.database import Base
from serps_pop.security.tokens import create_access_token


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def seed_users(db: Session) -> dict[str, str]:
    institution = create_institution(db, InstitutionCreate(code="MIVA", name="Miva Open University"))
    other = create_institution(db, InstitutionCreate(code="WAEC", name="West African Examinations Council"))
    sysadmin = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="sysadmin@example.test",
            full_name="System Admin",
            password="Password123!",
            roles=[ROLE_SYSADMIN],
        ),
    )
    admin = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="admin@example.test",
            full_name="Admin User",
            password="Password123!",
            roles=[ROLE_ADMIN],
        ),
    )
    reviewer = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="reviewer@example.test",
            full_name="Reviewer User",
            password="Password123!",
            roles=[ROLE_REVIEWER],
        ),
    )
    candidate_user = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="candidate-user@example.test",
            full_name="Candidate User",
            password="Password123!",
            roles=[ROLE_CANDIDATE],
        ),
    )
    other_admin = create_user(
        db,
        UserCreate(
            institution_id=other.institution_id,
            email="admin@waec.example.test",
            full_name="Other Admin",
            password="Password123!",
            roles=[ROLE_ADMIN],
        ),
    )
    db.commit()
    return {
        "institution_id": institution.institution_id,
        "other_institution_id": other.institution_id,
        "sysadmin": sysadmin.email,
        "admin": admin.email,
        "reviewer": reviewer.email,
        "candidate_user": candidate_user.email,
        "other_admin": other_admin.email,
    }


def login(client: TestClient, email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_login_refresh_logout_and_me(client: TestClient, db_session: Session) -> None:
    users = seed_users(db_session)
    response = client.post("/api/v1/auth/login", json={"email": users["admin"], "password": "Password123!"})
    assert response.status_code == 200
    tokens = response.json()

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert ROLE_ADMIN in me.json()["roles"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200

    logged_out = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed.json()["refresh_token"]},
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert logged_out.status_code == 204


def test_generic_login_failure_and_audit(client: TestClient, db_session: Session) -> None:
    seed_users(db_session)
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.test", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert db_session.query(AuditLog).filter(AuditLog.action == "auth.login", AuditLog.result == "failure").count() == 1


def test_protected_request_rejects_stale_roles_institution_and_disabled_user(client: TestClient, db_session: Session) -> None:
    users = seed_users(db_session)
    admin = db_session.query(User).filter(User.email == users["admin"]).one()
    wrong_role = create_access_token(
        subject=admin.user_id,
        institution_id=admin.institution_id,
        roles=[ROLE_REVIEWER],
    )
    wrong_institution = create_access_token(
        subject=admin.user_id,
        institution_id=users["other_institution_id"],
        roles=[ROLE_ADMIN],
    )

    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_role}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_institution}"}).status_code == 401

    valid = login(client, users["admin"])
    admin.status = "disabled"
    db_session.commit()
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {valid}"}).status_code == 401


def test_candidate_cannot_access_admin_candidate_list(client: TestClient, db_session: Session) -> None:
    users = seed_users(db_session)
    token = login(client, users["candidate_user"])
    response = client.get("/api/v1/candidates/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_candidate_uniqueness_and_cross_institution_filter(client: TestClient, db_session: Session) -> None:
    users = seed_users(db_session)
    admin_token = login(client, users["admin"])
    other_token = login(client, users["other_admin"])
    payload = {
        "candidate_identifier": "10000001",
        "identifier_type": "student_id",
        "full_name": "Demo Candidate",
        "email": "candidate@miva.edu.ng",
        "matric_number": "MIVA/CSC/2026/001",
    }
    created = client.post("/api/v1/candidates/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert created.status_code == 201, created.text

    duplicate = client.post("/api/v1/candidates/", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert duplicate.status_code == 409

    own_list = client.get("/api/v1/candidates/", headers={"Authorization": f"Bearer {admin_token}"})
    other_list = client.get("/api/v1/candidates/", headers={"Authorization": f"Bearer {other_token}"})
    assert len(own_list.json()) == 1
    assert other_list.json() == []


def test_examination_assignment_session_and_invalid_transition(client: TestClient, db_session: Session) -> None:
    users = seed_users(db_session)
    admin_token = login(client, users["admin"])
    headers = {"Authorization": f"Bearer {admin_token}"}
    candidate = client.post(
        "/api/v1/candidates/",
        json={"candidate_identifier": "10000002", "full_name": "Session Candidate", "email": "session@miva.edu.ng"},
        headers=headers,
    ).json()
    exam = client.post(
        "/api/v1/examinations/",
        json={"exam_code": "CSC101", "title": "Computer Science 101", "monitoring_mode": "B"},
        headers=headers,
    ).json()
    assignment = client.post(
        "/api/v1/examinations/assignments",
        json={"candidate_id": candidate["candidate_id"], "examination_id": exam["examination_id"]},
        headers=headers,
    )
    assert assignment.status_code == 409
    candidate_record = db_session.get(Candidate, candidate["candidate_id"])
    candidate_user = create_user(db_session, UserCreate(institution_id=users["institution_id"], email="session-user@miva.edu.ng", full_name="Session Candidate", password="Password123!", roles=[ROLE_CANDIDATE]))
    candidate_record.user_id = candidate_user.user_id
    candidate_record.status = "active"
    db_session.add(IdentityAssuranceProfile(user_id=candidate_user.user_id, enrolment_status="enrolled"))
    db_session.get(Examination, exam["examination_id"]).status = "active"
    db_session.commit()
    assignment = client.post("/api/v1/examinations/assignments", json={"candidate_id": candidate["candidate_id"], "examination_id": exam["examination_id"]}, headers=headers)
    assert assignment.status_code == 201
    session = client.post(
        "/api/v1/examination-sessions/",
        json={"assignment_id": assignment.json()["assignment_id"], "deployment_mode": "B"},
        headers=headers,
    )
    assert session.status_code == 201

    invalid = client.post(
        f"/api/v1/examination-sessions/{session.json()['session_id']}/transition",
        json={"status": "active"},
        headers=headers,
    )
    assert invalid.status_code == 409

    valid = client.post(
        f"/api/v1/examination-sessions/{session.json()['session_id']}/transition",
        json={"status": "device_check_pending"},
        headers=headers,
    )
    assert valid.status_code == 200
    assert valid.json()["status"] == "device_check_pending"
