from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.identity.models import CandidateExaminationAssignment, Examination
from serps_pop.identity.schemas import InstitutionCreate, UserCreate
from serps_pop.identity.services import ROLE_ADMIN, ROLE_REVIEWER, create_institution, create_user
from serps_pop.infrastructure.database import Base


@pytest.fixture()
def e2e_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = local_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def e2e_client(e2e_db: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield e2e_db

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"institution_code": "MIVA", "email": email, "password": "Password123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_complete_operational_workflow(e2e_client: TestClient, e2e_db: Session) -> None:
    institution = create_institution(e2e_db, InstitutionCreate(code="MIVA", name="Miva Open University"))
    create_user(
        e2e_db,
        UserCreate(
            institution_id=institution.institution_id,
            email="reviewer@example.test",
            full_name="Research Reviewer",
            password="Password123!",
            roles=[ROLE_REVIEWER],
        ),
        actor_user_id=None,
    )
    create_user(
        e2e_db,
        UserCreate(
            institution_id=institution.institution_id,
            email="admin@example.test",
            full_name="Research Administrator",
            password="Password123!",
            roles=[ROLE_ADMIN],
        ),
        actor_user_id=None,
    )
    e2e_db.commit()

    registration = e2e_client.post(
        "/api/v1/candidate/register",
        json={
            "institution_code": "MIVA",
            "candidate_identifier": "RC1-CANDIDATE",
            "full_name": "RC1 Candidate",
            "email": "candidate@example.test",
            "password": "Password123!",
        },
    )
    assert registration.status_code == 201, registration.text
    candidate = registration.json()
    candidate_token = _login(e2e_client, "candidate@example.test")
    candidate_headers = _auth(candidate_token)

    examination = Examination(
        institution_id=institution.institution_id,
        exam_code="RC1-DEMO",
        title="SERPS RC1 Demonstration",
        status="published",
        duration_minutes=30,
    )
    e2e_db.add(examination)
    e2e_db.flush()
    e2e_db.add(
        CandidateExaminationAssignment(
            institution_id=institution.institution_id,
            candidate_id=candidate["candidate_id"],
            examination_id=examination.examination_id,
            status="eligible",
        )
    )
    e2e_db.commit()
    assigned = e2e_client.get("/api/v1/candidate/examinations", headers=candidate_headers)
    assert assigned.status_code == 200 and assigned.json()[0]["examination_id"] == examination.examination_id

    consent = e2e_client.post(
        "/api/v1/candidate/consents",
        headers=candidate_headers,
        json={
            "consent_version": "CONSENT-1.0",
            "monitoring_consent": True,
            "privacy_notice_accepted": True,
            "institutional_policy_accepted": True,
        },
    )
    assert consent.status_code == 201 and consent.json()["accepted"] is True
    readiness = e2e_client.post(
        "/api/v1/candidate/device-checks",
        headers=candidate_headers,
        json={
            "supported_browser": True,
            "secure_context": True,
            "camera_available": True,
            "microphone_available": True,
            "browser_name": "Validation Browser",
            "browser_version": "1",
        },
    )
    assert readiness.status_code == 201 and readiness.json()["passed"] is True
    for role, device in (("primary", "rc1-primary"), ("secondary", "rc1-secondary")):
        selection = e2e_client.post(
            "/api/v1/candidate/cameras",
            headers=candidate_headers,
            json={"camera_role": role, "device_id": device, "label": f"{role.title()} Camera", "camera_count": 2},
        )
        assert selection.status_code == 201, selection.text
        permission = e2e_client.post(
            "/api/v1/candidate/camera-permissions",
            headers=candidate_headers,
            json={"camera_role": role, "status": "granted", "user_agent": "sprint3e-validation"},
        )
        assert permission.status_code == 201 and permission.json()["granted"] is True

    dashboard = e2e_client.get("/api/v1/candidate/dashboard", headers=candidate_headers)
    assert dashboard.status_code == 200 and dashboard.json()["readiness"]["ready_to_start"] is True
    started = e2e_client.post(
        f"/api/v1/candidate/examinations/{examination.examination_id}/start",
        headers=candidate_headers,
        json={"deployment_mode": "A"},
    )
    assert started.status_code == 201, started.text
    session_id = started.json()["session_id"]
    workspace = e2e_client.get(f"/api/v1/candidate/sessions/{session_id}", headers=candidate_headers)
    assert workspace.status_code == 200
    assert workspace.json()["primary_camera"]["camera_role"] == "primary"
    assert workspace.json()["secondary_camera"]["camera_role"] == "secondary"

    event_ids: list[str] = []
    for event_type, camera_id, risk_weight, description in (
        ("CAMERA_CONNECTED", "primary", 0.1, "Primary camera connected."),
        ("CAMERA_CONNECTED", "secondary", 0.1, "Secondary camera connected."),
        ("TAB_FOCUS_LOST", None, 0.3, "The demonstration tab lost visibility."),
        ("FACE_NOT_DETECTED", "primary", 0.5, "Primary view did not contain a detectable face."),
        ("FACE_NOT_DETECTED", "primary", 0.5, "Primary view remained without a detectable face."),
        ("FACE_NOT_DETECTED", "primary", 0.5, "Primary view still lacked a detectable face."),
        ("CAMERA_DISCONNECTED", "secondary", 0.7, "Secondary camera track ended."),
    ):
        event = e2e_client.post(
            "/api/v1/evidence-events/",
            headers=candidate_headers,
            json={
                "session_id": session_id,
                "candidate_id": candidate["candidate_id"],
                "source_module": "sprint3e_validation",
                "event_type": event_type,
                "camera_id": camera_id,
                "risk_weight": risk_weight,
                "confidence": 1.0,
                "description": description,
            },
        )
        assert event.status_code == 201, event.text
        event_ids.append(event.json()["event_id"])

    reviewer_headers = _auth(_login(e2e_client, "reviewer@example.test"))
    queue = e2e_client.get("/api/v1/reviewer/sessions?unresolved=true", headers=reviewer_headers)
    assert queue.status_code == 200 and queue.json()[0]["session_id"] == session_id
    detail = e2e_client.get(f"/api/v1/reviewer/sessions/{session_id}", headers=reviewer_headers)
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert set(detail_body["latest_assessment"]["evidence_event_ids"]) == set(event_ids[2:])
    assert detail_body["latest_recommendation"]["requires_reviewer"] is True
    assert detail_body["latest_policy_evaluation"]["requires_reviewer"] is True
    assert detail_body["primary_camera"]["connection_status"] == "connected"
    assert detail_body["secondary_camera"]["connection_status"] == "disconnected"

    decision = e2e_client.post(
        f"/api/v1/examination-sessions/{session_id}/reviewer-decisions",
        headers=reviewer_headers,
        json={
            "assessment_id": detail_body["latest_assessment"]["assessment_id"],
            "recommendation_id": detail_body["latest_recommendation"]["recommendation_id"],
            "policy_evaluation_id": detail_body["latest_policy_evaluation"]["evaluation_id"],
            "decision": "REQUEST_MORE_EVIDENCE",
            "rationale": "Secondary-camera disconnection requires additional contextual evidence.",
        },
    )
    assert decision.status_code == 201, decision.text
    timeline = e2e_client.get(
        f"/api/v1/examination-sessions/{session_id}/governance-timeline", headers=reviewer_headers
    )
    assert timeline.status_code == 200
    assert {entry["entry_type"] for entry in timeline.json()} >= {
        "EvidenceEvent",
        "ContextualAssessment",
        "AgentRecommendation",
        "PolicyEvaluation",
        "ReviewerDecision",
        "GovernanceAuditRecord",
    }
    report = e2e_client.post(f"/api/v1/examination-sessions/{session_id}/reports", headers=reviewer_headers)
    assert report.status_code == 201, report.text
    retrieved = e2e_client.get(
        f"/api/v1/examination-sessions/{session_id}/reports/{report.json()['report_id']}",
        headers=reviewer_headers,
    )
    assert retrieved.status_code == 200 and retrieved.json() == report.json()

    completed = e2e_client.post(f"/api/v1/candidate/sessions/{session_id}/complete", headers=candidate_headers)
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    admin_headers = _auth(_login(e2e_client, "admin@example.test"))
    metrics = e2e_client.get("/api/v1/admin/metrics", headers=admin_headers)
    assert metrics.status_code == 200
    assert metrics.json()["completed_sessions"] == 1
    assert metrics.json()["camera_failure_count"] == 1
    assert e2e_client.get(f"/api/v1/admin/sessions/{session_id}", headers=admin_headers).status_code == 200
    audit = e2e_client.get("/api/v1/audit-logs/", headers=admin_headers)
    assert audit.status_code == 200 and audit.json()
