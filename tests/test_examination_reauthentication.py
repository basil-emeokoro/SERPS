from datetime import datetime, timedelta, timezone
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from apps.api.app.main import app
from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.api.deps.database import get_db
from serps_pop.infrastructure.database import Base
from serps_pop.identity.models import Institution, User, Candidate, Examination, ExaminationSession
from serps_pop.identity.services import DomainNotFound, DomainConflict
from serps_pop.identity_assurance.models import BiometricEnrollment, IdentityAssuranceProfile, IdentityChallenge
from serps_pop.identity_assurance.schemas import FaceAuthenticationSubmit
from serps_pop.identity_assurance import reauthentication as lifecycle
from serps_pop.governance.models import InstitutionalPolicy, GovernanceAuditRecord, PolicyEvaluation
from serps_pop.governance.schemas import ReviewerDecisionCreate
from serps_pop.governance.services import create_contextual_assessment, create_agent_recommendation, create_policy_evaluation, record_reviewer_decision
from serps_pop.evidence.models import EvidenceEventRecord


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine, autoflush=False) as session:
        yield session
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def seeded(db):
    db.add(Institution(institution_id="I", code="I", name="Test institution")); db.flush()
    db.add(User(user_id="U", institution_id="I", email="candidate@test.invalid", full_name="Candidate", password_hash="unused")); db.flush()
    db.add(Candidate(candidate_id="C", institution_id="I", user_id="U", candidate_identifier="C", full_name="Candidate", email="candidate@test.invalid"))
    db.add(Examination(examination_id="E", institution_id="I", exam_code="E", title="Test", status="active")); db.flush()
    db.add(ExaminationSession(session_id="S", candidate_id="C", institution_id="I", examination_id="E", status="active", monitoring_status="active", deployment_mode="C"))
    db.add(IdentityAssuranceProfile(user_id="U", enrolment_status="enrolled", biometric_required=True))
    db.add(BiometricEnrollment(user_id="U", representation_json=[0.5]*64, representation_hash="test", capture_summary={}, capture_count=5, liveness_confidence=1))
    db.add(InstitutionalPolicy(institution_id="I", created_by="U", metadata_json={"identity_reauthentication": {"enabled": True}}))
    db.commit()
    return db


def assess(db, kinds=("sustained_face_absence", "face_detected"), start=None):
    start = start or datetime.now(timezone.utc) - timedelta(seconds=20)
    for index, kind in enumerate(kinds):
        db.add(EvidenceEventRecord(event_id=str(uuid.uuid4()), session_id="S", candidate_id="C", timestamp=start+timedelta(seconds=index), source_module="candidate_browser", event_type=kind, risk_weight=0.3, confidence=0.95, camera_id="primary", description="Synthetic test evidence"))
    db.flush()
    args = dict(actor_user_id="U", actor_institution_id="I", actor_roles=["Candidate"])
    assessment = create_contextual_assessment(db, session_id="S", **args)
    recommendation = create_agent_recommendation(db, assessment_id=assessment.assessment_id, **args)
    evaluation = create_policy_evaluation(db, recommendation_id=recommendation.recommendation_id, **args)
    db.commit()
    return evaluation


def begin(db):
    result = lifecycle.begin(db, "S", "U", "I"); db.commit(); return result


def verify(db, token, value=0.5, **extra):
    payload = FaceAuthenticationSubmit(challenge_token=token, descriptor=[value]*64, one_face=True, lighting_score=0.9, distance_score=0.9)
    payload = payload.model_copy(update=extra)
    result = lifecycle.verify(db, "S", "U", "I", payload); db.commit(); return result


def review(db, decision):
    requirement = lifecycle.latest_requirement(db, "S")
    meta = requirement.metadata_json
    record_reviewer_decision(db, session_id="S", payload=ReviewerDecisionCreate(assessment_id=meta["assessment_id"], recommendation_id=meta["recommendation_id"], policy_evaluation_id=meta["policy_evaluation_id"], decision=decision, rationale="Synthetic human review"), actor_user_id="U", actor_institution_id="I", actor_roles=["Reviewer/Proctor"])
    db.commit()


def test_contextual_requirement_binds_full_chain_and_success_is_idempotent(seeded):
    db = seeded
    evaluation = assess(db)
    requirement = lifecycle.latest_requirement(db, "S")
    assert requirement.status == "required"
    assert requirement.metadata_json.items() >= {"session_id":"S", "candidate_id":"C", "institution_id":"I", "examination_id":"E", "policy_evaluation_id": evaluation.evaluation_id}.items()
    before = db.get(ExaminationSession, "S").updated_at
    first = begin(db); second = begin(db)
    assert first["challenge_token"] == second["challenge_token"]
    assert first["attempts"] == second["attempts"] == 1
    result = verify(db, first["challenge_token"])
    assert result["state"] == "completed" and result["outcome"] == "Verified"
    assert result["required"] is False and result["return_path"] == "/candidate/examinations/S"
    assert verify(db, first["challenge_token"], value=0) == result
    audits = db.scalars(select(GovernanceAuditRecord).where(GovernanceAuditRecord.action == "IDENTITY_REAUTHENTICATION_RESULT")).all()
    assert len(audits) == 1
    session = db.get(ExaminationSession, "S")
    assert session.status == "active" and session.monitoring_status == "active" and session.updated_at == before
    assert db.scalar(select(func.count()).select_from(ExaminationSession)) == 1


@pytest.mark.parametrize("kinds", [("mobile_phone_detected",), ("tab_focus_lost",)*9, ("sustained_face_absence",), ("face_not_detected", "face_detected"), ("multiple_persons_detected",)])
def test_nonqualifying_context_never_creates_requirement_even_at_high_risk(seeded, kinds):
    evaluation = assess(seeded, kinds)
    assert not evaluation.metadata_json["reauthentication_expected"]
    assert lifecycle.latest_requirement(seeded, "S") is None
    assert begin(seeded)["state"] == "not_required"


def test_additional_people_uses_configured_context_threshold(seeded):
    evaluation = assess(seeded, ("multiple_persons_detected",)*2)
    assert evaluation.metadata_json["identity_conditions"] == ["additional_persons"]
    assert lifecycle.latest_requirement(seeded, "S") is not None


def test_unconfigured_institution_never_silently_enables_identity_policy(seeded):
    db = seeded
    db.add(InstitutionalPolicy(institution_id="I", created_by="U", metadata_json={})); db.commit()
    evaluation = assess(db)
    assert not evaluation.metadata_json["reauthentication_expected"]
    assert lifecycle.latest_requirement(db, "S") is None


def test_repeated_evaluations_cooldown_and_old_evidence_do_not_loop(seeded, monkeypatch):
    db = seeded
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(lifecycle, "utc_now", lambda: now)
    assess(db); first = begin(db)
    assess(db)
    assert begin(db)["challenge_token"] == first["challenge_token"]
    verify(db, first["challenge_token"])
    assess(db)
    assert db.scalar(select(func.count()).select_from(IdentityChallenge)) == 1
    monkeypatch.setattr(lifecycle, "utc_now", lambda: now+timedelta(seconds=301))
    assess(db, kinds=())  # Expiring a cooldown does not create fresh evidence.
    assert db.scalar(select(func.count()).select_from(IdentityChallenge)) == 1
    assess(db, start=now+timedelta(seconds=302))
    assert db.scalar(select(func.count()).select_from(IdentityChallenge)) == 2


def test_manual_review_is_not_resubmitted_and_reviewer_can_continue(seeded):
    db=seeded; assess(db); first=begin(db)
    result=verify(db,first["challenge_token"],value=0.81)
    assert result["state"] == "manual_review" and result["outcome"] == "Manual Review"
    assert "challenge_token" not in begin(db)
    assert verify(db,first["challenge_token"])["state"] == "manual_review"
    review(db,"ACKNOWLEDGE")
    assert begin(db)["state"] == "manual_review"
    review(db,"CONTINUE")
    result=begin(db)
    assert result["state"] == "released" and not result["required"]
    assert result["outcome"] != "Verified"


def test_failed_attempt_has_cooldown_fresh_token_and_hard_limit(seeded,monkeypatch):
    db=seeded; now=datetime.now(timezone.utc); monkeypatch.setattr(lifecycle,"utc_now",lambda:now)
    assess(db); first=begin(db)
    assert verify(db,first["challenge_token"],value=0)["state"] == "failed"
    assert "challenge_token" not in begin(db)
    for i in range(2):
        now += timedelta(seconds=31)
        fresh=begin(db)
        assert fresh["challenge_token"] != first["challenge_token"]
        with pytest.raises(DomainNotFound): verify(db,first["challenge_token"])
        result=verify(db,fresh["challenge_token"],value=0)
    assert result["state"] == "manual_review"
    assert "challenge_token" not in begin(db)


def test_expiry_is_persisted_and_recovered_with_bounded_new_challenge(seeded,monkeypatch):
    db=seeded; now=datetime.now(timezone.utc); monkeypatch.setattr(lifecycle,"utc_now",lambda:now)
    assess(db); first=begin(db)
    now+=timedelta(seconds=601)
    assert verify(db,first["challenge_token"])["state"] == "expired"
    assert lifecycle.latest_requirement(db,"S").status == "expired"
    next_attempt=begin(db)
    assert next_attempt["challenge_token"] != first["challenge_token"]
    assert verify(db,next_attempt["challenge_token"])["state"] == "completed"


def test_reviewer_can_authorise_fresh_attempt_after_manual_review(seeded,monkeypatch):
    db=seeded; now=datetime.now(timezone.utc); monkeypatch.setattr(lifecycle,"utc_now",lambda:now)
    assess(db); first=begin(db); verify(db,first["challenge_token"],value=0.81)
    review(db,"REQUEST_REAUTHENTICATION")
    assert "challenge_token" not in begin(db)
    now += timedelta(seconds=31)
    fresh=begin(db)
    assert fresh["challenge_token"] != first["challenge_token"]
    assert verify(db,fresh["challenge_token"])["state"] == "completed"


@pytest.mark.parametrize("user,institution,session",[("OTHER","I","S"),("U","OTHER","S"),("U","I","OTHER")])
def test_candidate_institution_and_session_isolation(seeded,user,institution,session):
    db=seeded; assess(db); first=begin(db)
    with pytest.raises(DomainNotFound): lifecycle.begin(db,session,user,institution)
    with pytest.raises(DomainNotFound): lifecycle.verify(db,session,user,institution,FaceAuthenticationSubmit(challenge_token=first["challenge_token"],descriptor=[0.5]*64,one_face=True,lighting_score=1,distance_score=1))
    assert lifecycle.latest_requirement(db,"S").status == "pending"


def test_quality_gate_privacy_and_completed_session_guard(seeded):
    db=seeded; assess(db); first=begin(db)
    result=verify(db,first["challenge_token"],one_face=False)
    assert result["outcome"] == "Retry Required" and result["required"]
    requirement=lifecycle.latest_requirement(db,"S")
    assert not requirement.metadata_json["quality_validated"]
    serial=json.dumps(requirement.metadata_json)
    assert "descriptor" not in serial and first["challenge_token"] not in serial
    assert requirement.metadata_json["raw_media_stored"] is False
    for audit in db.scalars(select(GovernanceAuditRecord)):
        assert "descriptor" not in json.dumps(audit.details)
    db.get(ExaminationSession,"S").status="completed"; db.commit()
    with pytest.raises(DomainConflict): begin(db)


def test_http_roundtrip_and_policy_authorisation(seeded):
    db=seeded
    app.dependency_overrides[get_db]=lambda: db
    app.dependency_overrides[get_current_user]=lambda: CurrentUser("U","I",("Candidate",))
    with TestClient(app) as client:
        base="/api/v1/identity-assurance/reauthentication"
        assert client.put(base+"/policy",json={"enabled":True}).status_code == 403
        assess(db)
        first=client.post(base+"/sessions/S/challenge")
        assert first.status_code == 200, first.text
        result=client.post(base+"/sessions/S/verify",json={"challenge_token":first.json()["challenge_token"],"descriptor":[0.5]*64,"one_face":True,"lighting_score":1,"distance_score":1})
        assert result.status_code == 200 and not result.json()["required"]
        assert client.get(base+"/sessions/S").json()["state"] == "completed"


def test_policy_configuration_appends_without_mutating_prior_policy(seeded):
    from serps_pop.identity.services import ROLE_ADMIN
    db=seeded; old=db.scalar(select(InstitutionalPolicy)); previous=dict(old.metadata_json)
    app.dependency_overrides[get_db]=lambda: db
    app.dependency_overrides[get_current_user]=lambda: CurrentUser("U","I",(ROLE_ADMIN,))
    with TestClient(app) as client:
        path="/api/v1/identity-assurance/reauthentication/policy"
        assert client.put(path,json={"enabled":True,"minimum_additional_person_events":1}).status_code == 422
        response=client.put(path,json={"enabled":True,"additional_persons":False})
        assert response.status_code == 200, response.text
        assert response.json()["policy_id"] != old.policy_id
        assert client.get(path).json()["additional_persons"] is False
    db.refresh(old)
    assert old.metadata_json == previous


def test_concurrent_begin_and_verify_consume_once(seeded, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    import sqlite3
    db=seeded; assess(db)
    database=tmp_path / "concurrency.sqlite"
    with sqlite3.connect(database) as destination:
        db.connection().connection.driver_connection.backup(destination)
    engine=create_engine(f"sqlite:///{database}", connect_args={"timeout": 15})
    barrier=Barrier(2)
    def start(_):
        with Session(engine, autoflush=False) as concurrent:
            barrier.wait(timeout=10)
            return begin(concurrent)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results=list(workers.map(start,range(2)))
    assert results[0]["challenge_token"] == results[1]["challenge_token"]
    barrier=Barrier(2)
    def consume(_):
        with Session(engine, autoflush=False) as concurrent:
            barrier.wait(timeout=10)
            return verify(concurrent,results[0]["challenge_token"])
    with ThreadPoolExecutor(max_workers=2) as workers:
        results=list(workers.map(consume,range(2)))
    assert results[0]["state"] == results[1]["state"] == "completed"
    with Session(engine) as checked:
        assert checked.scalar(select(func.count()).select_from(GovernanceAuditRecord).where(GovernanceAuditRecord.action == "IDENTITY_REAUTHENTICATION_RESULT")) == 1
        assert checked.scalar(select(func.count()).select_from(IdentityChallenge)) == 1
    engine.dispose()


def test_examination_token_cannot_verify_another_session_of_same_candidate(seeded):
    db=seeded; assess(db); token=begin(db)["challenge_token"]
    db.add(ExaminationSession(session_id="SECOND",candidate_id="C",institution_id="I",examination_id="E",status="active")); db.commit()
    assert lifecycle.begin(db,"SECOND","U","I")["state"] == "not_required"
    payload=FaceAuthenticationSubmit(challenge_token=token,descriptor=[0.5]*64,one_face=True,lighting_score=1,distance_score=1)
    with pytest.raises(DomainNotFound): lifecycle.verify(db,"SECOND","U","I",payload)
    assert lifecycle.latest_requirement(db,"S").status == "pending"


def test_monitoring_http_evidence_runs_full_governance_chain(seeded):
    db=seeded
    app.dependency_overrides[get_db]=lambda: db
    app.dependency_overrides[get_current_user]=lambda: CurrentUser("U","I",("Candidate",))
    with TestClient(app) as client:
        for kind in ("sustained_face_absence", "face_detected"):
            response=client.post("/api/v1/evidence-events/",json={"session_id":"S","candidate_id":"C","source_module":"candidate_browser","event_type":kind,"camera_id":"primary","confidence":0.95,"risk_weight":0.3,"description":"Synthetic identity context"})
            assert response.status_code == 201,response.text
        state=client.get("/api/v1/identity-assurance/reauthentication/sessions/S").json()
        assert state["required"] and state["conditions"] == ["sustained_absence_reappearance"]
        evaluation=db.get(PolicyEvaluation,state["policy_evaluation_id"])
        assert evaluation.metadata_json["misconduct_determination"] is False
