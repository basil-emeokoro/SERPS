# SERPS POP Technology Claim Matrix

| Technology | Dissertation Claim | Implemented Status | Integration Evidence | Automated Test Evidence | Next Action |
| --- | --- | --- | --- | --- | --- |
| FastAPI | Backend API/service boundary | Implemented foundation with auth/RBAC route groups | `apps/api/app/main.py`, `/api/v1/health`, `/api/v1/evidence-events`, `/api/v1/auth`, `/api/v1/candidates`, `/api/v1/examination-sessions` | `tests/test_api_health.py`, `tests/test_auth_rbac_sessions.py` | Add generated frontend client and PostgreSQL integration checks |
| Next.js / React / TypeScript | Production-oriented frontend | Implemented foundation with role-aware portal landing panels | `apps/web/src/app/page.tsx`, strict TS config | `apps/web/src/lib/api.test.ts` | Add protected route groups |
| PostgreSQL | Authoritative POP database | Configured, not runtime-verified yet | `docker-compose.yml`, SQLAlchemy URL, Alembic migration | Pending database integration test | Run migration against PostgreSQL |
| SQLAlchemy 2.x | ORM/repository layer | Implemented foundation with identity, RBAC, candidate, examination and session models | `src/serps_pop/infrastructure/database.py`, `src/serps_pop/identity/models.py`, `EvidenceEventRecord` | `tests/test_auth_rbac_sessions.py` | Add assignment-scoped reviewer filtering |
| Alembic | Migrations | Implemented foundation plus Sprint 2 identity/exam/session migration | `migrations/versions/0001_initial_evidence_events.py`, `migrations/versions/0002_auth_rbac_exam_foundation.py` | Pending migration test | Add CI database service |
| Docker Compose | Local service orchestration | Configured | `docker-compose.yml`, Dockerfiles | `docker compose config` | Validate build after dependencies install |
| JWT/RBAC | Real authentication | Implemented foundation | `src/serps_pop/security/`, `apps/api/app/api/deps/auth.py`, `/api/v1/auth/*` | `tests/test_auth_rbac_sessions.py` | Replace development secret fallback with deployed secret management |
| WebRTC | Media transport | Future | None | None | Add WebRTC-ready components after portals |
| MediaPipe / YOLO | AI detectors | Future migration | POC modules only | POC tests only | Migrate after evidence/API pipeline |
| CIE | Contextual reasoning | Future migration | POC modules only | POC tests only | Migrate after persistence stabilises |
