# SERPS Research Prototype

SERPS is an explainable multi-modal identity-assurance, monitoring, and governance layer for integration with external assessment systems. This repository contains the Production-Oriented Prototype and is classified as **Research Prototype Version 1.0 Release Candidate (RC1)** after Sprint 3E validation.

SERPS is not a complete assessment platform, production secure browser, or enterprise video-streaming service. Its bounded demonstration examination workspace generates realistic monitored interactions for research evaluation.

## Implemented workflow

Candidate registration -> bounded prototype verification -> six-direction facial enrolment -> password authentication -> dynamic facial/liveness authentication -> immutable consent -> device readiness -> distinct primary and secondary cameras -> identity-gated demonstration workspace -> EvidenceEvents -> Contextual Intelligence Engine -> bounded agent recommendation -> institutional policy evaluation -> reviewer decision -> administrator oversight -> immutable audit and structured reports.

Reviewer and administrator registrations enter a System Administrator approval queue. The four seeded defence identities are explicitly marked demonstration accounts and bypass registration and facial enrolment; normal candidate registrations do not bypass the lifecycle.

The backend remains authoritative for JWT authentication, RBAC, candidate ownership, institution isolation, registration status, identity readiness, governance records, and decisions. Browser face and liveness results are bounded research-prototype attestations, not certified biometric proof; final operational actions remain human-controlled.

## Stack

- Next.js, React, TypeScript, and locally bundled MediaPipe Tasks Vision web application
- FastAPI and Pydantic API
- SQLAlchemy and Alembic persistence
- PostgreSQL deployment target
- Pytest, Vitest, TypeScript, and ESLint validation
- Docker Compose packaging

## Local setup

```powershell
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
npm.cmd install
python -m alembic upgrade head
```

Set a real local `SERPS_JWT_SECRET`, database credentials, and `SERPS_DEMO_PASSWORD` in `.env`; never commit that file.

Start the API and web application in separate terminals:

```powershell
uvicorn apps.api.app.main:app --reload --port 8000
npm.cmd run dev -w apps/web
```

Seed a fresh demonstration database only after migrations:

```powershell
$env:SERPS_DEMO_PASSWORD = "your-strong-demo-only-password"
python scripts\dev\seed_demo_data.py
```

The seeder creates users, a candidate, examination, and eligible assignment. The candidate creates the examination session only after consent and dual-camera readiness.

## Docker Compose

Compose intentionally requires secrets instead of embedding defaults:

```powershell
$env:SERPS_POSTGRES_PASSWORD = "your-local-database-password"
$env:SERPS_DATABASE_URL = "postgresql+psycopg://serps:your-url-encoded-password@db:5432/serps_pop"
$env:SERPS_JWT_SECRET = "your-random-secret-with-at-least-32-characters"
docker compose config
docker compose up -d --build
```

## Verification

```powershell
python -m py_compile apps\api\app\main.py
python -m pytest -q
python -m alembic heads
npm.cmd run typecheck -w apps/web
npm.cmd run test -w apps/web
npm.cmd run lint -w apps/web
npm.cmd run build -w apps/web
docker compose config
```

See `docs/installation_guide.md`, `docs/user_manual.md`, `docs/demo_script.md`, and `docs/sprint3e_validation_report.md` for examiner-facing guidance and exact validation status.

## Dissertation boundary

The implementation supports the dissertation identity-lifecycle, governance, explainability, dual-camera, reviewer, administrator, and reporting claims at research-prototype scale. The facial representation is a derived 8-by-8 luminance descriptor and pose/liveness validation uses local MediaPipe landmarks plus bounded geometric movement proxies. It is not production face recognition, certified liveness, or presentation-attack resistance. Hardware-backed browser evidence and production deployment claims must follow the limitations documents.
