from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.database import get_db
from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.main import app
from serps_pop.candidate_workflow.models import CandidateConsent
from serps_pop.governance.models import (
    AgentRecommendation,
    ContextualAssessment,
    GovernanceAuditRecord,
    PolicyEvaluation,
)
from serps_pop.identity.models import Candidate, CandidateExaminationAssignment, Examination, ExaminationSession
from serps_pop.identity.schemas import InstitutionCreate
from serps_pop.identity.services import create_institution
from serps_pop.identity.services import ROLE_ADMIN, ROLE_REVIEWER
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
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def seed_institution(db: Session, code: str = "MIVA") -> str:
    institution = create_institution(db, InstitutionCreate(code=code, name=f"{code} University"))
    db.commit()
    return institution.institution_id


def registration_payload(code: str = "MIVA", suffix: str = "1") -> dict[str, str]:
    return {
        "institution_code": code,
        "candidate_identifier": f"CAND-{suffix}",
        "full_name": f"Candidate {suffix}",
        "email": f"candidate-{suffix}@example.test",
        "password": "Password123!",
    }


def register_and_login(client: TestClient, code: str = "MIVA", suffix: str = "1") -> tuple[dict, str]:
    registered = client.post("/api/v1/candidate/register", json=registration_payload(code, suffix))
    assert registered.status_code == 201, registered.text
    login = client.post(
        "/api/v1/auth/login",
        json={"institution_code": code, "email": f"candidate-{suffix}@example.test", "password": "Password123!"},
    )
    assert login.status_code == 200, login.text
    return registered.json(), login.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assign_exam(db: Session, candidate: dict, code: str = "CSC101") -> Examination:
    exam = Examination(
        institution_id=candidate["institution_id"],
        exam_code=code,
        title="Operational Examination",
        status="published",
        duration_minutes=60,
    )
    db.add(exam)
    db.flush()
    db.add(
        CandidateExaminationAssignment(
            institution_id=candidate["institution_id"],
            candidate_id=candidate["candidate_id"],
            examination_id=exam.examination_id,
            status="eligible",
        )
    )
    db.commit()
    return exam


def complete_preflight(client: TestClient, token: str) -> None:
    headers = auth(token)
    consent = client.post(
        "/api/v1/candidate/consents",
        headers=headers,
        json={
            "consent_version": "CONSENT-1.0",
            "monitoring_consent": True,
            "privacy_notice_accepted": True,
            "institutional_policy_accepted": True,
        },
    )
    assert consent.status_code == 201, consent.text
    device = client.post(
        "/api/v1/candidate/device-checks",
        headers=headers,
        json={
            "supported_browser": True,
            "secure_context": True,
            "camera_available": True,
            "microphone_available": True,
            "browser_name": "Chrome",
            "browser_version": "126",
            "operating_system": "Test OS",
            "user_agent": "pytest-browser",
        },
    )
    assert device.status_code == 201 and device.json()["passed"] is True
    camera = client.post(
        "/api/v1/candidate/cameras",
        headers=headers,
        json={"camera_role": "primary", "device_id": "primary-browser-device", "label": "Integrated Camera", "camera_count": 2},
    )
    assert camera.status_code == 201, camera.text
    permission = client.post(
        "/api/v1/candidate/camera-permissions",
        headers=headers,
        json={"camera_role": "primary", "status": "granted", "user_agent": "pytest-browser"},
    )
    assert permission.status_code == 201 and permission.json()["granted"] is True
    secondary = client.post(
        "/api/v1/candidate/cameras",
        headers=headers,
        json={"camera_role": "secondary", "device_id": "secondary-browser-device", "label": "Room Camera", "camera_count": 2},
    )
    assert secondary.status_code == 201, secondary.text
    secondary_permission = client.post(
        "/api/v1/candidate/camera-permissions",
        headers=headers,
        json={"camera_role": "secondary", "status": "granted", "user_agent": "pytest-browser"},
    )
    assert secondary_permission.status_code == 201 and secondary_permission.json()["granted"] is True


def test_registration_authentication_and_institution_validation(client: TestClient, db: Session):
    seed_institution(db)
    registered, token = register_and_login(client)
    stored = db.get(Candidate, registered["candidate_id"])
    assert stored.user_id == registered["user_id"]
    assert client.get("/api/v1/candidate/dashboard", headers=auth(token)).status_code == 200
    invalid = client.post("/api/v1/candidate/register", json=registration_payload("UNKNOWN", "2"))
    assert invalid.status_code == 404


def test_assigned_examinations_are_candidate_scoped(client: TestClient, db: Session):
    seed_institution(db)
    first, first_token = register_and_login(client, suffix="1")
    _, second_token = register_and_login(client, suffix="2")
    exam = assign_exam(db, first)
    first_response = client.get("/api/v1/candidate/examinations", headers=auth(first_token))
    second_response = client.get("/api/v1/candidate/examinations", headers=auth(second_token))
    assert [item["examination_id"] for item in first_response.json()] == [exam.examination_id]
    assert second_response.json() == []


def test_consent_is_explicit_versioned_and_immutable(client: TestClient, db: Session):
    seed_institution(db)
    _, token = register_and_login(client)
    response = client.post(
        "/api/v1/candidate/consents",
        headers=auth(token),
        json={
            "consent_version": "CONSENT-1.0",
            "monitoring_consent": True,
            "privacy_notice_accepted": True,
            "institutional_policy_accepted": False,
        },
    )
    assert response.status_code == 201 and response.json()["accepted"] is False
    accepted = client.post(
        "/api/v1/candidate/consents",
        headers=auth(token),
        json={
            "consent_version": "CONSENT-1.0",
            "monitoring_consent": True,
            "privacy_notice_accepted": True,
            "institutional_policy_accepted": True,
        },
    )
    assert accepted.status_code == 201 and accepted.json()["accepted"] is True
    assert len(client.get("/api/v1/candidate/consents", headers=auth(token)).json()) == 2
    record = db.get(CandidateConsent, accepted.json()["consent_id"])
    record.accepted = False
    with pytest.raises(ValueError, match="append-only"):
        db.flush()
    db.rollback()


def test_start_rejects_consent_and_camera_bypass(client: TestClient, db: Session):
    seed_institution(db)
    candidate, token = register_and_login(client)
    exam = assign_exam(db, candidate)
    start = f"/api/v1/candidate/examinations/{exam.examination_id}/start"
    assert client.post(start, headers=auth(token), json={}).status_code == 409
    client.post(
        "/api/v1/candidate/consents",
        headers=auth(token),
        json={"monitoring_consent": True, "privacy_notice_accepted": True, "institutional_policy_accepted": True},
    )
    client.post(
        "/api/v1/candidate/device-checks",
        headers=auth(token),
        json={
            "supported_browser": True, "secure_context": True, "camera_available": True,
            "microphone_available": True, "browser_name": "Chrome",
        },
    )
    client.post(
        "/api/v1/candidate/cameras",
        headers=auth(token),
        json={"camera_role": "primary", "device_id": "camera", "camera_count": 2},
    )
    client.post(
        "/api/v1/candidate/camera-permissions", headers=auth(token), json={"camera_role": "primary", "status": "denied"}
    )
    denied = client.post(start, headers=auth(token), json={})
    assert denied.status_code == 409
    assert "primary_camera_permission_granted" in denied.json()["detail"]


def test_device_and_permission_attestations_are_bounded_and_candidate_owned(client: TestClient, db: Session):
    institution_id = seed_institution(db)
    first, first_token = register_and_login(client, suffix="1")
    second, second_token = register_and_login(client, suffix="2")
    payload = {
        "supported_browser": True,
        "secure_context": True,
        "camera_available": True,
        "microphone_available": True,
        "browser_name": "Chrome",
        "browser_version": "126",
        "operating_system": "Test OS",
        "user_agent": "pytest-browser",
    }

    recorded = client.post("/api/v1/candidate/device-checks", headers=auth(first_token), json=payload)
    assert recorded.status_code == 201
    assert recorded.json()["candidate_id"] == first["candidate_id"]
    assert recorded.json()["institution_id"] == institution_id
    assert recorded.json()["metadata_json"]["trust_boundary"] == "client_reported"
    assert recorded.json()["metadata_json"]["attestation_status"] == "passed"
    assert recorded.json()["metadata_json"]["server_received_at"]

    forbidden_identity = client.post(
        "/api/v1/candidate/device-checks",
        headers=auth(second_token),
        json={**payload, "candidate_id": first["candidate_id"]},
    )
    assert forbidden_identity.status_code == 422
    assert client.post(
        "/api/v1/candidate/device-checks",
        headers=auth(second_token),
        json={**payload, "attestation_source": "reviewer_console"},
    ).status_code == 422

    permission = client.post(
        "/api/v1/candidate/camera-permissions",
        headers=auth(first_token),
        json={"camera_role": "primary", "status": "granted", "user_agent": "pytest-browser"},
    )
    assert permission.status_code == 201
    assert permission.json()["metadata_json"]["attestation_source"] == "candidate_browser"
    assert permission.json()["metadata_json"]["attestation_status"] == "granted"
    assert permission.json()["metadata_json"]["browser_context"]["user_agent"] == "pytest-browser"
    assert client.post(
        "/api/v1/candidate/camera-permissions",
        headers=auth(first_token),
        json={"camera_role": "primary", "status": "verified_by_server"},
    ).status_code == 422

    assert second["institution_id"] == institution_id


def test_session_creation_links_preflight_and_dashboard(client: TestClient, db: Session):
    seed_institution(db)
    candidate, token = register_and_login(client)
    exam = assign_exam(db, candidate)
    complete_preflight(client, token)
    dashboard = client.get("/api/v1/candidate/dashboard", headers=auth(token))
    assert dashboard.status_code == 200 and dashboard.json()["readiness"]["ready_to_start"] is True
    started = client.post(
        f"/api/v1/candidate/examinations/{exam.examination_id}/start", headers=auth(token), json={}
    )
    assert started.status_code == 201, started.text
    body = started.json()
    assert body["status"] == "active"
    assert all(body[field] for field in ("consent_id", "device_check_id", "camera_selection_id", "camera_permission_id", "secondary_camera_selection_id", "secondary_camera_permission_id"))


def test_duplicate_dual_camera_selection_is_rejected(client: TestClient, db: Session):
    seed_institution(db)
    _, token = register_and_login(client)
    primary = client.post(
        "/api/v1/candidate/cameras", headers=auth(token),
        json={"camera_role": "primary", "device_id": "same-device", "camera_count": 2},
    )
    assert primary.status_code == 201
    duplicate = client.post(
        "/api/v1/candidate/cameras", headers=auth(token),
        json={"camera_role": "secondary", "device_id": "same-device", "camera_count": 2},
    )
    assert duplicate.status_code == 409
    assert "distinct devices" in duplicate.json()["detail"]


def test_candidate_workspace_ownership_and_completion(client: TestClient, db: Session):
    seed_institution(db)
    first, first_token = register_and_login(client, suffix="1")
    _, second_token = register_and_login(client, suffix="2")
    exam = assign_exam(db, first)
    complete_preflight(client, first_token)
    session = client.post(
        f"/api/v1/candidate/examinations/{exam.examination_id}/start", headers=auth(first_token), json={}
    ).json()
    own = client.get(f"/api/v1/candidate/sessions/{session['session_id']}", headers=auth(first_token))
    assert own.status_code == 200
    assert own.json()["primary_camera"]["camera_role"] == "primary"
    assert own.json()["secondary_camera"]["camera_role"] == "secondary"
    assert client.get(f"/api/v1/candidate/sessions/{session['session_id']}", headers=auth(second_token)).status_code == 403
    completed = client.post(f"/api/v1/candidate/sessions/{session['session_id']}/complete", headers=auth(first_token))
    assert completed.status_code == 200 and completed.json()["status"] == "completed"


def test_real_event_ingestion_triggers_governance_chain(client: TestClient, db: Session):
    seed_institution(db)
    candidate, token = register_and_login(client)
    exam = assign_exam(db, candidate)
    complete_preflight(client, token)
    session = client.post(
        f"/api/v1/candidate/examinations/{exam.examination_id}/start", headers=auth(token), json={}
    ).json()
    event = client.post(
        "/api/v1/evidence-events/",
        headers=auth(token),
        json={
            "session_id": session["session_id"],
            "candidate_id": candidate["candidate_id"],
            "source_module": "candidate_browser",
            "event_type": "TAB_FOCUS_LOST",
            "risk_weight": 0.3,
            "confidence": 1.0,
            "description": "Browser visibility API reported a hidden examination tab.",
        },
    )
    assert event.status_code == 201, event.text
    assessment = db.scalar(select(ContextualAssessment).where(ContextualAssessment.session_id == session["session_id"]))
    recommendation = db.scalar(select(AgentRecommendation).where(AgentRecommendation.assessment_id == assessment.assessment_id))
    evaluation = db.scalar(select(PolicyEvaluation).where(PolicyEvaluation.recommendation_id == recommendation.recommendation_id))
    assert assessment.evidence_event_ids == [event.json()["event_id"]]
    assert recommendation.recommended_action == "CONTINUE_MONITORING"
    assert evaluation.continue_examination is True
    actions = set(db.scalars(select(GovernanceAuditRecord.action)).all())
    assert {"CONTEXTUAL_ASSESSMENT_CREATED", "AGENT_RECOMMENDATION_CREATED", "POLICY_EVALUATION_CREATED"} <= actions


def test_candidate_cannot_spoof_another_session(client: TestClient, db: Session):
    seed_institution(db)
    first, first_token = register_and_login(client, suffix="1")
    second, second_token = register_and_login(client, suffix="2")
    exam = assign_exam(db, first)
    complete_preflight(client, first_token)
    session = client.post(
        f"/api/v1/candidate/examinations/{exam.examination_id}/start", headers=auth(first_token), json={}
    ).json()
    spoof = client.post(
        "/api/v1/evidence-events/",
        headers=auth(second_token),
        json={
            "session_id": session["session_id"], "candidate_id": second["candidate_id"],
            "source_module": "candidate_browser", "event_type": "CAMERA_CONNECTED",
            "risk_weight": 0.1, "confidence": 1.0, "description": "Spoof attempt",
        },
    )
    assert spoof.status_code == 403
    assert db.scalar(select(ExaminationSession).where(ExaminationSession.session_id == session["session_id"]))


def test_reviewer_and_admin_operational_views_are_scoped_and_dual_camera_aware(client: TestClient, db: Session):
    institution_id = seed_institution(db)
    candidate, token = register_and_login(client)
    exam = assign_exam(db, candidate)
    complete_preflight(client, token)
    session = client.post(
        f"/api/v1/candidate/examinations/{exam.examination_id}/start", headers=auth(token), json={}
    ).json()
    for role in ("primary", "secondary"):
        event = client.post(
            "/api/v1/evidence-events/", headers=auth(token),
            json={
                "session_id": session["session_id"], "candidate_id": candidate["candidate_id"],
                "source_module": "candidate_browser", "event_type": "CAMERA_CONNECTED",
                "camera_id": role, "risk_weight": 0.1, "confidence": 1.0,
                "description": f"{role} camera connected",
            },
        )
        assert event.status_code == 201, event.text

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="REVIEWER", institution_id=institution_id, roles=(ROLE_REVIEWER,)
    )
    queue = client.get("/api/v1/reviewer/sessions")
    assert queue.status_code == 200
    assert queue.json()[0]["primary_camera_status"] == "connected"
    assert queue.json()[0]["secondary_camera_status"] == "connected"
    detail = client.get(f"/api/v1/reviewer/sessions/{session['session_id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["primary_camera"]["stream_mode"] == "metadata_only"
    assert detail.json()["secondary_camera"]["connection_status"] == "connected"

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="ADMIN", institution_id=institution_id, roles=(ROLE_ADMIN,)
    )
    metrics = client.get("/api/v1/admin/metrics")
    assert metrics.status_code == 200, metrics.text
    assert metrics.json()["active_sessions"] == 1
    assert metrics.json()["connected_primary_cameras"] == 1
    assert metrics.json()["connected_secondary_cameras"] == 1
    assert client.get(f"/api/v1/admin/sessions/{session['session_id']}").status_code == 200

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="OTHER", institution_id="OTHER-INSTITUTION", roles=(ROLE_ADMIN,)
    )
    assert client.get(f"/api/v1/admin/sessions/{session['session_id']}").status_code == 403
    app.dependency_overrides.pop(get_current_user, None)
