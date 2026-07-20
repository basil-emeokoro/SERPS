from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from serps_pop.infrastructure.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CandidateConsent(Base):
    __tablename__ = "candidate_consents"
    __table_args__ = (
        Index("ix_candidate_consents_institution_candidate", "institution_id", "candidate_id"),
        Index("ix_candidate_consents_candidate_timestamp", "candidate_id", "accepted_at"),
    )

    consent_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    consent_version: Mapped[str] = mapped_column(String(40), nullable=False)
    monitoring_consent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    privacy_notice_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    institutional_policy_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class DeviceCheckRecord(Base):
    __tablename__ = "device_check_records"
    __table_args__ = (
        Index("ix_device_checks_institution_candidate", "institution_id", "candidate_id"),
        Index("ix_device_checks_candidate_checked", "candidate_id", "checked_at"),
        Index("ix_device_checks_passed", "passed"),
    )

    device_check_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    supported_browser: Mapped[bool] = mapped_column(Boolean, nullable=False)
    secure_context: Mapped[bool] = mapped_column(Boolean, nullable=False)
    camera_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    microphone_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    browser_name: Mapped[str] = mapped_column(String(80), nullable=False)
    browser_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class CameraSelectionRecord(Base):
    __tablename__ = "camera_selection_records"
    __table_args__ = (
        CheckConstraint("camera_count >= 1", name="camera_count_positive"),
        Index("ix_camera_selections_institution_candidate", "institution_id", "candidate_id"),
        Index("ix_camera_selections_candidate_selected", "candidate_id", "selected_at"),
    )

    camera_selection_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    camera_count: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class CameraPermissionRecord(Base):
    __tablename__ = "camera_permission_records"
    __table_args__ = (
        Index("ix_camera_permissions_institution_candidate", "institution_id", "candidate_id"),
        Index("ix_camera_permissions_candidate_checked", "candidate_id", "checked_at"),
        Index("ix_camera_permissions_status", "status"),
    )

    camera_permission_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


IMMUTABLE_MODELS = (CandidateConsent, DeviceCheckRecord, CameraSelectionRecord, CameraPermissionRecord)


def _reject_mutation(_mapper: object, _connection: object, target: object) -> None:
    raise ValueError(f"{type(target).__name__} records are append-only.")


for _model in IMMUTABLE_MODELS:
    event.listen(_model, "before_update", _reject_mutation)
    event.listen(_model, "before_delete", _reject_mutation)
