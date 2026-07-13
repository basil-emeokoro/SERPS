from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.api.v1.router import api_v1_router
from serps_pop.domain.version import SERPS_POP_VERSION

app = FastAPI(
    title="SERPS POP API",
    version=SERPS_POP_VERSION,
    description="Production-oriented prototype API boundary for SERPS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
