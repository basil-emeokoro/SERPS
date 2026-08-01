from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CandidateRegistrationCreate(BaseModel):
    institution_code: str = Field(min_length=2, max_length=32)
    candidate_identifier: str = Field(min_length=2, max_length=80)
    identifier_type: str = Field(default="candidate_id", max_length=40)
    full_name: str = Field(min_length=2, max_length=180)
    email: str
    password: str = Field(min_length=8, max_length=256)
    matric_number: str | None = Field(default=None, max_length=80)
    registration_number: str | None = Field(default=None, max_length=120)
    programme: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)


class CandidateRegistrationRead(BaseModel):
    candidate_id: str
    user_id: str
    institution_id: str
    candidate_identifier: str
    full_name: str
    email: str
    status: str

    model_config = {"from_attributes": True}


class AssignedExaminationRead(BaseModel):
    assignment_id: str
    assignment_status: str
    examination_id: str
    exam_code: str
    title: str
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    duration_minutes: int
    monitoring_mode: str


class ConsentCreate(BaseModel):
    consent_version: str = Field(default="CONSENT-1.0", min_length=1, max_length=40)
    monitoring_consent: bool
    privacy_notice_accepted: bool
    institutional_policy_accepted: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsentRead(BaseModel):
    consent_id: str
    institution_id: str
    candidate_id: str
    user_id: str
    consent_version: str
    monitoring_consent: bool
    privacy_notice_accepted: bool
    institutional_policy_accepted: bool
    accepted: bool
    accepted_at: datetime
    ip_address: str | None
    user_agent: str | None
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class DeviceCheckCreate(BaseModel):
    model_config = {"extra": "forbid"}

    attestation_source: Literal["candidate_browser"] = "candidate_browser"
    supported_browser: bool
    secure_context: bool
    camera_available: bool
    microphone_available: bool
    browser_name: str = Field(min_length=1, max_length=80)
    browser_version: str | None = Field(default=None, max_length=40)
    operating_system: str | None = Field(default=None, max_length=120)
    user_agent: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceCheckRead(BaseModel):
    device_check_id: str
    institution_id: str
    candidate_id: str
    supported_browser: bool
    secure_context: bool
    camera_available: bool
    microphone_available: bool
    browser_name: str
    browser_version: str | None
    operating_system: str | None
    passed: bool
    checked_at: datetime
    user_agent: str | None
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class CameraSelectionCreate(BaseModel):
    model_config = {"extra": "forbid"}

    attestation_source: Literal["candidate_browser"] = "candidate_browser"
    camera_role: Literal["primary", "secondary"]
    device_id: str = Field(min_length=1, max_length=255)
    label: str | None = Field(default=None, max_length=255)
    group_id: str | None = Field(default=None, max_length=255)
    camera_count: int = Field(ge=1, le=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CameraSelectionRead(BaseModel):
    camera_selection_id: str
    institution_id: str
    candidate_id: str
    camera_role: str
    device_id: str
    label: str | None
    group_id: str | None
    camera_count: int
    selected_at: datetime
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class CameraPermissionCreate(BaseModel):
    model_config = {"extra": "forbid"}

    attestation_source: Literal["candidate_browser"] = "candidate_browser"
    camera_role: Literal["primary", "secondary"]
    status: Literal["granted", "denied", "prompt", "unavailable"]
    user_agent: str | None = Field(default=None, max_length=2048)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CameraPermissionRead(BaseModel):
    camera_permission_id: str
    institution_id: str
    candidate_id: str
    camera_role: str
    status: str
    granted: bool
    checked_at: datetime
    user_agent: str | None
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class CandidateSessionStart(BaseModel):
    deployment_mode: str = Field(default="A", pattern="^[ABC]$")


class CandidateSessionRead(BaseModel):
    session_id: str
    institution_id: str
    candidate_id: str
    examination_id: str
    assignment_id: str
    consent_id: str
    device_check_id: str
    camera_selection_id: str
    camera_permission_id: str
    secondary_camera_selection_id: str
    secondary_camera_permission_id: str
    status: str
    deployment_mode: str
    authentication_gate_status: str
    device_check_status: str
    monitoring_status: str
    started_at: datetime

    model_config = {"from_attributes": True}


class CandidateDashboardRead(BaseModel):
    candidate: dict[str, Any]
    assigned_examinations: list[AssignedExaminationRead]
    consent: ConsentRead | None
    device_check: DeviceCheckRead | None
    primary_camera_selection: CameraSelectionRead | None
    primary_camera_permission: CameraPermissionRead | None
    secondary_camera_selection: CameraSelectionRead | None
    secondary_camera_permission: CameraPermissionRead | None
    active_session: CandidateSessionRead | None
    readiness: dict[str, bool]


class CandidateWorkspaceRead(BaseModel):
    candidate: dict[str, Any]
    institution: dict[str, Any]
    examination: dict[str, Any]
    session: CandidateSessionRead
    consent: ConsentRead
    device_check: DeviceCheckRead
    primary_camera: CameraSelectionRead
    primary_permission: CameraPermissionRead
    secondary_camera: CameraSelectionRead
    secondary_permission: CameraPermissionRead
