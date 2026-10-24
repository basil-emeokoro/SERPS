from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps.auth import CurrentUser, require_roles
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import Candidate, CandidateExaminationAssignment, Examination
from serps_pop.identity.schemas import AssignmentCreate, AssignmentRead, ExaminationCreate, ExaminationRead
from serps_pop.identity.services import (
    DomainConflict,
    DomainNotFound,
    ROLE_ADMIN,
    ROLE_REVIEWER,
    ROLE_SYSADMIN,
    create_assignment,
    create_examination,
)
from apps.api.app.examination_management import (
    CohortAssignmentRequest, CohortPreviewRead, Course, CourseCreate, CourseRead,
    CourseRegistration, CourseRegistrationCreate, CourseRegistrationRead,
    ExaminationManagementCreate, audit, resolve_course_cohort,
)

router = APIRouter()


@router.post("/", response_model=ExaminationRead, status_code=status.HTTP_201_CREATED)
def create(
    payload: ExaminationManagementCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> Examination:
    institution_id = payload.institution_id if current_user.has_role(ROLE_SYSADMIN) and payload.institution_id else current_user.institution_id
    try:
        exam = create_examination(db, ExaminationCreate(**payload.model_dump(exclude={"is_active"})), institution_id=institution_id, actor_user_id=current_user.user_id)
        exam.is_active = payload.is_active and payload.status != "inactive"
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()
    db.refresh(exam)
    return exam


@router.get("/", response_model=list[ExaminationRead])
def list_exams(
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
) -> list[Examination]:
    stmt = select(Examination)
    if not current_user.has_role(ROLE_SYSADMIN):
        stmt = stmt.where(Examination.institution_id == current_user.institution_id)
    return list(db.scalars(stmt.order_by(Examination.created_at.desc())).all())


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_candidate(
    payload: AssignmentCreate,
    current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)),
    db: Session = Depends(get_db),
):
    try:
        assignment = create_assignment(
            db,
            candidate_id=payload.candidate_id,
            examination_id=payload.examination_id,
            institution_id=current_user.institution_id,
            actor_user_id=current_user.user_id,
        )
    except DomainConflict as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DomainNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    db.commit()
    db.refresh(assignment)
    examination = db.get(Examination, assignment.examination_id)
    audit(db, action="assignment.operation", result="success", institution_id=assignment.institution_id, actor_user_id=current_user.user_id, target_type="assignment", target_id=assignment.assignment_id, metadata={"assignment_type": "individual", "examination_id": assignment.examination_id, "monitoring_mode": examination.monitoring_mode if examination else None, "affected_candidate_count": 1})
    db.commit()
    return assignment


@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    course = Course(institution_id=current_user.institution_id, course_code=payload.course_code.strip(), title=payload.title.strip(), is_active=payload.is_active)
    db.add(course)
    try: db.flush()
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Course code already exists for this institution.") from exc
    audit(db, action="course.create", result="success", institution_id=current_user.institution_id, actor_user_id=current_user.user_id, target_type="course", target_id=course.course_id, metadata={"course_code": course.course_code})
    db.commit(); db.refresh(course); return course


@router.get("/courses", response_model=list[CourseRead])
def list_courses(current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    return list(db.scalars(select(Course).where(Course.institution_id == current_user.institution_id).order_by(Course.course_code)).all())


@router.post("/course-registrations", response_model=CourseRegistrationRead, status_code=status.HTTP_201_CREATED)
def register_candidate_for_course(payload: CourseRegistrationCreate, current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    course, candidate = db.get(Course, payload.course_id), db.get(Candidate, payload.candidate_id)
    if not course or not candidate or course.institution_id != current_user.institution_id or candidate.institution_id != current_user.institution_id:
        raise HTTPException(status_code=404, detail="Course or candidate not found in authorised institution.")
    registration = CourseRegistration(institution_id=current_user.institution_id, course_id=course.course_id, candidate_id=candidate.candidate_id)
    db.add(registration)
    try: db.flush()
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Candidate is already registered for this course.") from exc
    audit(db, action="course.registration.create", result="success", institution_id=current_user.institution_id, actor_user_id=current_user.user_id, target_type="course_registration", target_id=registration.course_registration_id, metadata={"course_id": course.course_id, "candidate_id": candidate.candidate_id})
    db.commit(); db.refresh(registration); return registration


@router.post("/cohorts/preview", response_model=CohortPreviewRead)
def preview_cohort(payload: CohortAssignmentRequest, current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    try: return resolve_course_cohort(db, course_id=payload.course_id, examination_id=payload.examination_id, institution_id=current_user.institution_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))


@router.post("/cohorts/assign", response_model=CohortPreviewRead, status_code=status.HTTP_201_CREATED)
def assign_cohort(payload: CohortAssignmentRequest, current_user: CurrentUser = Depends(require_roles(ROLE_ADMIN, ROLE_SYSADMIN)), db: Session = Depends(get_db)):
    try: result = resolve_course_cohort(db, course_id=payload.course_id, examination_id=payload.examination_id, institution_id=current_user.institution_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc))
    created = []
    for candidate in result["candidates"]:
        if candidate["outcome"] == "eligible":
            assignment = CandidateExaminationAssignment(institution_id=current_user.institution_id, candidate_id=candidate["candidate_id"], examination_id=payload.examination_id, status="eligible")
            db.add(assignment); db.flush(); created.append(assignment.assignment_id)
    result["created_count"] = len(created)
    audit(db, action="assignment.cohort", result="success", institution_id=current_user.institution_id, actor_user_id=current_user.user_id, target_type="course", target_id=payload.course_id, metadata={"assignment_type": "cohort", "cohort_criterion": {"type": "course_registration", "course_id": payload.course_id}, "examination_id": payload.examination_id, "monitoring_mode": result["monitoring_mode"], "affected_candidate_count": len(created), "already_assigned_count": result["already_assigned_count"], "ineligible_count": result["ineligible_count"]})
    db.commit(); return result
