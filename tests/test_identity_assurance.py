from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.identity.schemas import InstitutionCreate, UserCreate
from serps_pop.identity.services import ROLE_CANDIDATE, ROLE_SYSADMIN, create_institution, create_user
from serps_pop.identity_assurance.services import _validate_actions, create_demo_profile
from serps_pop.identity.services import DomainConflict
from serps_pop.infrastructure.database import Base


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = local_session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield db

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def seed(db: Session):
    institution = create_institution(db, InstitutionCreate(code="MIVA", name="Miva Open University"))
    institution.metadata_json = {"registration_configuration": {"version": "1.0", "enabled": True, "candidate_identifier_field": "matriculation_number", "fields": [
        {"name": "matriculation_number", "label": "Matriculation number", "type": "text", "required": True, "pattern": r"[A-Z0-9-]{4,20}", "active": True, "applies_to": ["candidate"]},
        {"name": "full_name", "label": "Full name", "type": "text", "required": True, "active": True, "applies_to": ["candidate", "reviewer", "administrator"]},
        {"name": "contact_email", "label": "Contact email", "type": "email", "required": True, "active": True, "applies_to": ["candidate", "reviewer", "administrator"]},
    ]}}
    sysadmin = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="sysadmin@example.test",
            full_name="System Administrator",
            password="Password123!",
            roles=[ROLE_SYSADMIN],
        ),
    )
    db.commit()
    return institution, sysadmin


def candidate_registration(email: str = "biometric@example.test") -> dict:
    return {
        "institution_code": "MIVA",
        "account_type": "candidate",
        "candidate_identifier": "BIO-001",
        "full_name": "Biometric Candidate",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "biometric_consent": True,
        "configuration_version": "1.0",
        "configured_fields": {"matriculation_number": "BIO-001", "full_name": "Biometric Candidate", "contact_email": email},
    }


def test_public_institution_configuration_and_server_validation(client: TestClient, db: Session):
    seed(db)
    listed = client.get("/api/v1/identity-assurance/institutions")
    assert listed.status_code == 200
    assert listed.json()[0]["code"] == "MIVA"
    assert {item["name"] for item in listed.json()[0]["fields"]} == {"matriculation_number", "full_name", "contact_email"}

    unknown_field = candidate_registration("unknown@example.test")
    unknown_field["configured_fields"]["injected"] = "unsafe"
    response = client.post("/api/v1/identity-assurance/registrations", json=unknown_field)
    assert response.status_code == 409
    assert "Unknown configured registration field" in response.json()["detail"]

    stale = candidate_registration("stale@example.test")
    stale["configuration_version"] = "0.9"
    response = client.post("/api/v1/identity-assurance/registrations", json=stale)
    assert response.status_code == 409
    assert "configuration changed" in response.json()["detail"].lower()


def captures() -> list[dict]:
    return [
        {
            "pose": pose,
            "descriptor": [0.5] * 64,
            "one_face": True,
            "pose_validated": True,
            "lighting_score": 0.9,
            "distance_score": 0.9,
            "confidence": 0.9,
        }
        for pose in ("forward", "left", "right", "up", "down", "centre_confirmation")
    ]


def liveness(actions: list[str]) -> list[dict]:
    started = datetime.now(timezone.utc)
    return [
        {"action": action, "completed": True, "confidence": 0.9, "timestamp": (started + timedelta(seconds=index * 0.6)).isoformat()}
        for index, action in enumerate(actions)
    ]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_static_or_rapid_liveness_sequence_is_rejected():
    timestamp = datetime.now(timezone.utc)
    submitted = [SimpleNamespace(action=action, completed=True, confidence=.9, timestamp=timestamp) for action in ["turn_left", "turn_right", "return_to_centre"]]
    with pytest.raises(DomainConflict, match="too quickly"):
        _validate_actions(["turn_left", "turn_right", "return_to_centre"], submitted)


def test_candidate_registration_enrollment_password_face_and_periodic_flow(client: TestClient, db: Session):
    seed(db)
    registration = client.post("/api/v1/identity-assurance/registrations", json=candidate_registration())
    assert registration.status_code == 201, registration.text
    registered = registration.json()
    assert registered["status"] == "pending_facial_enrolment"
    assert registered["prototype_verified"] is True
    assert len(registered["required_actions"]) == 3

    missing_enrolment = client.post(
        "/api/v1/auth/login",
        json={"institution_code": "MIVA", "email": "biometric@example.test", "password": "Password123!"},
    )
    assert missing_enrolment.status_code == 200
    assert missing_enrolment.json()["authentication_stage"] == "enrollment_required"
    assert missing_enrolment.json()["capture_restart_required"] is True
    assert len(missing_enrolment.json()["required_actions"]) == 3

    resumed = client.post(
        "/api/v1/identity-assurance/enrollments/resume",
        json={"institution_code": "miva", "email": "biometric@example.test", "password": "Password123!"},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["purpose"] == "enrollment"
    assert len(resumed.json()["required_actions"]) == 3
    registered["enrollment_token"] = resumed.json()["challenge_token"]
    registered["required_actions"] = resumed.json()["required_actions"]

    invalid_resume = client.post(
        "/api/v1/identity-assurance/enrollments/resume",
        json={"institution_code": "MIVA", "email": "biometric@example.test", "password": "WrongPassword!"},
    )
    assert invalid_resume.status_code == 404

    enrolled = client.post(
        "/api/v1/identity-assurance/enrollments",
        json={
            "enrollment_token": registered["enrollment_token"],
            "captures": captures(),
            "liveness_actions": liveness(registered["required_actions"]),
            "retry_count": 0,
        },
    )
    assert enrolled.status_code == 201, enrolled.text
    assert enrolled.json()["capture_count"] == 6
    assert enrolled.json()["raw_media_stored"] is False

    duplicate = client.post(
        "/api/v1/identity-assurance/enrollments",
        json={
            "enrollment_token": registered["enrollment_token"],
            "captures": captures(),
            "liveness_actions": liveness(registered["required_actions"]),
            "retry_count": 0,
        },
    )
    assert duplicate.status_code in (404, 409)

    password_stage = client.post(
        "/api/v1/auth/login",
        json={"institution_code": "MIVA", "email": "biometric@example.test", "password": "Password123!"},
    )
    assert password_stage.status_code == 200, password_stage.text
    challenge = password_stage.json()
    assert challenge["authentication_stage"] == "facial_required"

    retry_required = client.post(
        "/api/v1/identity-assurance/facial-authentication",
        json={
            "challenge_token": challenge["challenge_token"],
            "descriptor": [0.5] * 64,
            "one_face": False,
            "lighting_score": 0.2,
            "distance_score": 0.2,
            "liveness_actions": liveness(challenge["required_actions"]),
            "retry_count": 1,
        },
    )
    assert retry_required.status_code == 200
    assert retry_required.json()["outcome"] == "Retry Required"

    verified = client.post(
        "/api/v1/identity-assurance/facial-authentication",
        json={
            "challenge_token": challenge["challenge_token"],
            "descriptor": [0.5] * 64,
            "one_face": True,
            "lighting_score": 0.9,
            "distance_score": 0.9,
            "liveness_actions": liveness(challenge["required_actions"]),
            "retry_count": 1,
        },
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["outcome"] == "Verified"
    access_token = verified.json()["access_token"]

    periodic = client.post("/api/v1/identity-assurance/periodic/challenge", headers=auth(access_token))
    assert periodic.status_code == 200, periodic.text
    periodic_result = client.post(
        "/api/v1/identity-assurance/periodic/verify",
        headers=auth(access_token),
        json={
            "challenge_token": periodic.json()["challenge_token"],
            "descriptor": [0.5] * 64,
            "one_face": True,
            "lighting_score": 0.9,
            "distance_score": 0.9,
            "liveness_actions": liveness(periodic.json()["required_actions"]),
            "retry_count": 0,
        },
    )
    assert periodic_result.status_code == 200, periodic_result.text
    assert periodic_result.json()["outcome"] == "Verified"


def test_registration_approval_and_demo_bypass(client: TestClient, db: Session):
    institution, sysadmin = seed(db)
    login = client.post("/api/v1/auth/login", json={"email": sysadmin.email, "password": "Password123!"})
    token = login.json()["access_token"]
    request = client.post(
        "/api/v1/identity-assurance/registrations",
        json={
            "institution_code": "MIVA",
            "account_type": "reviewer",
            "full_name": "Institution Reviewer",
            "email": "reviewer-request@example.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
                "biometric_consent": False,
                "configuration_version": "1.0",
                "configured_fields": {"full_name": "Institution Reviewer", "contact_email": "reviewer-request@example.test"},
        },
    )
    assert request.status_code == 201
    assert request.json()["status"] == "pending_approval"
    approved = client.post(
        f"/api/v1/identity-assurance/registrations/{request.json()['registration_id']}/decision",
        headers=auth(token),
        json={"decision": "approve", "rationale": "Institutional reviewer appointment confirmed."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"

    demo = create_user(
        db,
        UserCreate(
            institution_id=institution.institution_id,
            email="demo-candidate@example.test",
            full_name="Demo Candidate",
            password="Password123!",
            roles=[ROLE_CANDIDATE],
        ),
    )
    create_demo_profile(db, demo.user_id)
    db.commit()
    bypass = client.post("/api/v1/auth/login", json={"email": demo.email, "password": "Password123!"})
    assert bypass.status_code == 200
    assert bypass.json()["authentication_stage"] == "complete"
    assert "access_token" in bypass.json()
