from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorEnvelope(BaseModel):
    detail: str


class InstitutionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=180)
    institution_type: str = "generic"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InstitutionRead(InstitutionCreate):
    institution_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleRead(BaseModel):
    role_id: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    institution_id: str
    email: str
    full_name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=8)
    roles: list[str] = Field(default_factory=list)


class UserRead(BaseModel):
    user_id: str
    institution_id: str
    email: str
    full_name: str
    status: str
    roles: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: str
    password: str
    institution_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    user_id: str
    institution_id: str
    email: str
    full_name: str
    roles: list[str]


class CandidateCreate(BaseModel):
    institution_id: str | None = None
    candidate_identifier: str = Field(min_length=2, max_length=80)
    identifier_type: str = "candidate_id"
    full_name: str = Field(min_length=2, max_length=180)
    email: str
    matric_number: str | None = None
    registration_number: str | None = None
    centre_number: str | None = None
    candidate_number: str | None = None
    programme: str | None = None
    department: str | None = None
    profile_metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    status: str | None = None
    programme: str | None = None
    department: str | None = None
    profile_metadata: dict[str, Any] | None = None


class CandidateRead(BaseModel):
    candidate_id: str
    institution_id: str
    candidate_identifier: str
    identifier_type: str
    full_name: str
    email: str
    status: str
    matric_number: str | None = None
    registration_number: str | None = None
    centre_number: str | None = None
    candidate_number: str | None = None
    programme: str | None = None
    department: str | None = None
    profile_metadata: dict[str, Any]

    model_config = {"from_attributes": True}


class ExaminationCreate(BaseModel):
    institution_id: str | None = None
    exam_code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    status: str = "draft"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    duration_minutes: int = Field(default=120, ge=1)
    monitoring_mode: str = Field(default="A", pattern="^[ABC]$")
    policy_profile: str = "generic"


class ExaminationRead(BaseModel):
    examination_id: str
    institution_id: str
    exam_code: str
    title: str
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    duration_minutes: int
    monitoring_mode: str
    policy_profile: str
    is_active: bool

    model_config = {"from_attributes": True}


class AssignmentCreate(BaseModel):
    candidate_id: str
    examination_id: str


class AssignmentRead(BaseModel):
    assignment_id: str
    institution_id: str
    candidate_id: str
    examination_id: str
    status: str

    model_config = {"from_attributes": True}


class ExaminationSessionCreate(BaseModel):
    assignment_id: str
    deployment_mode: str = Field(default="A", pattern="^[ABC]$")


class ExaminationSessionTransition(BaseModel):
    status: str


class ExaminationSessionRead(BaseModel):
    session_id: str
    institution_id: str
    candidate_id: str
    examination_id: str
    assignment_id: str | None
    status: str
    deployment_mode: str
    authentication_gate_status: str
    device_check_status: str
    monitoring_status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    audit_id: str
    institution_id: str | None
    actor_user_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    result: str
    metadata_json: dict[str, Any]
    timestamp: datetime

    model_config = {"from_attributes": True}
