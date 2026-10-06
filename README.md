# SERPS Research Prototype

SERPS is an explainable multi-modal identity-assurance, monitoring, and governance layer for integration with external assessment systems. This repository contains the Production-Oriented Prototype and is classified as **Research Prototype Version 1.0 Release Candidate (RC1)**.

SERPS is not a complete assessment platform, production secure browser, or enterprise video-streaming service. Its bounded demonstration examination workspace generates realistic monitored interactions for research evaluation.

## Implemented workflow

Candidate registration -> bounded prototype verification -> six-direction facial enrolment -> password authentication -> dynamic facial/liveness authentication -> immutable consent -> device readiness -> distinct primary and secondary cameras -> identity-gated demonstration workspace -> EvidenceEvents -> Contextual Intelligence Engine -> bounded agent recommendation -> institutional policy evaluation -> reviewer decision -> administrator oversight -> immutable audit and structured reports.

Reviewer and administrator registrations enter a System Administrator approval queue. The four seeded defence identities are explicitly marked demonstration accounts and bypass registration and facial enrolment; normal candidate registrations do not bypass the lifecycle.

The backend remains authoritative for JWT authentication, RBAC, candidate ownership, institution isolation, registration status, identity readiness, governance records, and decisions. The browser performs bounded local EfficientDet-Lite0 person/mobile-phone inference, MediaPipe face-presence monitoring, and Web Audio RMS activity measurement. Raw camera and microphone media are not sent to reviewer or administrator portals or persisted by these monitors. Browser face and liveness results are bounded research-prototype attestations, not certified biometric or presentation-attack proof; recommendations remain advisory, final operational actions remain human-controlled, and SERPS does not autonomously terminate examinations.

## Stack

- Next.js, React, TypeScript, locally bundled MediaPipe Tasks Vision, EfficientDet-Lite0, and Web Audio RMS monitoring
- FastAPI and Pydantic API
- SQLAlchemy and Alembic persistence
- SQLite for the evaluated native prototype runtime; PostgreSQL is the configured deployment target
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

See [Docker deployment](docs/docker_deployment.md) for a fresh-clone setup, required secrets, build-time browser API URL, configurable loopback ports, isolated PostgreSQL storage, health checks and migration verification. Docker Desktop must be running with Linux containers and Compose v2.

The deployment path is separate from the native SQLite evaluation runtime. Container readiness does not establish detector or physical camera acceptance.

## Verification

```powershell
python -m py_compile apps\api\app\main.py
python -m pytest -q
python -m alembic heads
npm.cmd run typecheck -w apps/web
npm.cmd run test -w apps/web
npm.cmd run lint -w apps/web
npm.cmd run build -w apps/web
docker compose config --quiet
```

See `docs/installation_guide.md`, `docs/user_manual.md`, `docs/demo_script.md`, and `docs/sprint3e_validation_report.md` for installation, operation, demonstration, and historical validation guidance. Current verification results should be taken from the applicable test run rather than inferred from the historical Sprint 3E report.

## Dissertation boundary

The implementation supports identity lifecycle, governance, explainability, dual-camera, reviewer, administrator, and reporting workflows at research-prototype scale. The facial representation is a derived 8-by-8 luminance descriptor and pose/liveness validation uses local MediaPipe landmarks plus bounded geometric movement proxies. Object-class person evidence does not establish that a detected representation is a physically present live person. SERPS is not production face recognition, certified liveness, presentation-attack resistance, penetration-tested infrastructure, or a production deployment. Hardware-backed browser evidence and production claims require separate validation.
