from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.domain.evidence import EvidenceEvent
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.engine import assess_events, risk_level_for_score
from serps_pop.governance.models import ContextualAssessment, GovernanceAuditRecord, PolicyEvaluation
from serps_pop.governance.services import governance_timeline, governance_timeline_count
from serps_pop.identity.models import Candidate, Examination, ExaminationSession, Institution
from serps_pop.identity.services import ROLE_REVIEWER
from serps_pop.infrastructure.database import Base


@contextmanager
def governance_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = local_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed_session(db: Session, *, institution_id: str = "INST-1", session_id: str = "SESSION-1") -> None:
    db.add(Institution(institution_id=institution_id, code=institution_id, name=f"{institution_id} University"))
    db.add(Candidate(
        candidate_id=f"CAND-{institution_id}", institution_id=institution_id, candidate_identifier=f"ID-{institution_id}",
        full_name="Ada Candidate", email=f"ada-{institution_id.lower()}@example.test",
    ))
    db.add(Examination(
        examination_id=f"EXAM-{institution_id}", institution_id=institution_id, exam_code=f"CODE-{institution_id}",
        title="Governed Examination", status="active",
    ))
    db.add(ExaminationSession(
        session_id=session_id, institution_id=institution_id, candidate_id=f"CAND-{institution_id}",
        examination_id=f"EXAM-{institution_id}", status="active",
    ))
    db.commit()


def reviewer(institution_id: str = "INST-1", user_id: str = "REVIEWER-1") -> CurrentUser:
    return CurrentUser(user_id=user_id, institution_id=institution_id, roles=(ROLE_REVIEWER,))


def api_client(db: Session, user: CurrentUser | None = None) -> TestClient:
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    if user is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def add_events(db: Session, session_id: str = "SESSION-1") -> None:
    base = datetime(2026, 7, 19, 10, 0, tzinfo=timezone.utc)
    records = [
        EvidenceEventRecord(event_id="EVT-001", session_id=session_id, candidate_id="CAND-INST-1", timestamp=base,
                            source_module="camera", event_type="face_not_detected", risk_weight=0.5, confidence=0.9,
                            description="Face absent"),
        EvidenceEventRecord(event_id="EVT-002", session_id=session_id, candidate_id="CAND-INST-1", timestamp=base + timedelta(seconds=10),
                            source_module="camera", event_type="face_not_detected", risk_weight=0.5, confidence=0.8,
                            description="Face absent"),
        EvidenceEventRecord(event_id="EVT-003", session_id=session_id, candidate_id="CAND-INST-1", timestamp=base + timedelta(seconds=20),
                            source_module="camera", event_type="face_not_detected", risk_weight=0.5, confidence=0.95,
                            description="Face absent"),
        EvidenceEventRecord(event_id="EVT-004", session_id=session_id, candidate_id="CAND-INST-1", timestamp=base + timedelta(seconds=25),
                            source_module="camera", event_type="camera_disconnected", risk_weight=0.7, confidence=0.9,
                            description="Camera disconnected"),
    ]
    db.add_all(records)
    db.commit()


def test_risk_level_boundaries():
    assert risk_level_for_score(0.0) == "Low"
    assert risk_level_for_score(0.2999) == "Low"
    assert risk_level_for_score(0.30) == "Moderate"
    assert risk_level_for_score(0.60) == "High"
    assert risk_level_for_score(0.85) == "Critical"
    assert risk_level_for_score(1.2) == "Critical"


def test_temporal_window_combined_weight_and_explanation():
    base = datetime(2026, 7, 19, tzinfo=timezone.utc)
    events = [
        EvidenceEvent(event_id="OLD", session_id="S", candidate_id="C", timestamp=base, source_module="camera",
                      event_type="face_not_detected", risk_weight=0.2, confidence=0.9, description="old"),
        EvidenceEvent(event_id="FACE", session_id="S", candidate_id="C", timestamp=base + timedelta(seconds=100), source_module="camera",
                      event_type="face_not_detected", risk_weight=0.2, confidence=0.8, description="face"),
        EvidenceEvent(event_id="CAM", session_id="S", candidate_id="C", timestamp=base + timedelta(seconds=110), source_module="camera",
                      event_type="camera_disconnected", risk_weight=0.2, confidence=1.0, description="camera"),
    ]
    result = assess_events(events, window_seconds=60)
    assert result.risk_score == 0.50
    assert result.risk_level == "Moderate"
    assert result.evidence_event_ids == ["FACE", "CAM"]
    assert "combined camera-disconnection and face-absence pattern" not in result.explanation


def run_chain(client: TestClient, db: Session) -> tuple[dict, dict, dict]:
    assessment_response = client.post("/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={})
    assert assessment_response.status_code == 201, assessment_response.text
    assessment = assessment_response.json()
    recommendation_response = client.post(f"/api/v1/contextual-assessments/{assessment['assessment_id']}/recommendations")
    assert recommendation_response.status_code == 201, recommendation_response.text
    recommendation = recommendation_response.json()
    evaluation_response = client.post(f"/api/v1/agent-recommendations/{recommendation['recommendation_id']}/policy-evaluations")
    assert evaluation_response.status_code == 201, evaluation_response.text
    return assessment, recommendation, evaluation_response.json()


def test_no_evidence_assessment_and_recalculation_are_persisted():
    with governance_db() as db:
        seed_session(db)
        client = api_client(db, reviewer())
        first = client.post("/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={})
        second = client.post("/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={})
        assert first.status_code == second.status_code == 201
        assert first.json()["risk_level"] == "Low"
        assert first.json()["assessment_id"] != second.json()["assessment_id"]
        assert len(db.scalars(select(ContextualAssessment)).all()) == 2


def test_full_governance_chain_queue_decision_timeline_and_report():
    with governance_db() as db:
        seed_session(db)
        add_events(db)
        client = api_client(db, reviewer())
        assessment, recommendation, evaluation = run_chain(client, db)
        assert assessment["risk_level"] == "Critical"
        assert recommendation["recommended_action"] == "ESCALATE_INCIDENT"
        assert evaluation["continue_examination"] is True
        assert evaluation["requires_reviewer"] is True
        assert db.scalar(select(PolicyEvaluation)).continue_examination is True

        queue = client.get("/api/v1/reviewer/sessions?unresolved=true")
        assert queue.status_code == 200
        assert queue.json()[0]["candidate_name"] == "Ada Candidate"
        assert queue.json()[0]["review_status"] == "unresolved"

        decision_payload = {
            "assessment_id": assessment["assessment_id"],
            "recommendation_id": recommendation["recommendation_id"],
            "policy_evaluation_id": evaluation["evaluation_id"],
            "decision": "REQUEST_MORE_EVIDENCE",
            "rationale": "Additional contextual evidence is required before escalation.",
        }
        decision = client.post("/api/v1/examination-sessions/SESSION-1/reviewer-decisions", json=decision_payload)
        assert decision.status_code == 201, decision.text
        assert db.scalar(select(GovernanceAuditRecord).where(GovernanceAuditRecord.action == "REVIEWER_DECISION_RECORDED"))

        timeline = client.get("/api/v1/examination-sessions/SESSION-1/governance-timeline")
        assert timeline.status_code == 200
        assert {entry["entry_type"] for entry in timeline.json()} >= {
            "EvidenceEvent", "ContextualAssessment", "AgentRecommendation", "PolicyEvaluation", "ReviewerDecision", "GovernanceAuditRecord"
        }
        report = client.post("/api/v1/examination-sessions/SESSION-1/reports")
        assert report.status_code == 201, report.text
        report_body = report.json()
        payload = report_body["report_payload"]
        assert payload["candidate"]["full_name"] == "Ada Candidate"
        assert len(payload["contextual_assessments"]) == 1
        assert len(payload["agent_recommendations"]) == 1
        assert len(payload["policy_evaluations"]) == 1
        assert len(payload["reviewer_decisions"]) == 1
        assert payload["audit_history"]
        retrieved = client.get(f"/api/v1/examination-sessions/SESSION-1/reports/{report_body['report_id']}")
        assert retrieved.status_code == 200
        assert retrieved.json() == report_body


def test_operational_timeline_can_be_bounded_without_deleting_history():
    with governance_db() as db:
        seed_session(db)
        base = datetime(2026, 7, 19, 10, 0, tzinfo=timezone.utc)
        db.add_all([
            EvidenceEventRecord(
                event_id=f"EVT-{index:03d}",
                session_id="SESSION-1",
                candidate_id="CAND-INST-1",
                timestamp=base + timedelta(seconds=index),
                source_module="camera",
                event_type="camera_heartbeat",
                risk_weight=0.0,
                confidence=1.0,
                description="Camera heartbeat",
            )
            for index in range(205)
        ])
        db.commit()

        timeline = governance_timeline(
            db, session_id="SESSION-1", actor_institution_id="INST-1", actor_roles=(ROLE_REVIEWER,), limit=200
        )
        assert len(timeline) == 200
        assert timeline[0]["entity_id"] == "EVT-005"
        assert timeline[-1]["entity_id"] == "EVT-204"
        assert governance_timeline_count(db, session_id="SESSION-1") == 205


def test_reviewer_decision_validation_rejects_empty_and_unsupported_values():
    with governance_db() as db:
        seed_session(db)
        add_events(db)
        client = api_client(db, reviewer())
        assessment, recommendation, evaluation = run_chain(client, db)
        base = {
            "assessment_id": assessment["assessment_id"], "recommendation_id": recommendation["recommendation_id"],
            "policy_evaluation_id": evaluation["evaluation_id"], "decision": "CONTINUE", "rationale": "   ",
        }
        assert client.post("/api/v1/examination-sessions/SESSION-1/reviewer-decisions", json=base).status_code == 422
        base["rationale"] = "Reviewed evidence."
        base["decision"] = "DECLARE_MISCONDUCT"
        assert client.post("/api/v1/examination-sessions/SESSION-1/reviewer-decisions", json=base).status_code == 422


def test_invalid_unauthenticated_and_cross_institution_access():
    with governance_db() as db:
        seed_session(db)
        assert api_client(db, reviewer()).post("/api/v1/examination-sessions/MISSING/contextual-assessments", json={}).status_code == 404
        assert api_client(db, reviewer("OTHER", "REVIEWER-2")).post(
            "/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={}
        ).status_code == 403
        assert api_client(db, None).post(
            "/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={}
        ).status_code == 401


def test_governance_records_reject_mutation():
    with governance_db() as db:
        seed_session(db)
        assessment = api_client(db, reviewer()).post(
            "/api/v1/examination-sessions/SESSION-1/contextual-assessments", json={}
        ).json()
        record = db.get(ContextualAssessment, assessment["assessment_id"])
        record.explanation = "mutated"
        with pytest.raises(ValueError, match="append-only"):
            db.flush()
        db.rollback()
