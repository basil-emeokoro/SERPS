from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic.script import ScriptDirectory

from apps.api.app.api.deps.database import get_db
from serps_pop.config.settings import get_settings
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
def version(db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none() or "unversioned"
    return {
        "application_version": SERPS_POP_VERSION,
        "frontend_build_identifier": settings.frontend_build_id,
        "backend_build_identifier": settings.backend_build_id,
        "database_migration_revision": revision,
        "environment": settings.env,
    }


@router.get('/ready')
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        expected = set(ScriptDirectory.from_config(Config('alembic.ini')).get_heads())
        actual = set(db.execute(text('SELECT version_num FROM alembic_version')).scalars())
        if actual != expected:
            raise HTTPException(status_code=503, detail='Database migrations are not ready.')
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail='Database is unavailable.') from None
    return {'status': 'ready'}
