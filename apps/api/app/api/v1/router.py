from fastapi import APIRouter

from apps.api.app.api.v1.routes.audit_logs import router as audit_logs_router
from apps.api.app.api.v1.routes.auth import router as auth_router
from apps.api.app.api.v1.routes.candidates import router as candidates_router
from apps.api.app.api.v1.routes.candidate_workflow import router as candidate_workflow_router
from apps.api.app.api.v1.routes.evidence import router as evidence_router
from apps.api.app.api.v1.routes.examination_sessions import router as examination_sessions_router
from apps.api.app.api.v1.routes.examinations import router as examinations_router
from apps.api.app.api.v1.routes.health import router as health_router
from apps.api.app.api.v1.routes.governance import router as governance_router
from apps.api.app.api.v1.routes.institutions import router as institutions_router
from apps.api.app.api.v1.routes.identity_assurance import router as identity_assurance_router
from apps.api.app.api.v1.routes.roles import router as roles_router
from apps.api.app.api.v1.routes.users import router as users_router

from apps.api.app.api.v1.routes.reauthentication import router as reauthentication_router

api_v1_router = APIRouter()
api_v1_router.include_router(reauthentication_router, prefix="/identity-assurance/reauthentication", tags=["identity-assurance"])
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(identity_assurance_router, prefix="/identity-assurance", tags=["identity-assurance"])
api_v1_router.include_router(institutions_router, prefix="/institutions", tags=["institutions"])
api_v1_router.include_router(users_router, prefix="/users", tags=["users"])
api_v1_router.include_router(roles_router, prefix="/roles", tags=["roles"])
api_v1_router.include_router(candidates_router, prefix="/candidates", tags=["candidates"])
api_v1_router.include_router(candidate_workflow_router, prefix="/candidate", tags=["candidate-workflow"])
api_v1_router.include_router(examinations_router, prefix="/examinations", tags=["examinations"])
api_v1_router.include_router(
    examination_sessions_router,
    prefix="/examination-sessions",
    tags=["examination-sessions"],
)
api_v1_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit-logs"])
api_v1_router.include_router(evidence_router, prefix="/evidence-events", tags=["evidence"])
api_v1_router.include_router(governance_router, tags=["governance"])
