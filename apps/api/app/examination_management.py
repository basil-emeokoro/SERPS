from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from serps_pop.identity.models import AuditLog, Candidate, CandidateExaminationAssignment, Examination
from serps_pop.infrastructure.database import Base
from serps_pop.identity_assurance.models import IdentityAssuranceProfile


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("institution_id", "course_code", name="uq_courses_institution_course_code"),
        Index("ix_courses_institution_active", "institution_id", "is_active"),
    )
    course_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class CourseRegistration(Base):
    __tablename__ = "course_registrations"
    __table_args__ = (
        UniqueConstraint("course_id", "candidate_id", name="uq_course_registrations_course_candidate"),
        Index("ix_course_registrations_institution_status", "institution_id", "status"),
    )
    course_registration_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.institution_id"), nullable=False)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.candidate_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="registered")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ExaminationManagementCreate(BaseModel):
    institution_id: str | None = None
    exam_code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    status: Literal["draft", "published", "active", "inactive"] = "draft"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    duration_minutes: int = Field(default=120, ge=1, le=1440)
    monitoring_mode: Literal["A", "B", "C"] = "A"
    policy_profile: str = Field(default="generic", min_length=1, max_length=80)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class CourseCreate(BaseModel):
    course_code: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    is_active: bool = True


class CourseRead(BaseModel):
    course_id: str
    institution_id: str
    course_code: str
    title: str
    is_active: bool
    model_config = {"from_attributes": True}


class CourseRegistrationCreate(BaseModel):
    course_id: str
    candidate_id: str


class CourseRegistrationRead(BaseModel):
    course_registration_id: str
    institution_id: str
    course_id: str
    candidate_id: str
    status: str
    model_config = {"from_attributes": True}


class CohortAssignmentRequest(BaseModel):
    examination_id: str
    course_id: str


class CohortCandidateRead(BaseModel):
    candidate_id: str
    full_name: str
    email: str
    outcome: Literal["eligible", "already_assigned", "ineligible"]
    reason: str | None = None


class CohortPreviewRead(BaseModel):
    examination_id: str
    course_id: str
    monitoring_mode: Literal["A", "B", "C"]
    candidates: list[CohortCandidateRead]
    eligible_count: int
    already_assigned_count: int
    ineligible_count: int
    created_count: int = 0


def audit(db: Session, *, action: str, result: str, institution_id: str, actor_user_id: str, target_type: str, target_id: str, metadata: dict) -> None:
    db.add(AuditLog(institution_id=institution_id, actor_user_id=actor_user_id, action=action, result=result, target_type=target_type, target_id=target_id, metadata_json=metadata))


def candidate_is_enrolled(db: Session, candidate: Candidate) -> bool:
    if candidate.status != "active" or not candidate.user_id:
        return False
    profile = db.scalar(select(IdentityAssuranceProfile).where(IdentityAssuranceProfile.user_id == candidate.user_id))
    return bool(profile and profile.enrolment_status == "enrolled")


def resolve_course_cohort(db: Session, *, course_id: str, examination_id: str, institution_id: str) -> dict:
    course = db.get(Course, course_id)
    exam = db.get(Examination, examination_id)
    if not course or course.institution_id != institution_id:
        raise LookupError("Course not found in authorised institution.")
    if not exam or exam.institution_id != institution_id:
        raise LookupError("Examination not found in authorised institution.")
    if not course.is_active:
        raise ValueError("Only an active course can resolve a cohort.")
    if not exam.is_active or exam.status not in {"published", "active"}:
        raise ValueError("Only an active examination can be assigned.")
    rows = db.execute(select(CourseRegistration, Candidate).join(Candidate, Candidate.candidate_id == CourseRegistration.candidate_id).where(CourseRegistration.course_id == course_id, CourseRegistration.institution_id == institution_id, CourseRegistration.status == "registered").order_by(Candidate.full_name)).all()
    existing = set(db.scalars(select(CandidateExaminationAssignment.candidate_id).where(CandidateExaminationAssignment.examination_id == examination_id, CandidateExaminationAssignment.institution_id == institution_id)).all())
    candidates = []
    for _, candidate in rows:
        if candidate.candidate_id in existing:
            outcome, reason = "already_assigned", "Candidate already has this examination assignment."
        elif not candidate_is_enrolled(db, candidate):
            outcome, reason = "ineligible", "Candidate is not active with completed identity enrolment."
        else:
            outcome, reason = "eligible", None
        candidates.append({"candidate_id": candidate.candidate_id, "full_name": candidate.full_name, "email": candidate.email, "outcome": outcome, "reason": reason})
    return {"examination_id": examination_id, "course_id": course_id, "monitoring_mode": exam.monitoring_mode, "candidates": candidates, "eligible_count": sum(x["outcome"] == "eligible" for x in candidates), "already_assigned_count": sum(x["outcome"] == "already_assigned" for x in candidates), "ineligible_count": sum(x["outcome"] == "ineligible" for x in candidates), "created_count": 0}
