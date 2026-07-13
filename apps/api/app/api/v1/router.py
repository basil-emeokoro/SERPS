from fastapi import APIRouter

from apps.api.app.api.v1.routes.evidence import router as evidence_router
from apps.api.app.api.v1.routes.health import router as health_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(evidence_router, prefix="/evidence-events", tags=["evidence"])
