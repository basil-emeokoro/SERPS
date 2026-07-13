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
        return event
