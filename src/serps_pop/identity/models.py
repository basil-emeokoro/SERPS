from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from serps_pop.infrastructure.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Institution(Base):
    __tablename__ = "institutions"

    institution_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False, default="generic")
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    users: Mapped[list["User"]] = relationship(back_populates="institution")
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="institution")
    examinations: Mapped[list["Examination"]] = relationship(back_populates="institution")


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    users: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("institution_id", "email", name="uq_users_institution_email"),
        Index("ix_users_institution_status", "institution_id", "status"),
    )

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    institution: Mapped[Institution] = relationship(back_populates="users")
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)

    user_role_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship(back_populates="users")


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("institution_id", "candidate_identifier", name="uq_candidates_institution_identifier"),
        UniqueConstraint("institution_id", "email", name="uq_candidates_institution_email"),
        UniqueConstraint("institution_id", "matric_number", name="uq_candidates_institution_matric_number"),
        UniqueConstraint(
            "institution_id", "registration_number", name="uq_candidates_institution_registration_number"
        ),
        Index("ix_candidates_institution_status", "institution_id", "status"),
    )

    candidate_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True, unique=True)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_identifier: Mapped[str] = mapped_column(String(80), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate_id")
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="registered")
    matric_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    centre_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    candidate_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    programme: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    profile_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    institution: Mapped[Institution] = relationship(back_populates="candidates")
    assignments: Mapped[list["CandidateExaminationAssignment"]] = relationship(back_populates="candidate")
    sessions: Mapped[list["ExaminationSession"]] = relationship(back_populates="candidate")


class Examination(Base):
    __tablename__ = "examinations"
    __table_args__ = (
        UniqueConstraint("institution_id", "exam_code", name="uq_examinations_institution_exam_code"),
        Index("ix_examinations_institution_status", "institution_id", "status"),
    )

    examination_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    exam_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    monitoring_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    policy_profile: Mapped[str] = mapped_column(String(80), nullable=False, default="generic")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    institution: Mapped[Institution] = relationship(back_populates="examinations")
    assignments: Mapped[list["CandidateExaminationAssignment"]] = relationship(back_populates="examination")
    sessions: Mapped[list["ExaminationSession"]] = relationship(back_populates="examination")


class CandidateExaminationAssignment(Base):
    __tablename__ = "candidate_examination_assignments"
    __table_args__ = (
        UniqueConstraint("candidate_id", "examination_id", name="uq_candidate_exam_assignment"),
        Index("ix_assignments_institution_status", "institution_id", "status"),
    )

    assignment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    examination_id: Mapped[str] = mapped_column(ForeignKey("examinations.examination_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="eligible")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    candidate: Mapped[Candidate] = relationship(back_populates="assignments")
    examination: Mapped[Examination] = relationship(back_populates="assignments")


class ExaminationSession(Base):
    __tablename__ = "examination_sessions"
    __table_args__ = (
        Index("ix_examination_sessions_institution_status", "institution_id", "status"),
        Index("ix_examination_sessions_candidate_status", "candidate_id", "status"),
    )

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    examination_id: Mapped[str] = mapped_column(ForeignKey("examinations.examination_id"), nullable=False)
    assignment_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidate_examination_assignments.assignment_id"), nullable=True
    )
    consent_id: Mapped[str | None] = mapped_column(ForeignKey("candidate_consents.consent_id"), nullable=True)
    device_check_id: Mapped[str | None] = mapped_column(ForeignKey("device_check_records.device_check_id"), nullable=True)
    camera_selection_id: Mapped[str | None] = mapped_column(
        ForeignKey("camera_selection_records.camera_selection_id"), nullable=True
    )
    camera_permission_id: Mapped[str | None] = mapped_column(
        ForeignKey("camera_permission_records.camera_permission_id"), nullable=True
    )
    secondary_camera_selection_id: Mapped[str | None] = mapped_column(
        ForeignKey("camera_selection_records.camera_selection_id"), nullable=True
    )
    secondary_camera_permission_id: Mapped[str | None] = mapped_column(
        ForeignKey("camera_permission_records.camera_permission_id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="authentication_pending")
    deployment_mode: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    authentication_gate_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    device_check_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    monitoring_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_started")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    candidate: Mapped[Candidate] = relationship(back_populates="sessions")
    examination: Mapped[Examination] = relationship(back_populates="sessions")


class AuthenticationSession(Base):
    __tablename__ = "authentication_sessions"

    authentication_session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    candidate_id: Mapped[str | None] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_token_hash", "token_hash"),)

    refresh_token_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    replaced_by_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_institution_timestamp", "institution_id", "timestamp"),
        Index("ix_audit_logs_action_result", "action", "result"),
    )

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str | None] = mapped_column(ForeignKey("institutions.institution_id"), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
