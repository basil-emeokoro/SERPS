# SERPS POP - Secure Explainable Remote Proctoring System Production-Oriented Prototype

SERPS POP is the Production-Oriented Prototype of the Secure Explainable Remote Proctoring System. It is a separate implementation from the validated Streamlit proof of concept located at `C:\Miva_Capstone`.

This repository does not claim to be a production-certified examination platform. It applies production-capable architecture and engineering practices while preserving the validated SERPS governance pipeline:

```text
Sensors and Browser Signals
-> Detection Modules
-> Structured EvidenceEvent Generation
-> Contextual Intelligence Engine
-> Agentic Decision Support
-> Institutional Policy and Incident Management Engine
-> Candidate Acknowledgement where required
-> Human Reviewer
-> Final Institutional Decision
```

Detection modules produce structured evidence only. They do not make misconduct decisions. The CIE reasons contextually and produces explainable risk assessments. Agentic Decision Support remains advisory. IPIME applies configurable institutional workflow. Final decisions remain with authorised human reviewers.

## Repository Relationship

- **SERPS POC / SERPS Proof of Concept:** `C:\Miva_Capstone`
- **SERPS POP / SERPS Production-Oriented Prototype:** `C:\SERPS`
- POP preserves and refines validated POC functionality module by module.
- POC remains intact as the validated viva fallback baseline.
- This repository does not copy the POC Git history wholesale.

## Sprint 1 Scope

Implemented in this foundation sprint:

- Monorepo structure for web, API, shared packages, domain modules, migrations, tests, docs and scripts.
- FastAPI application under `/api/v1`.
- API health/version endpoints.
- EvidenceEvent schema migrated from the POC as a shared domain contract.
- Evidence ingestion endpoint scaffold.
- SQLAlchemy 2.x database configuration.
- Alembic migration scaffold for PostgreSQL.
- Next.js App Router frontend scaffold with TypeScript strict mode.
- Frontend-to-backend health connectivity.
- Docker Compose for web, API and PostgreSQL.
- CI foundation.
- POC-to-POP migration audit and backlog.
- Technology claim matrix.

Not implemented in Sprint 1:

- Full candidate enrolment workflow.
- Live camera/WebRTC transport.
- CIE migration.
- Agentic Decision Support migration.
- IPIME workflow migration.
- Production authentication and RBAC.
- Reviewer/candidate/admin full portals.

## Sprint 2 Scope

Implemented in the authentication, RBAC, candidate, examination and session foundation sprint:

- Real password hashing and JWT access/refresh token handling.
- Server-enforced role model for Candidate, Reviewer/Proctor, Administrator and System Administrator.
- Institution, user, role, candidate, examination, assignment, examination session, authentication session, refresh token and audit-log tables.
- Non-destructive Alembic migration `0002_auth_rbac_exam_foundation`.
- FastAPI route groups for authentication, institutions, users, roles, candidates, examinations, examination sessions and audit logs.
- Examination session state controls for authentication, device-check, ready, active, paused, completed and terminated states.
- Duplicate prevention and clean conflict responses for candidates, users, institutions, examinations, assignments and active sessions.
- Role-aware Next.js landing page explaining administrator, reviewer/proctor and candidate portal responsibilities.
- Idempotent demo seed script at `scripts/dev/seed_demo_data.py`; set `SERPS_DEMO_PASSWORD` to choose a local demo password, otherwise the script prints a one-time generated password.
- Regenerated OpenAPI documentation at `docs/openapi.json`.
- Regenerated Chapter Three diagram artefacts; Figure 3.19 now reflects the expanded schema.
- Security review notes, including the current npm audit finding, are tracked in `docs/security_review.md`.
- Docker API startup now runs `alembic upgrade head` before serving FastAPI, so the Compose PostgreSQL schema is brought to the current migration head during local container startup.

Still intentionally deferred:

- Full production portal implementation.
- Live media transport and AI detector migration.
- CIE, Agentic Decision Support and IPIME migration into POP.
- Production identity provider integration.
- Hardened cookie-backed browser sessions; the current Next.js login page is a local POP validation foundation.

## Local Development

```powershell
python -m pip install -e .[dev]
uvicorn apps.api.app.main:app --reload --port 8000
npm.cmd install
npm.cmd run dev -w apps/web
```

Backend health: `http://localhost:8000/api/v1/health`

Frontend: `http://localhost:3000`

OpenAPI: `http://localhost:8000/openapi.json`

Seed local demo data after applying migrations:

```powershell
$env:SERPS_DEMO_PASSWORD = "choose-a-local-demo-password"
python scripts\dev\seed_demo_data.py
```

## Verification Commands

```powershell
python -m py_compile apps\api\app\main.py src\serps_pop\domain\evidence.py src\serps_pop\identity\models.py src\serps_pop\identity\services.py
python -m pytest -q
npm.cmd run lint -w apps/web
npm.cmd run typecheck -w apps/web
npm.cmd run test -w apps/web
docker compose config
docker compose up -d --build
```

## Dissertation Figure Discipline

Do not assign or generate final figure outputs unless they match the dissertation-defined numbering and the implemented system. Chapter Five figure numbering is pending an updated dissertation document.
