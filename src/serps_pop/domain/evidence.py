from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class RiskLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceEventCreate(BaseModel):
    session_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    source_module: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    risk_weight: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = Field(min_length=1)
    camera_id: str | None = None
    evidence_path: str | None = None

    @field_validator("event_type", "source_module")
    @classmethod
    def normalise_token(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")


class EvidenceEvent(EvidenceEventCreate):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid4().hex[:8].upper()}")
    timestamp: datetime = Field(default_factory=utc_now)

    def risk_points(self) -> int:
        return round(
            max(0.0, min(self.risk_weight, 1.0))
            * max(0.0, min(self.confidence, 1.0))
            * 100
        )

    @classmethod
    def from_create(cls, payload: EvidenceEventCreate) -> "EvidenceEvent":
        return cls(**payload.model_dump())
