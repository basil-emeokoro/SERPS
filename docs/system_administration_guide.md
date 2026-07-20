# SERPS RC1 System Administration Guide

## Responsibilities

The system administrator protects secrets and data, applies migrations, provisions role-appropriate users, monitors service health, verifies institution isolation, maintains demonstration data, and communicates prototype limitations. RC1 is not approved for unattended production use.

## Configuration

Keep `.env` outside version control. Production-like startup requires:

- `SERPS_ENV=production`
- an externally generated `SERPS_JWT_SECRET`
- a least-privilege PostgreSQL URL and separate database password
- exact `SERPS_CORS_ORIGINS`
- the correct browser-facing `NEXT_PUBLIC_API_BASE_URL`
- `SERPS_DEMO_PASSWORD` only when seeding a controlled demo

Rotate secrets after exposure or shared demonstrations. Existing JWT access tokens remain valid until their short expiry unless signing keys are rotated.

## Roles and authority

- Candidate: own assignments, readiness, sessions, workspace, completion, and evidence.
- Reviewer/Proctor: institution-scoped queues/details, decisions, timelines, and reports.
- Administrator: institution users/data, operational metrics, audit, and read-only oversight.
- System Administrator: cross-institution administration where explicitly supported.

Never use frontend visibility as an authorization control; verify API responses and server roles.

## Database lifecycle

Before upgrades, back up the database and test restore. Review the single Alembic head, then apply:

```powershell
python -m alembic heads
python -m alembic upgrade head
python -m alembic current
```

RC1 head is `0005_sprint3d_dual_camera`. Downgrades are demonstration/test operations, not a substitute for a production rollback plan.

## Demo data

Use a fresh database/volume where practical. Set `SERPS_DEMO_PASSWORD` explicitly, migrate, then run the seeder. It is idempotent for core demo records and intentionally does not create an examination session. If users already exist, changing the environment password does not reset their stored credentials; recreate the controlled demo database or use the original configured password.

## Monitoring and audit

Check API health, container/process status, database connectivity, authentication failures, evidence ingestion errors, camera-failure counts, unresolved reviewer cases, and audit history. RC1 logs/audits must never contain plaintext credentials, tokens, raw video, or biometric templates.

## Backup and retention

RC1 does not implement automated backup or retention. Before institutional use, define encrypted backups, tested restore, evidence/report retention, candidate data access/deletion procedures, legal basis, and audit preservation. Raw video is not persisted by RC1.

## Release verification

Run compile, full tests, typecheck, frontend tests, lint, production build, Compose config, migration status, and a seeded workflow. Record environment, commit, database engine, commands, results, and limitations. Do not claim PostgreSQL or hardware proof unless actually executed.

## Incident response

On suspected compromise: stop exposed services, preserve relevant audit evidence, rotate JWT/database credentials, revoke active sessions where supported, assess data scope, notify the responsible institution, and follow its incident/privacy process. RC1 itself is not a complete incident-management platform.
