from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from serps_pop.infrastructure.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RegistrationRequest(Base):
    __tablename__ = "registration_requests"
    __table_args__ = (
        Index("ix_registration_institution_status", "institution_id", "status"),
        UniqueConstraint("institution_id", "email", "account_type", name="uq_registration_identity_type"),
    )

    registration_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    candidate_identifier: Mapped[str | None] = mapped_column(String(80), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending_verification")
    prototype_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    configured_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    configuration_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0")
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending_verification")


class IdentityAssuranceProfile(Base):
    __tablename__ = "identity_assurance_profiles"

    profile_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    registration_id: Mapped[str | None] = mapped_column(ForeignKey("registration_requests.registration_id"), nullable=True)
    biometric_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    demo_bypass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enrolment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_enrolled")
    authentication_result: Mapped[str] = mapped_column(String(30), nullable=False, default="not_verified")
    identity_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    liveness_result: Mapped[str] = mapped_column(String(30), nullable=False, default="not_tested")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class BiometricEnrollment(Base):
    __tablename__ = "biometric_enrollments"
    __table_args__ = (Index("ix_biometric_enrollment_user_status", "user_id", "status"),)

    enrollment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    representation_json: Mapped[list] = mapped_column(JSON, nullable=False)
    representation_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    capture_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    capture_count: Mapped[int] = mapped_column(Integer, nullable=False)
    liveness_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class IdentityChallenge(Base):
    __tablename__ = "identity_challenges"
    __table_args__ = (Index("ix_identity_challenge_user_purpose", "user_id", "purpose", "created_at"),)

    challenge_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    required_actions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
