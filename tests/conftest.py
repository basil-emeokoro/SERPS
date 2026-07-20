from __future__ import annotations

import os

os.environ.setdefault("SERPS_ENV", "test")
os.environ.setdefault("SERPS_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SERPS_JWT_SECRET", "serps-test-secret-that-is-at-least-32-characters")
os.environ.setdefault("SERPS_JWT_ISSUER", "serps-pop")
os.environ.setdefault("SERPS_JWT_AUDIENCE", "serps-api")
os.environ.setdefault("SERPS_ACCESS_TOKEN_MINUTES", "10")
