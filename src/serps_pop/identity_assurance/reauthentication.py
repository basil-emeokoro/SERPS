"""Policy-scoped examination identity assurance; no detector makes an identity decision.

Requirements reuse IdentityChallenge and its metadata. All mutations serialize on
an existing examination-session row (also on SQLite); governance records remain
append-only. Tokens are reproducible HMACs, persisted only as hashes, so a lost
HTTP response never requires issuing a duplicate challenge.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from serps_pop.config.settings import get_settings
from serps_pop.identity.models import Candidate, ExaminationSession
from serps_pop.identity.services import DomainConflict, DomainNotFound
from serps_pop.identity_assurance.models import IdentityChallenge, new_uuid, utc_now
from serps_pop.identity_assurance.services import _token_hash, profile_for_user, verify_facial_authentication

PURPOSE = "examination"
RESOLVED = {"completed", "released"}


class IdentityReauthenticationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    sustained_absence_reappearance: bool = True
    minimum_sustained_absence_events: int = Field(default=1, ge=1, le=20)
    additional_persons: bool = True
    minimum_additional_person_events: int = Field(default=2, ge=2, le=20)
    minimum_confidence: float = Field(default=0.7, ge=0, le=1)
    cooldown_seconds: int = Field(default=300, ge=30, le=3600)
    retry_cooldown_seconds: int = Field(default=30, ge=5, le=300)
    maximum_attempts: int = Field(default=3, ge=1, le=5)
    challenge_lifetime_seconds: int = Field(default=600, ge=60, le=1800)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def configured_policy(policy) -> IdentityReauthenticationPolicy:
    return IdentityReauthenticationPolicy.model_validate(policy.metadata_json.get("identity_reauthentication", {}))


def identity_conditions(assessment, policy) -> list[str]:
    config = configured_policy(policy)
    if not config.enabled:
        return []
    context = assessment.metadata_json.get("identity_context", {})
    conditions = []
    recovered = context.get("sustained_absence_reappearance", {})
    persons = context.get("additional_persons", {})
    if (config.sustained_absence_reappearance
            and recovered.get("count", 0) >= config.minimum_sustained_absence_events
            and recovered.get("confidence", 0) >= config.minimum_confidence):
        conditions.append("sustained_absence_reappearance")
    if (config.additional_persons and persons.get("count", 0) >= config.minimum_additional_person_events
            and persons.get("confidence", 0) >= config.minimum_confidence):
        conditions.append("additional_persons")
    return conditions


def lock_session(db: Session, session_id: str) -> None:
    # An unchanged value takes a write lock without changing session state or timestamps.
    db.execute(update(ExaminationSession).where(ExaminationSession.session_id == session_id)
               .values(updated_at=ExaminationSession.updated_at).execution_options(synchronize_session=False))


def candidate_session(db: Session, session_id: str, user_id: str, institution_id: str):
    session = db.get(ExaminationSession, session_id, populate_existing=True)
    candidate = db.get(Candidate, session.candidate_id) if session else None
    if (not session or not candidate or session.institution_id != institution_id
            or candidate.institution_id != institution_id or candidate.user_id != user_id):
        raise DomainNotFound("Examination session not found for this candidate.")
    if session.status != "active":
        raise DomainConflict("Identity assurance requires the originating active examination session.")
    return session


def latest_requirement(db: Session, session_id: str):
    return db.scalar(select(IdentityChallenge).where(
        IdentityChallenge.purpose == PURPOSE,
        IdentityChallenge.metadata_json["session_id"].as_string() == session_id,
    ).order_by(IdentityChallenge.created_at.desc(), IdentityChallenge.challenge_id.desc())
      .limit(1).execution_options(populate_existing=True))


def audit_result(db, challenge, actor_id, action, **details):
    from serps_pop.governance.services import _append_audit
    meta = challenge.metadata_json
    _append_audit(db, institution_id=meta["institution_id"], session_id=meta["session_id"],
                  actor_id=actor_id, action=action, entity_type="IdentityChallenge",
                  entity_id=challenge.challenge_id, previous_entity_id=meta["policy_evaluation_id"],
                  details={"candidate_id": meta["candidate_id"], "policy_evaluation_id": meta["policy_evaluation_id"],
                           "state": challenge.status, "misconduct_determination": False,
                           "raw_media_stored": False, **details})


def require_from_evaluation(db, evaluation, assessment, policy):
    conditions = evaluation.metadata_json.get("identity_conditions", [])
    if not conditions:
        return None
    session = db.get(ExaminationSession, evaluation.session_id)
    candidate = db.get(Candidate, session.candidate_id) if session else None
    if not session or session.status != "active" or not candidate or not candidate.user_id:
        return None
    profile = profile_for_user(db, candidate.user_id)
    if not profile or not profile.biometric_required or profile.demo_bypass:
        return None
    lock_session(db, session.session_id)
    previous = latest_requirement(db, session.session_id)
    config = configured_policy(policy)
    now = utc_now()
    if previous:
        if previous.status not in RESOLVED:
            return previous
        resolved_at = aware(previous.completed_at)
        if now < resolved_at + timedelta(seconds=previous.metadata_json["policy"]["cooldown_seconds"]):
            return None
        # Old evidence cannot be recycled once the cooldown expires.
        contexts = assessment.metadata_json["identity_context"]
        conditions = [name for name in conditions
                      if aware(datetime.fromisoformat(contexts[name]["first_event_at"])) > resolved_at]
        if not conditions:
            return None
    challenge = IdentityChallenge(challenge_id=new_uuid(), user_id=candidate.user_id,
        purpose=PURPOSE, token_hash=_token_hash(new_uuid()), required_actions=[], status="required",
        expires_at=now, metadata_json={"session_id": session.session_id,
            "institution_id": session.institution_id, "candidate_id": candidate.candidate_id,
            "examination_id": session.examination_id, "policy_evaluation_id": evaluation.evaluation_id,
            "assessment_id": assessment.assessment_id, "recommendation_id": evaluation.recommendation_id,
            "policy_id": policy.policy_id, "policy": config.model_dump(), "conditions": conditions,
            "attempts": 0, "generation": 0, "submissions": 0})
    db.add(challenge)
    db.flush()
    audit_result(db, challenge, evaluation.evaluated_by, "IDENTITY_REAUTHENTICATION_REQUIRED", conditions=conditions)
    return challenge


def state(challenge, session_id: str):
    if challenge is None:
        return {"session_id": session_id, "state": "not_required", "required": False}
    meta = challenge.metadata_json
    status = challenge.status
    if status == "pending" and aware(challenge.expires_at) <= utc_now():
        status = "expired"
    return {"session_id": session_id, "requirement_id": challenge.challenge_id,
            "state": status, "required": status not in RESOLVED,
            "policy_evaluation_id": meta["policy_evaluation_id"], "assessment_id": meta["assessment_id"],
            "recommendation_id": meta["recommendation_id"], "conditions": meta["conditions"],
            "attempts": meta["attempts"], "retry_after": meta.get("retry_after"),
            "maximum_attempts": meta["policy"]["maximum_attempts"],
            "expires_at": aware(challenge.expires_at).isoformat(),
            "outcome": meta.get("outcome"), "identity_confidence": challenge.confidence,
            "return_path": f"/candidate/examinations/{session_id}", "misconduct_determination": False}


def challenge_token(challenge):
    message = f"serps:examination-reauth:{challenge.challenge_id}:{challenge.metadata_json['generation']}"
    return hmac.new(get_settings().jwt_secret.get_secret_value().encode(), message.encode(), hashlib.sha256).hexdigest()


def begin(db: Session, session_id: str, user_id: str, institution_id: str):
    candidate_session(db, session_id, user_id, institution_id)
    lock_session(db, session_id)
    candidate_session(db, session_id, user_id, institution_id)
    challenge = latest_requirement(db, session_id)
    if not challenge or challenge.status in RESOLVED:
        return state(challenge, session_id)
    meta = dict(challenge.metadata_json)
    config = IdentityReauthenticationPolicy.model_validate(meta["policy"])
    now = utc_now()
    if challenge.status == "manual_review":
        return state(challenge, session_id)
    if meta.get("retry_after") and now < datetime.fromisoformat(meta["retry_after"]):
        return state(challenge, session_id)
    if challenge.status != "pending" or aware(challenge.expires_at) <= now:
        if meta["attempts"] >= config.maximum_attempts:
            challenge.status = "manual_review"
            audit_result(db, challenge, user_id, "IDENTITY_REAUTHENTICATION_REVIEW_REQUIRED", reason="attempt_limit")
            db.flush()
            return state(challenge, session_id)
        meta.update(attempts=meta["attempts"] + 1, generation=meta["generation"] + 1, retry_after=None)
        challenge.metadata_json = meta
        challenge.status = "pending"
        challenge.expires_at = now + timedelta(seconds=config.challenge_lifetime_seconds)
        challenge.token_hash = _token_hash(challenge_token(challenge))
        audit_result(db, challenge, user_id, "IDENTITY_REAUTHENTICATION_CHALLENGE_ISSUED", attempt=meta["attempts"])
        db.flush()
    return {**state(challenge, session_id), "challenge_token": challenge_token(challenge)}


def verify(db: Session, session_id: str, user_id: str, institution_id: str, payload):
    candidate_session(db, session_id, user_id, institution_id)
    lock_session(db, session_id)
    candidate_session(db, session_id, user_id, institution_id)
    challenge = latest_requirement(db, session_id)
    if not challenge or challenge.user_id != user_id or not hmac.compare_digest(challenge.token_hash, _token_hash(payload.challenge_token)):
        raise DomainNotFound("Challenge does not belong to the active session requirement. Refresh identity status.")
    if challenge.status != "pending":
        return state(challenge, session_id)  # Lost-response replay returns the recorded result, never re-compares.
    if aware(challenge.expires_at) <= utc_now():
        challenge.status = "expired"
        audit_result(db, challenge, user_id, "IDENTITY_REAUTHENTICATION_CHALLENGE_EXPIRED")
        db.flush()
        return state(challenge, session_id)
    meta = dict(challenge.metadata_json)
    config = IdentityReauthenticationPolicy.model_validate(meta["policy"])
    _, confidence, outcome = verify_facial_authentication(db, payload, purpose=PURPOSE)
    meta.update(outcome=outcome, submissions=meta["submissions"] + 1,
                observation_count=0 if outcome == "Retry Required" else 1,
                quality_validated=outcome != "Retry Required", raw_media_stored=False)
    challenge.metadata_json = meta
    if outcome == "Verified":
        challenge.completed_at = utc_now()
    elif outcome == "Manual Review" or meta["submissions"] >= config.maximum_attempts:
        challenge.status = "manual_review"
    else:
        # A quality failure or failed match can have only a bounded, fresh attempt.
        challenge.status = "failed"
        meta["retry_after"] = (utc_now() + timedelta(seconds=config.retry_cooldown_seconds)).isoformat()
        challenge.metadata_json = dict(meta)
    audit_result(db, challenge, user_id, "IDENTITY_REAUTHENTICATION_RESULT", outcome=outcome, confidence=confidence)
    db.flush()
    return state(challenge, session_id)


def apply_reviewer_decision(db, decision):
    lock_session(db, decision.session_id)
    challenge = latest_requirement(db, decision.session_id)
    if not challenge or challenge.status in RESOLVED or challenge.metadata_json["policy_evaluation_id"] != decision.policy_evaluation_id:
        return
    if decision.decision == "CONTINUE":
        challenge.status = "released"
        challenge.completed_at = utc_now()
    elif decision.decision == "REQUEST_REAUTHENTICATION":
        meta = dict(challenge.metadata_json)
        meta.update(attempts=0, submissions=0,
                    retry_after=(utc_now() + timedelta(seconds=meta["policy"]["retry_cooldown_seconds"])).isoformat())
        challenge.metadata_json = meta
        challenge.status = "required"
    elif decision.decision in {"ESCALATE", "REQUEST_MORE_EVIDENCE"}:
        challenge.status = "manual_review"
    else:
        return  # Acknowledgement alone never clears an identity requirement.
    audit_result(db, challenge, decision.reviewer_user_id, "IDENTITY_REAUTHENTICATION_REVIEWER_RECOVERY",
                 decision=decision.decision, decision_id=decision.decision_id)
    db.flush()
