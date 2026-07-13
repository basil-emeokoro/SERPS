from fastapi import APIRouter

from serps_pop.domain.version import SERPS_POP_VERSION

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "serps-pop-api",
        "version": SERPS_POP_VERSION,
    }


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": SERPS_POP_VERSION, "architecture": "SERPS POP foundation"}
