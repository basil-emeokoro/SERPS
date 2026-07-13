# SERPS POP Technology Claim Matrix

| Technology | Dissertation Claim | Implemented Status | Integration Evidence | Automated Test Evidence | Next Action |
| --- | --- | --- | --- | --- | --- |
| FastAPI | Backend API/service boundary | Implemented foundation | `apps/api/app/main.py`, `/api/v1/health`, `/api/v1/evidence-events` | `tests/test_api_health.py` | Add authenticated services and persistence-backed endpoints |
| Next.js / React / TypeScript | Production-oriented frontend | Implemented foundation | `apps/web/src/app/page.tsx`, strict TS config | `apps/web/src/lib/api.test.ts` | Add role-aware portals |
| PostgreSQL | Authoritative POP database | Configured, not runtime-verified yet | `docker-compose.yml`, SQLAlchemy URL, Alembic migration | Pending database integration test | Run migration against PostgreSQL |
| SQLAlchemy 2.x | ORM/repository layer | Implemented foundation | `src/serps_pop/infrastructure/database.py`, `EvidenceEventRecord` | Import/compile tests after dependency install | Expand schema entities |
| Alembic | Migrations | Implemented foundation | `migrations/versions/0001_initial_evidence_events.py` | Pending migration test | Add CI database service |
| Docker Compose | Local service orchestration | Configured | `docker-compose.yml`, Dockerfiles | `docker compose config` | Validate build after dependencies install |
| JWT/RBAC | Real authentication | Future | None | None | Sprint 2/3 authentication foundation |
| WebRTC | Media transport | Future | None | None | Add WebRTC-ready components after portals |
| MediaPipe / YOLO | AI detectors | Future migration | POC modules only | POC tests only | Migrate after evidence/API pipeline |
| CIE | Contextual reasoning | Future migration | POC modules only | POC tests only | Migrate after persistence stabilises |
