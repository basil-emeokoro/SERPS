from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

AdvisoryAction = Literal[
    "CONTINUE_MONITORING",
    "REQUEST_REAUTHENTICATION",
    "NOTIFY_REVIEWER",
    "REQUEST_CANDIDATE_ACKNOWLEDGEMENT",
    "ESCALATE_INCIDENT",
]
ReviewerDecisionValue = Literal[
    "CONTINUE",
    "REQUEST_REAUTHENTICATION",
    "ACKNOWLEDGE",
    "ESCALATE",
    "REQUEST_MORE_EVIDENCE",
]


class AssessmentCreate(BaseModel):
    window_seconds: int = Field(default=60, ge=1, le=3600)


class ContextualAssessmentRead(BaseModel):
    assessment_id: str
    institution_id: str
    session_id: str
    candidate_id: str
    created_by: str
    calculated_at: datetime
    risk_score: float
    risk_level: str
    confidence: float
    explanation: str
    evidence_window_start: datetime | None
    evidence_window_end: datetime | None
    evidence_event_ids: list[str]
    rule_version: str
    status: str
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class AgentRecommendationRead(BaseModel):
    recommendation_id: str
    institution_id: str
    session_id: str
    assessment_id: str
    created_by: str
    created_at: datetime
    recommended_action: AdvisoryAction
    priority: str
    confidence: float
    explanation: str
    requires_reviewer: bool
    status: str
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class PolicyEvaluationRead(BaseModel):
    evaluation_id: str
    institution_id: str
    session_id: str
    recommendation_id: str
    policy_id: str
    evaluated_by: str
    evaluated_at: datetime
    approved_action: AdvisoryAction
    requires_reviewer: bool
    requires_candidate_acknowledgement: bool
    continue_examination: bool
    explanation: str
    policy_version: str
    status: str
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class ReviewerDecisionCreate(BaseModel):
    assessment_id: str
    recommendation_id: str
    policy_evaluation_id: str
    decision: ReviewerDecisionValue
    rationale: str = Field(min_length=1, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("rationale")
    @classmethod
    def rationale_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reviewer rationale is required.")
        return value


class ReviewerDecisionRead(BaseModel):
    decision_id: str
    institution_id: str
    session_id: str
    reviewer_user_id: str
    assessment_id: str
    recommendation_id: str
    policy_evaluation_id: str
    decision: ReviewerDecisionValue
    rationale: str
    created_at: datetime
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class ReviewerQueueItem(BaseModel):
    session_id: str
    institution_id: str
    candidate_id: str
    candidate_name: str
    examination_id: str
    examination: str
    session_status: str
    latest_risk_score: float | None
    latest_risk_level: str | None
    latest_evidence: dict[str, Any] | None
    assessment_explanation: str | None
    agent_recommendation: str | None
    policy_outcome: str | None
    review_status: str


class TimelineEntry(BaseModel):
    entry_type: str
    entity_id: str
    timestamp: datetime
    payload: dict[str, Any]


class SessionReportRead(BaseModel):
    report_id: str
    institution_id: str
    session_id: str
    generated_at: datetime
    generated_by: str
    report_version: str
    summary: str
    report_payload: dict[str, Any]

    model_config = {"from_attributes": True}
