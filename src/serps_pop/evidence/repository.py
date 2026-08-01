from sqlalchemy import select
from sqlalchemy.orm import Session

from serps_pop.domain.evidence import EvidenceEvent
from serps_pop.evidence.models import EvidenceEventRecord


class EvidenceEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: EvidenceEvent) -> EvidenceEvent:
        record = EvidenceEventRecord(**event.model_dump())
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def list_by_session(self, session_id: str) -> list[EvidenceEvent]:
        records = self.session.scalars(
            select(EvidenceEventRecord)
            .where(EvidenceEventRecord.session_id == session_id)
            .order_by(EvidenceEventRecord.timestamp.asc(), EvidenceEventRecord.event_id.asc())
        ).all()
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(record: EvidenceEventRecord) -> EvidenceEvent:
        return EvidenceEvent(
            event_id=record.event_id,
            session_id=record.session_id,
            candidate_id=record.candidate_id,
            timestamp=record.timestamp,
            source_module=record.source_module,
            event_type=record.event_type,
            risk_weight=record.risk_weight,
            confidence=record.confidence,
            camera_id=record.camera_id,
            evidence_path=record.evidence_path,
            description=record.description,
            metadata_json=record.metadata_json,
        )
