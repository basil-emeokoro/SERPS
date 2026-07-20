from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from serps_pop.identity.models import AuditLog
from serps_pop.identity.services import audit
from serps_pop.infrastructure.database import Base


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def create_audit_record(db: Session) -> str:
    record = audit(
        db,
        action="security.audit.created",
        result="success",
        institution_id=None,
        metadata={"source": "pytest"},
    )
    db.commit()
    return record.audit_id


def test_audit_creation_and_historical_retrieval_succeed(db: Session):
    audit_id = create_audit_record(db)

    stored = db.scalar(select(AuditLog).where(AuditLog.audit_id == audit_id))

    assert stored is not None
    assert stored.action == "security.audit.created"
    assert stored.metadata_json == {"source": "pytest"}


def test_audit_update_is_rejected_and_history_remains(db: Session):
    audit_id = create_audit_record(db)
    stored = db.get(AuditLog, audit_id)
    stored.result = "altered"

    with pytest.raises(ValueError, match="append-only"):
        db.flush()
    db.rollback()

    assert db.get(AuditLog, audit_id).result == "success"


def test_audit_delete_is_rejected_and_history_remains(db: Session):
    audit_id = create_audit_record(db)
    stored = db.get(AuditLog, audit_id)
    db.delete(stored)

    with pytest.raises(ValueError, match="append-only"):
        db.flush()
    db.rollback()

    assert db.get(AuditLog, audit_id) is not None


def test_audit_replacement_is_rejected(db: Session):
    audit_id = create_audit_record(db)
    replacement = AuditLog(
        audit_id=audit_id,
        action="security.audit.replaced",
        result="success",
        metadata_json={},
    )
    db.merge(replacement)

    with pytest.raises(ValueError, match="append-only"):
        db.flush()
    db.rollback()

    assert db.get(AuditLog, audit_id).action == "security.audit.created"
