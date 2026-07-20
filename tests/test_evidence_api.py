from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.models import AgentRecommendation, ContextualAssessment, PolicyEvaluation
from serps_pop.identity.models import (
    Candidate,
    CandidateExaminationAssignment,
    Examination,
    ExaminationSession,
    Institution,
)
from serps_pop.identity.services import ROLE_ADMIN, ROLE_CANDIDATE, ROLE_REVIEWER
from serps_pop.infrastructure.database import Base


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@contextmanager
def _db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _seed_session(db: Session, institution_id: str = "INST-1", session_id: str = "SESSION-1") -> ExaminationSession:
    institution = Institution(institution_id=institution_id, code=institution_id, name=f"{institution_id} Institution")
    candidate = Candidate(
        candidate_id="CAND-1",
        institution_id=institution_id,
        candidate_identifier="10000001",
        full_name="Demo Candidate",
        email=f"candidate-{institution_id.lower()}@example.com",
        user_id="USER-CANDIDATE",
    )
    examination = Examination(
        examination_id="EXAM-1",
        institution_id=institution_id,
        exam_code=f"{institution_id}-EXAM",
        title="Demo Examination",
    )
    assignment = CandidateExaminationAssignment(
        assignment_id="ASSIGN-1",
        institution_id=institution_id,
        candidate_id=candidate.candidate_id,
        examination_id=examination.examination_id,
    )
    examination_session = ExaminationSession(
        session_id=session_id,
        institution_id=institution_id,
        candidate_id=candidate.candidate_id,
        examination_id=examination.examination_id,
        assignment_id=assignment.assignment_id,
        status="active",
    )
    db.add_all([institution, candidate, examination, assignment, examination_session])
    db.commit()
    return examination_session


def _event_payload(
    session_id: str = "SESSION-1",
    event_type: str = "face_detected",
    timestamp: str = "2026-06-20T10:00:00+00:00",
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "candidate_id": "CAND-1",
        "timestamp": timestamp,
        "source_module": "candidate_browser",
        "event_type": event_type,
        "risk_weight": 0.02,
        "confidence": 0.95,
        "camera_id": "primary",
        "evidence_path": None,
        "description": f"{event_type} event",
    }


def _admin_user(institution_id: str = "INST-1") -> CurrentUser:
    return CurrentUser(user_id="USER-1", institution_id=institution_id, roles=(ROLE_ADMIN,))


def _candidate_user(institution_id: str = "INST-1", user_id: str = "USER-CANDIDATE") -> CurrentUser:
    return CurrentUser(user_id=user_id, institution_id=institution_id, roles=(ROLE_CANDIDATE,))


def _client(db: Session, current_user: CurrentUser | None = None) -> TestClient:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    else:
        app.dependency_overrides.pop(get_current_user, None)
    return TestClient(app)


def test_authenticated_valid_event_persists():
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, _candidate_user())

        response = client.post("/api/v1/evidence-events/", json=_event_payload())

        assert response.status_code == 201
        body = response.json()
        assert body["event_id"]
        assert body["event_type"] == "face_detected"
        stored = db.execute(select(EvidenceEventRecord)).scalars().all()
        assert len(stored) == 1
        assert stored[0].event_id == body["event_id"]


def test_persisted_event_can_be_retrieved():
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, _candidate_user())
        first = client.post(
            "/api/v1/evidence-events/",
            json=_event_payload(timestamp="2026-06-20T10:00:02+00:00"),
        ).json()
        second = client.post(
            "/api/v1/evidence-events/",
            json=_event_payload(event_type="tab_focus_lost", timestamp="2026-06-20T10:00:01+00:00"),
        ).json()

        app.dependency_overrides[get_current_user] = lambda: _admin_user()
        response = client.get("/api/v1/examination-sessions/SESSION-1/evidence-events")

        assert response.status_code == 200
        events = response.json()
        assert [event["event_id"] for event in events] == [second["event_id"], first["event_id"]]


def test_invalid_session_returns_404():
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, _candidate_user())

        response = client.post("/api/v1/evidence-events/", json=_event_payload(session_id="MISSING-SESSION"))

        assert response.status_code == 404


def test_unauthenticated_submission_returns_401():
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, None)

        response = client.post("/api/v1/evidence-events/", json=_event_payload())

        assert response.status_code == 401


def test_unauthorised_retrieval_returns_403():
    with _db_session() as db:
        _seed_session(db, institution_id="INST-1")
        client = _client(db, _admin_user(institution_id="INST-2"))

        response = client.get("/api/v1/examination-sessions/SESSION-1/evidence-events")

        assert response.status_code == 403


@pytest.mark.parametrize("role", [ROLE_REVIEWER, ROLE_ADMIN])
def test_reviewer_and_administrator_cannot_create_candidate_evidence(role: str):
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, CurrentUser(user_id="PRIVILEGED-USER", institution_id="INST-1", roles=(role,)))

        response = client.post("/api/v1/evidence-events/", json=_event_payload(event_type="tab_focus_lost"))

        assert response.status_code == 403
        assert db.scalars(select(EvidenceEventRecord)).all() == []
        assert db.scalars(select(ContextualAssessment)).all() == []
        assert db.scalars(select(AgentRecommendation)).all() == []
        assert db.scalars(select(PolicyEvaluation)).all() == []


def test_cross_institution_candidate_cannot_create_evidence():
    with _db_session() as db:
        _seed_session(db, institution_id="INST-1")
        client = _client(db, _candidate_user(institution_id="INST-2"))

        response = client.post("/api/v1/evidence-events/", json=_event_payload())

        assert response.status_code == 403
        assert db.scalars(select(EvidenceEventRecord)).all() == []


@pytest.mark.parametrize("field,value", [("event_type", "keystroke_capture"), ("source_module", "reviewer_console")])
def test_candidate_event_type_and_source_are_allowlisted(field: str, value: str):
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, _candidate_user())
        payload = _event_payload()
        payload[field] = value

        response = client.post("/api/v1/evidence-events/", json=payload)

        assert response.status_code == 422
        assert db.scalars(select(EvidenceEventRecord)).all() == []


def test_repeated_retrieval_does_not_mutate_stored_events():
    with _db_session() as db:
        _seed_session(db)
        client = _client(db, _candidate_user())
        client.post("/api/v1/evidence-events/", json=_event_payload())

        app.dependency_overrides[get_current_user] = lambda: _admin_user()
        first = client.get("/api/v1/examination-sessions/SESSION-1/evidence-events")
        second = client.get("/api/v1/examination-sessions/SESSION-1/evidence-events")

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
        stored = db.execute(select(EvidenceEventRecord)).scalars().all()
        assert len(stored) == 1
