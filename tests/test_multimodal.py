from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.api.deps.database import get_db
from apps.api.app.main import app
from serps_pop.domain.evidence import EvidenceEvent
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.engine import RULE_VERSION, assess_events
from serps_pop.governance.models import AgentRecommendation, ContextualAssessment, GovernanceAuditRecord, PolicyEvaluation
from serps_pop.identity.models import Candidate, Examination, ExaminationSession, Institution
from serps_pop.identity.services import ROLE_CANDIDATE, ROLE_REVIEWER
from serps_pop.infrastructure.database import Base


@contextmanager
def multimodal_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = local_session()
    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def seed_active_session(db: Session) -> None:
    db.add(Institution(institution_id="INST-1", code="MIVA", name="MIVA University"))
    db.add(Candidate(candidate_id="CAND-1", institution_id="INST-1", candidate_identifier="C-1", full_name="Test Candidate", email="candidate@example.test", user_id="USER-1"))
    db.add(Examination(examination_id="EXAM-1", institution_id="INST-1", exam_code="MM-1", title="Multimodal Test", status="active"))
    db.add(ExaminationSession(session_id="SESSION-1", institution_id="INST-1", candidate_id="CAND-1", examination_id="EXAM-1", status="active", deployment_mode="B"))
    db.commit()


def client(db: Session, institution_id: str = "INST-1") -> TestClient:
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(user_id="USER-1", institution_id=institution_id, roles=(ROLE_CANDIDATE,))
    return TestClient(app)


def event(event_id: str, event_type: str, seconds: int, confidence: float = 0.9, camera_id: str | None = None) -> EvidenceEvent:
    return EvidenceEvent(
        event_id=event_id,
        session_id="SESSION-1",
        candidate_id="CAND-1",
        timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds),
        source_module="candidate_browser",
        event_type=event_type,
        risk_weight=0.5,
        confidence=confidence,
        camera_id=camera_id,
        description=event_type,
        metadata_json={"fixture": "synthetic_event_metadata"},
    )


def payload(event_type: str, *, camera_id: str | None = None, metadata: dict | None = None) -> dict:
    return {
        "session_id": "SESSION-1",
        "candidate_id": "CAND-1",
        "timestamp": "2026-08-01T10:00:00+00:00",
        "source_module": "candidate_browser",
        "event_type": event_type,
        "risk_weight": 0.65,
        "confidence": 0.91,
        "camera_id": camera_id,
        "description": f"Synthetic detector fixture produced {event_type}.",
        "metadata_json": metadata or {"fixture": "synthetic", "raw_video_stored": False},
    }


def test_isolated_benign_person_and_transient_audio_remain_low_risk():
    result = assess_events([event("PERSON", "person_detected", 0), event("AUDIO", "audio_activity_detected", 2)])
    assert result.risk_level == "Low"
    assert result.risk_score == 0.05
    assert result.evidence_event_ids == ["AUDIO"]


def test_repeated_and_corroborated_multimodal_rules_are_explainable():
    result = assess_events([
        event("MULTI", "multiple_persons_detected", 0, camera_id="secondary"),
        event("AUDIO-1", "sustained_audio_activity", 5),
        event("AUDIO-2", "sustained_audio_activity", 15),
    ])
    assert result.risk_level == "Critical"
    assert result.risk_score == 1.0
    assert "multiple persons coincided with sustained audio activity" in result.explanation
    assert "Repeated evidence" in result.explanation
    assert result.metadata["correlations"]


def test_mobile_phone_corroborated_across_cameras_requires_human_review_level():
    result = assess_events([
        event("PHONE-P", "mobile_phone_detected", 0, camera_id="primary"),
        event("PHONE-S", "mobile_phone_detected", 5, camera_id="secondary"),
    ])
    assert result.risk_level == "Critical"
    assert result.risk_score == 0.9
    assert "corroborated across camera roles" in result.explanation


def test_detector_unavailable_is_a_limitation_not_misconduct_evidence():
    result = assess_events([
        event("OBJECT-OFF", "object_detector_unavailable", 0),
        event("AUDIO-OFF", "audio_monitor_unavailable", 1),
        event("FACE-OFF", "face_detector_unavailable", 2),
    ])
    assert result.risk_score == 0
    assert result.risk_level == "Low"
    assert result.evidence_event_ids == []
    assert "did not contribute to misconduct risk" in result.explanation


def test_sustained_face_absence_and_sustained_audio_are_contextually_correlated():
    result = assess_events([
        event("FACE-ABSENT", "sustained_face_absence", 0),
        event("AUDIO", "sustained_audio_activity", 5),
    ])
    assert result.risk_level == "High"
    assert "face absence coincided with sustained audio activity" in result.explanation


def test_camera_disconnect_is_distinct_from_face_absence():
    result = assess_events([
        event("FACE", "face_not_detected", 0),
        event("CAMERA", "camera_disconnected", 5),
    ])
    assert result.metadata["combined_pattern"] is False
    assert "camera disconnection corroborated face absence" not in result.metadata["correlations"]


def test_face_return_is_recorded_as_cie_recovery_without_erasing_prior_evidence():
    result = assess_events([
        event("ABSENT", "sustained_face_absence", 0),
        event("RETURNED", "face_detected", 8),
    ])
    assert result.metadata["face_presence_recovered"] is True
    assert "recovery of face presence" in result.explanation
    assert result.evidence_event_ids == ["ABSENT"]


def test_face_monitoring_event_types_are_accepted_and_persisted():
    with multimodal_db() as db:
        seed_active_session(db)
        api = client(db)
        for event_type in ("face_detected", "face_not_detected", "sustained_face_absence", "face_detector_unavailable"):
            response = api.post("/api/v1/evidence-events/", json=payload(event_type, camera_id="primary"))
            assert response.status_code == 201, response.text
        assert {record.event_type for record in db.scalars(select(EvidenceEventRecord)).all()} == {
            "face_detected", "face_not_detected", "sustained_face_absence", "face_detector_unavailable"
        }


def test_multimodal_event_persists_metadata_and_runs_the_full_governance_chain():
    with multimodal_db() as db:
        seed_active_session(db)
        response = client(db).post("/api/v1/evidence-events/", json=payload(
            "mobile_phone_detected",
            camera_id="secondary",
            metadata={"detected_class": "cell phone", "object_count": 1, "model_name": "EfficientDet-Lite0 (COCO)", "model_version": "float32/1", "threshold": 0.55, "raw_video_stored": False},
        ))
        assert response.status_code == 201, response.text
        stored = db.scalar(select(EvidenceEventRecord))
        assert stored.metadata_json["detected_class"] == "cell phone"
        assessment = db.scalar(select(ContextualAssessment))
        recommendation = db.scalar(select(AgentRecommendation))
        evaluation = db.scalar(select(PolicyEvaluation))
        assert assessment.rule_version == RULE_VERSION
        assert assessment.evidence_event_ids == [stored.event_id]
        assert recommendation.recommended_action == "NOTIFY_REVIEWER"
        assert recommendation.requires_reviewer is True
        assert evaluation.requires_reviewer is True
        assert evaluation.continue_examination is True
        assert db.scalars(select(GovernanceAuditRecord)).all()


def test_audio_event_metadata_is_privacy_safe_and_reported_without_raw_audio():
    with multimodal_db() as db:
        seed_active_session(db)
        api = client(db)
        response = api.post("/api/v1/evidence-events/", json=payload(
            "sustained_audio_activity",
            metadata={"normalized_level": 0.18, "threshold": 0.08, "duration_ms": 2800, "recurrence_count": 1, "detector_version": "SERPS-AUDIO-1.0", "raw_audio_stored": False},
        ))
        assert response.status_code == 201, response.text
        stored = db.scalar(select(EvidenceEventRecord))
        assert stored.metadata_json["duration_ms"] == 2800
        assert "audio_samples" not in stored.metadata_json
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(user_id="REVIEWER-1", institution_id="INST-1", roles=(ROLE_REVIEWER,))
        report = api.post("/api/v1/examination-sessions/SESSION-1/reports")
        assert report.status_code == 201, report.text
        report_event = report.json()["report_payload"]["evidence_events"][0]
        assert report_event["metadata_json"]["raw_audio_stored"] is False


def test_raw_audio_metadata_is_rejected():
    with multimodal_db() as db:
        seed_active_session(db)
        response = client(db).post("/api/v1/evidence-events/", json=payload("audio_activity_detected", metadata={"audio_samples": [0.1, 0.2]}))
        assert response.status_code == 422
        assert db.scalars(select(EvidenceEventRecord)).all() == []


def test_candidate_authorisation_and_institution_isolation_apply_to_multimodal_events():
    with multimodal_db() as db:
        seed_active_session(db)
        response = client(db, institution_id="OTHER").post("/api/v1/evidence-events/", json=payload("multiple_persons_detected", camera_id="secondary"))
        assert response.status_code == 403
        assert db.scalars(select(EvidenceEventRecord)).all() == []
