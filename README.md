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

## Verification Commands

```powershell
python -m py_compile apps\api\app\main.py src\serps_pop\domain\evidence.py
python -m pytest -q
npm.cmd run lint -w apps/web
npm.cmd run typecheck -w apps/web
npm.cmd run test -w apps/web
docker compose config
```

## Dissertation Figure Discipline

Do not assign or generate final figure outputs unless they match the dissertation-defined numbering and the implemented system. Chapter Five figure numbering is pending an updated dissertation document.
