from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


AccountType = Literal["candidate", "reviewer", "administrator"]


class RegistrationCreate(BaseModel):
    institution_code: str = Field(min_length=2, max_length=32)
    account_type: AccountType
    email: str
    full_name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)
    candidate_identifier: str | None = Field(default=None, max_length=80)
    biometric_consent: bool = False
    configuration_version: str = Field(min_length=1, max_length=30)
    configured_fields: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if self.account_type == "candidate" and not self.candidate_identifier and not self.configured_fields:
            raise ValueError("Institution-configured candidate fields are required.")
        if self.account_type == "candidate" and not self.biometric_consent:
            raise ValueError("Biometric processing consent is required for candidate registration.")
        return self


class RegistrationRead(BaseModel):
    registration_id: str
    account_type: str
    email: str
    status: str
    prototype_verified: bool
    requested_at: datetime
    enrollment_token: str | None = None
    required_actions: list[str] = Field(default_factory=list)
    institution_code: str | None = None
    configuration_version: str = "1.0"
    configured_fields: dict[str, Any] = Field(default_factory=dict)
    verification_status: str = "pending_verification"


class EnrollmentResumeCreate(BaseModel):
    institution_code: str = Field(min_length=2, max_length=32)
    email: str
    password: str = Field(min_length=12, max_length=128)


class RegistrationFieldRead(BaseModel):
    name: str
    label: str
    type: Literal["text", "email", "number", "date", "select", "checkbox"]
    required: bool = False
    placeholder: str = ""
    pattern: str | None = None
    help_text: str = ""
    order: int = 0
    active: bool = True
    options: list[str] = Field(default_factory=list)
    applies_to: list[AccountType] = Field(default_factory=lambda: ["candidate"])


class InstitutionRegistrationRead(BaseModel):
    code: str
    name: str
    version: str
    enabled: bool
    candidate_identifier_field: str | None = None
    fields: list[RegistrationFieldRead]


class RegistrationDecision(BaseModel):
    decision: Literal["approve", "reject"]
    rationale: str = Field(min_length=8, max_length=1000)


class FaceCapture(BaseModel):
    pose: Literal["forward", "left", "right", "up", "down", "centre_confirmation"]
    descriptor: list[float] = Field(min_length=16, max_length=128)
    one_face: bool
    pose_validated: bool
    lighting_score: float = Field(ge=0, le=1)
    distance_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class LivenessAction(BaseModel):
    action: str
    completed: bool
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime


class EnrollmentSubmit(BaseModel):
    enrollment_token: str
    captures: list[FaceCapture] = Field(min_length=6, max_length=6)
    liveness_actions: list[LivenessAction] = Field(min_length=3, max_length=8)
    retry_count: int = Field(default=0, ge=0, le=20)


class ChallengeRead(BaseModel):
    challenge_id: str
    challenge_token: str
    purpose: str
    required_actions: list[str]
    expires_at: datetime


class FaceAuthenticationSubmit(BaseModel):
    challenge_token: str
    descriptor: list[float] = Field(min_length=16, max_length=128)
    one_face: bool
    lighting_score: float = Field(ge=0, le=1)
    distance_score: float = Field(ge=0, le=1)
    liveness_actions: list[LivenessAction] = Field(min_length=3, max_length=8)
    retry_count: int = Field(default=0, ge=0, le=20)


class IdentityStatusRead(BaseModel):
    user_id: str
    biometric_required: bool
    demo_bypass: bool
    enrolment_status: str
    authentication_result: str
    identity_confidence: float | None
    liveness_result: str
    last_verified_at: datetime | None
