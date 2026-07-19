from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from serps_pop.domain.evidence import EvidenceEvent, EvidenceEventCreate
from serps_pop.evidence.repository import EvidenceEventRepository
from serps_pop.identity.models import ExaminationSession
from serps_pop.identity.services import ROLE_SYSADMIN


class EvidenceSessionNotFound(Exception):
    pass


class EvidenceAccessDenied(Exception):
    pass


class EvidenceCandidateMismatch(Exception):
    pass


def _role_set(roles: Iterable[str]) -> set[str]:
    return set(roles)


def get_session_for_evidence(
    db: Session,
    session_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> ExaminationSession:
    examination_session = db.get(ExaminationSession, session_id)
    if examination_session is None:
        raise EvidenceSessionNotFound(session_id)
    if ROLE_SYSADMIN not in _role_set(actor_roles) and examination_session.institution_id != actor_institution_id:
        raise EvidenceAccessDenied(session_id)
    return examination_session


def create_evidence_event(
    db: Session,
    payload: EvidenceEventCreate,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> EvidenceEvent:
    examination_session = get_session_for_evidence(
        db,
        payload.session_id,
        actor_institution_id,
        actor_roles,
    )
    if examination_session.candidate_id != payload.candidate_id:
        raise EvidenceCandidateMismatch(payload.candidate_id)
    event = EvidenceEvent.from_create(payload)
    return EvidenceEventRepository(db).add(event)


def list_session_evidence_events(
    db: Session,
    session_id: str,
    actor_institution_id: str,
    actor_roles: Iterable[str],
) -> list[EvidenceEvent]:
    get_session_for_evidence(db, session_id, actor_institution_id, actor_roles)
    return EvidenceEventRepository(db).list_by_session(session_id)
