from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from apps.api.app.api.deps.auth import CurrentUser
from serps_pop.candidate_workflow.services import candidate_protection_state
from serps_pop.evidence.models import EvidenceEventRecord
from serps_pop.governance.models import InstitutionalPolicy, PolicyEvaluation
from serps_pop.identity.models import Candidate, ExaminationSession
from test_governance import governance_db, seed_session, api_client, reviewer, run_chain


@pytest.fixture(autouse=True)
def restore_test_dependencies():
    from apps.api.app.main import app
    previous = dict(app.dependency_overrides)
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def transition(db, role, kind, offset=0):
    event = EvidenceEventRecord(event_id=uuid4().hex, session_id="SESSION-1", candidate_id="CAND-INST-1",
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=offset), source_module="camera",
        event_type=kind, camera_id=role, risk_weight=0, confidence=1, description="Synthetic operational transition")
    db.add(event); db.commit()
    return event.event_id


@pytest.mark.parametrize("mode,role,protect", [("A", "primary", True), ("A", "secondary", False),
    ("B", "primary", True), ("B", "secondary", True), ("C", "primary", True), ("C", "secondary", False)])
def test_required_camera_policy_and_recovery_without_phone_switch(mode, role, protect):
    with governance_db() as db:
        seed_session(db)
        db.get(ExaminationSession, "SESSION-1").deployment_mode = mode
        db.add(InstitutionalPolicy(institution_id="INST-1", metadata_json={"required_camera_loss_action": "PROTECT_AND_PAUSE"}))
        db.commit()
        loss_id = transition(db, role, "camera_disconnected")
        api = api_client(db, reviewer()); assessment, _, evaluation = run_chain(api, db)
        assert (evaluation["approved_action"] == "PROTECT_AND_PAUSE") is protect
        assert evaluation["metadata_json"]["misconduct_determination"] is False
        assert evaluation["metadata_json"]["reauthentication_expected"] is False
        assert assessment["metadata_json"]["required_camera_condition"]["required_roles"] == (["primary", "secondary"] if mode == "B" else ["primary"])
        candidate = db.get(Candidate, "CAND-INST-1")
        assert (candidate_protection_state(db, candidate, "SESSION-1")["state"] == "PROTECTED") is protect
        transition(db, role, "camera_reconnected", 1)
        assert candidate_protection_state(db, candidate, "SESSION-1")["state"] == "NORMAL"
        assert db.get(EvidenceEventRecord, loss_id) is not None
        assert db.get(ExaminationSession, "SESSION-1").status == "active"
        _, _, recovered = run_chain(api, db)
        assert recovered["metadata_json"]["required_camera_condition"]["unavailable_roles"] == []
        assert len(db.scalars(select(PolicyEvaluation)).all()) == 2


@pytest.mark.parametrize("action", [None, "CONTINUE_MONITORING", "NOTIFY_REVIEWER"])
def test_camera_policy_is_opt_in_and_does_not_require_identity(action):
    with governance_db() as db:
        seed_session(db)
        db.add(InstitutionalPolicy(institution_id="INST-1", metadata_json={"required_camera_loss_action": action}))
        db.commit(); transition(db, "primary", "camera_disconnected")
        _, _, evaluation = run_chain(api_client(db, reviewer()), db)
        assert evaluation["approved_action"] != "PROTECT_AND_PAUSE"
        assert evaluation["metadata_json"]["reauthentication_expected"] is False
        if action: assert evaluation["approved_action"] == action
        if action == "NOTIFY_REVIEWER": assert evaluation["requires_reviewer"] is True


def test_only_admin_can_append_valid_institution_scoped_camera_policy():
    with governance_db() as db:
        seed_session(db)
        api = api_client(db, reviewer())
        assert api.put("/api/v1/admin/policy/camera-monitoring", json={"required_camera_loss_action": "PROTECT_AND_PAUSE"}).status_code == 403
        from serps_pop.identity.services import ROLE_ADMIN
        api = api_client(db, CurrentUser(user_id="ADMIN", institution_id="INST-1", roles=(ROLE_ADMIN,)))
        assert api.put("/api/v1/admin/policy/camera-monitoring", json={"required_camera_loss_action": "TERMINATE"}).status_code == 422
        first = api.put("/api/v1/admin/policy/camera-monitoring", json={"required_camera_loss_action": "PROTECT_AND_PAUSE"})
        assert first.status_code == 200, first.text
        second = api.put("/api/v1/admin/policy/camera-monitoring", json={"required_camera_loss_action": None})
        assert second.status_code == 200, second.text
        assert first.json()["policy_id"] != second.json()["policy_id"]
        assert db.get(InstitutionalPolicy, first.json()["policy_id"]).metadata_json["required_camera_loss_action"] == "PROTECT_AND_PAUSE"
        assert api.get("/api/v1/admin/policy/camera-monitoring").json()["required_camera_loss_action"] is None
        assert all(p.institution_id == "INST-1" for p in db.scalars(select(InstitutionalPolicy)))


def test_recovered_camera_pause_does_not_clear_an_independent_phone_pause(monkeypatch):
    from types import SimpleNamespace
    from serps_pop.governance.demo_policy import set_phone_protection_armed
    monkeypatch.setattr("serps_pop.config.settings.get_settings", lambda: SimpleNamespace(demo_policy_controls=True))
    with governance_db() as db:
        seed_session(db)
        now = datetime.now(timezone.utc)
        common = dict(institution_id="INST-1", session_id="SESSION-1", recommendation_id="R", policy_id="P",
                      evaluated_by="REVIEWER-1", approved_action="PROTECT_AND_PAUSE", requires_reviewer=True,
                      requires_candidate_acknowledgement=False, continue_examination=True, explanation="Test", policy_version="test")
        db.add(PolicyEvaluation(**common, evaluated_at=now, metadata_json={"phone_protection_required": True}))
        db.add(PolicyEvaluation(**common, evaluated_at=now + timedelta(seconds=1), metadata_json={
            "required_camera_loss_action": "PROTECT_AND_PAUSE", "protection_trigger": "required_camera_unavailable",
            "required_camera_condition": {"event_ids": ["OLD-LOSS"]}, "phone_protection_required": False}))
        db.commit()
        set_phone_protection_armed("SESSION-1", True)
        try:
            assert candidate_protection_state(db, db.get(Candidate, "CAND-INST-1"), "SESSION-1")["state"] == "PROTECTED"
        finally:
            set_phone_protection_armed("SESSION-1", False)


def test_latest_reviewer_continuation_does_not_reactivate_older_camera_evaluations():
    from serps_pop.governance.models import ReviewerDecision
    with governance_db() as db:
        seed_session(db)
        db.add(InstitutionalPolicy(institution_id="INST-1", metadata_json={"required_camera_loss_action": "PROTECT_AND_PAUSE"}))
        db.commit(); transition(db, "primary", "camera_disconnected")
        api = api_client(db, reviewer())
        run_chain(api, db)
        assessment, recommendation, evaluation = run_chain(api, db)
        db.add(ReviewerDecision(institution_id="INST-1", session_id="SESSION-1", reviewer_user_id="REVIEWER-1",
            assessment_id=assessment["assessment_id"], recommendation_id=recommendation["recommendation_id"],
            policy_evaluation_id=evaluation["evaluation_id"], decision="CONTINUE", rationale="Authorised operational continuation"))
        db.commit()
        assert candidate_protection_state(db, db.get(Candidate, "CAND-INST-1"), "SESSION-1")["state"] == "NORMAL"
