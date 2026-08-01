from __future__ import annotations

import os

from sqlalchemy import select

from serps_pop.evidence import models as evidence_models  # noqa: F401
from serps_pop.identity import models as identity_models  # noqa: F401
from serps_pop.identity.models import Candidate, CandidateExaminationAssignment, Examination, Institution, User
from serps_pop.identity.schemas import CandidateCreate, ExaminationCreate, InstitutionCreate, UserCreate
from serps_pop.identity.services import (
    ROLE_ADMIN,
    ROLE_CANDIDATE,
    ROLE_REVIEWER,
    ROLE_SYSADMIN,
    create_assignment,
    create_candidate,
    create_examination,
    create_institution,
    create_user,
    ensure_roles,
)
from serps_pop.identity_assurance import models as identity_assurance_models  # noqa: F401
from serps_pop.identity_assurance.services import create_demo_profile
from serps_pop.infrastructure.database import Base, SessionLocal, engine


def demo_password() -> str:
    password = os.getenv("SERPS_DEMO_PASSWORD")
    if not password:
        raise RuntimeError("Set SERPS_DEMO_PASSWORD before seeding demonstration users.")
    if len(password) < 12:
        raise RuntimeError("SERPS_DEMO_PASSWORD must contain at least 12 characters.")
    return password


def first_or_none(session, model, *conditions):
    stmt = select(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return session.scalars(stmt).first()


def registration_configuration(code: str) -> dict:
    common = [
        {"name": "full_name", "label": "Full name", "type": "text", "required": True, "placeholder": "Enter your full name", "help_text": "Use the name held by the institution.", "order": 20, "active": True, "applies_to": ["candidate", "reviewer", "administrator"]},
        {"name": "contact_email", "label": "Email or approved contact address", "type": "email", "required": True, "placeholder": "name@example.org", "help_text": "Used for account access; it need not be an institutional domain.", "order": 30, "active": True, "applies_to": ["candidate", "reviewer", "administrator"]},
    ]
    if code == "MIVA":
        specific = [
            {"name": "matriculation_number", "label": "Matriculation number", "type": "text", "required": True, "placeholder": "MIVA/2026/0001", "pattern": r"[A-Za-z0-9/\-]{4,40}", "help_text": "Your Miva candidate identifier.", "order": 10, "active": True, "applies_to": ["candidate"]},
            {"name": "programme", "label": "Programme or cohort", "type": "text", "required": False, "placeholder": "BSc Computer Science", "help_text": "Optional where configured by the institution.", "order": 40, "active": True, "applies_to": ["candidate"]},
        ]
        identifier = "matriculation_number"
    elif code == "WAEC":
        specific = [
            {"name": "candidate_number", "label": "Candidate number", "type": "text", "required": True, "placeholder": "1234567890", "pattern": r"[A-Za-z0-9\-]{6,20}", "help_text": "The number on the examination registration.", "order": 10, "active": True, "applies_to": ["candidate"]},
            {"name": "examination_type", "label": "Examination type", "type": "select", "required": True, "options": ["WASSCE School Candidate", "WASSCE Private Candidate"], "placeholder": "Select examination type", "help_text": "Choose the registered examination route.", "order": 12, "active": True, "applies_to": ["candidate"]},
            {"name": "examination_year", "label": "Examination year", "type": "number", "required": True, "placeholder": "2026", "pattern": r"20[0-9]{2}", "help_text": "Four-digit examination year.", "order": 14, "active": True, "applies_to": ["candidate"]},
            {"name": "centre_number", "label": "Centre number", "type": "text", "required": True, "placeholder": "1234567", "pattern": r"[A-Za-z0-9\-]{5,20}", "help_text": "Registered examination centre.", "order": 16, "active": True, "applies_to": ["candidate"]},
        ]
        identifier = "candidate_number"
    else:
        specific = [
            {"name": "candidate_identifier", "label": "Candidate identifier", "type": "text", "required": True, "placeholder": "Institution-issued identifier", "pattern": r"[A-Za-z0-9._/\-]{3,80}", "help_text": "The identifier supplied by your assessment institution.", "order": 10, "active": True, "applies_to": ["candidate"]},
            {"name": "cohort", "label": "Programme or cohort", "type": "text", "required": False, "placeholder": "Optional", "help_text": "Configured descriptive registration field.", "order": 40, "active": True, "applies_to": ["candidate"]},
        ]
        identifier = "candidate_identifier"
    return {"version": "1.0", "enabled": True, "candidate_identifier_field": identifier, "fields": specific + common}


def ensure_registration_institutions(db) -> None:
    definitions = [("MIVA", "Miva Open University", "university"), ("WAEC", "West African Examinations Council", "examination_body"), ("GENERIC", "Generic Institution", "generic")]
    for code, name, institution_type in definitions:
        institution = first_or_none(db, Institution, Institution.code == code)
        if institution is None:
            institution = Institution(code=code, name=name, institution_type=institution_type, metadata_json={}, is_active=True)
            db.add(institution)
        institution.metadata_json = {**(institution.metadata_json or {}), "registration_configuration": registration_configuration(code)}


def seed() -> None:
    password = demo_password()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        roles = ensure_roles(db)

        institution = first_or_none(db, Institution, Institution.code == "MIVA")
        if institution is None:
            institution = create_institution(
                db,
                InstitutionCreate(
                    code="MIVA",
                    name="Miva Open University",
                    institution_type="university",
                    metadata_json={"demo": True, "policy_profile": "university"},
                ),
                actor_user_id=None,
            )
        ensure_registration_institutions(db)

        sysadmin = first_or_none(db, User, User.email == "sysadmin@serps.local")
        if sysadmin is None:
            sysadmin = create_user(
                db,
                UserCreate(
                    institution_id=institution.institution_id,
                    email="sysadmin@serps.local",
                    full_name="SERPS System Administrator",
                    password=password,
                    roles=[ROLE_SYSADMIN],
                ),
                actor_user_id=None,
            )

        admin = first_or_none(db, User, User.email == "admin@miva.edu.ng")
        if admin is None:
            admin = create_user(
                db,
                UserCreate(
                    institution_id=institution.institution_id,
                    email="admin@miva.edu.ng",
                    full_name="Demo Administrator",
                    password=password,
                    roles=[ROLE_ADMIN],
                ),
                actor_user_id=sysadmin.user_id,
            )

        reviewer = first_or_none(db, User, User.email == "reviewer@miva.edu.ng")
        if reviewer is None:
            reviewer = create_user(
                db,
                UserCreate(
                    institution_id=institution.institution_id,
                    email="reviewer@miva.edu.ng",
                    full_name="Demo Reviewer Proctor",
                    password=password,
                    roles=[ROLE_REVIEWER],
                ),
                actor_user_id=sysadmin.user_id,
            )

        candidate_user = first_or_none(db, User, User.email == "candidate@miva.edu.ng")
        if candidate_user is None:
            candidate_user = create_user(
                db,
                UserCreate(
                    institution_id=institution.institution_id,
                    email="candidate@miva.edu.ng",
                    full_name="Demo Candidate",
                    password=password,
                    roles=[ROLE_CANDIDATE],
                ),
                actor_user_id=admin.user_id,
            )

        candidate = first_or_none(
            db,
            Candidate,
            Candidate.institution_id == institution.institution_id,
            Candidate.candidate_identifier == "10000001",
        )
        if candidate is None:
            candidate = create_candidate(
                db,
                CandidateCreate(
                    institution_id=institution.institution_id,
                    candidate_identifier="10000001",
                    identifier_type="student_id",
                    full_name="Demo Candidate",
                    email="candidate@miva.edu.ng",
                    matric_number="MIVA/CSC/2026/001",
                    programme="MIT Capstone Demonstration",
                    department="Computer Science",
                    profile_metadata={"demo_status": "registered_pending_face_capture"},
                ),
                institution_id=institution.institution_id,
                actor_user_id=admin.user_id,
            )
        if candidate.user_id is None:
            candidate.user_id = candidate_user.user_id
        candidate.status = "active"
        candidate.profile_metadata = {**candidate.profile_metadata, "demonstration_account": True}

        for demo_user in (sysadmin, admin, reviewer, candidate_user):
            create_demo_profile(db, demo_user.user_id)

        exam = first_or_none(db, Examination, Examination.exam_code == "SERPS-DEMO-001")
        if exam is None:
            exam = create_examination(
                db,
                ExaminationCreate(
                    institution_id=institution.institution_id,
                    exam_code="SERPS-DEMO-001",
                    title="SERPS Remote Proctoring Demo Assessment",
                    status="published",
                    duration_minutes=45,
                    monitoring_mode="B",
                    policy_profile="university",
                ),
                institution_id=institution.institution_id,
                actor_user_id=admin.user_id,
            )

        assignment = first_or_none(
            db,
            CandidateExaminationAssignment,
            CandidateExaminationAssignment.candidate_id == candidate.candidate_id,
            CandidateExaminationAssignment.examination_id == exam.examination_id,
        )
        if assignment is None:
            assignment = create_assignment(
                db,
                candidate_id=candidate.candidate_id,
                examination_id=exam.examination_id,
                institution_id=institution.institution_id,
                actor_user_id=admin.user_id,
            )

        db.commit()
        print("Seeded SERPS POP demo data.")
        print(f"  Institution: {institution.code} ({institution.institution_id})")
        print("  Demo users: sysadmin@serps.local, admin@miva.edu.ng, reviewer@miva.edu.ng, candidate@miva.edu.ng")
        print("  Demo password: read from SERPS_DEMO_PASSWORD")
        print("  Session: candidate creates it after consent and dual-camera readiness")
        print(f"  Roles available: {', '.join(sorted(roles))}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
