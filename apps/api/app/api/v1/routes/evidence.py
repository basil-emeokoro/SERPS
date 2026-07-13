from fastapi import APIRouter, status

from serps_pop.domain.evidence import EvidenceEvent, EvidenceEventCreate

router = APIRouter()


@router.post("/", response_model=EvidenceEvent, status_code=status.HTTP_201_CREATED)
def create_evidence_event(payload: EvidenceEventCreate) -> EvidenceEvent:
    """Accept a structured evidence event.

    Sprint 1 validates the API contract and domain schema. Repository-backed
    persistence is wired through SQLAlchemy models and will be enabled in the
    next migration sprint.
    """
    return EvidenceEvent.from_create(payload)
