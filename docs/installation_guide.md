# SERPS RC1 Installation Guide

## Supported demonstration topology

RC1 is designed for a controlled local demonstration with the Next.js web application, FastAPI API, and a migrated database. PostgreSQL is the deployment target; SQLite may be used only for bounded local validation. Use two local cameras if demonstrating the full candidate media flow.

## Prerequisites

- Windows PowerShell (commands below), Python 3.11 or newer, and pip
- Node.js 22 and npm
- Git
- Optional: Docker Desktop with Linux containers and Compose v2
- Two browser-visible video inputs for a hardware dual-camera demonstration
- A modern secure-context browser; localhost is treated as secure for media APIs

## Source and dependencies

```powershell
Set-Location C:\SERPS
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
npm.cmd install
```

Edit `.env` locally. Do not commit it. At minimum set:

```dotenv
SERPS_ENV=development
SERPS_DATABASE_URL=postgresql+psycopg://serps:URL_ENCODED_PASSWORD@localhost:5432/serps_pop
SERPS_JWT_SECRET=GENERATE_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS
SERPS_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SERPS_DEMO_PASSWORD=CHOOSE_A_STRONG_DEMO_ONLY_PASSWORD
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Database migration and seed

Start PostgreSQL, then:

```powershell
python -m alembic heads
python -m alembic upgrade head
python -m alembic current
$env:SERPS_DEMO_PASSWORD = "the-same-strong-demo-password"
python scripts\dev\seed_demo_data.py
```

The current revision must match `python -m alembic heads` for the checked-out commit. The seed output should list four users and state that the candidate creates the session after consent and dual-camera readiness.

## Native development startup

Terminal 1:

```powershell
Set-Location C:\SERPS
uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
Set-Location C:\SERPS
npm.cmd run dev -w apps/web
```

Open `http://localhost:3000`. API health is `http://localhost:8000/api/v1/health`; OpenAPI UI is `http://localhost:8000/docs`.

## Docker Compose startup

Follow [Docker deployment](docker_deployment.md). It supplies fresh-clone commands and avoids relying on a native runtime `.env` or web `.env.local`. Never point container validation at the active evaluation database or reuse its storage.

## Installation verification

```powershell
python -m py_compile apps\api\app\main.py
python -m pytest -q
npm.cmd run typecheck -w apps/web
npm.cmd run test -w apps/web
npm.cmd run lint -w apps/web
npm.cmd run build -w apps/web
```

Do not classify an installation as PostgreSQL-verified unless a real connection, migrations, workflow persistence, reviewer decision, and report generation have succeeded against PostgreSQL.
