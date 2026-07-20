# Sprint 3C Candidate Workflow Report

## Repository starting state

- Repository: `C:\SERPS`
- Branch: `main`
- Starting HEAD: `2ecde4c073a25af92396c2ace96f8f6001879a99`
- Starting status: clean; Sprint 3B accepted
- Sprint 3A/Sprint 3B behavior and Chapter Three diagrams were not redesigned.

## Files created

- `src/serps_pop/candidate_workflow/__init__.py`
- `src/serps_pop/candidate_workflow/models.py`
- `src/serps_pop/candidate_workflow/schemas.py`
- `src/serps_pop/candidate_workflow/services.py`
- `apps/api/app/api/v1/routes/candidate_workflow.py`
- `apps/web/src/app/register/page.tsx`
- `migrations/versions/0004_sprint3c_candidate_workflow.py`
- `tests/test_candidate_workflow.py`
- `docs/project_progress.md`
- `docs/sprint3c_candidate_workflow_report.md`

## Files modified

- `src/serps_pop/identity/models.py`
- `src/serps_pop/evidence/services.py`
- `apps/api/app/api/v1/routes/evidence.py`
- `apps/api/app/api/v1/router.py`
- `apps/web/src/app/candidate/page.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/lib/api.ts`
- `migrations/env.py`
- `scripts/dev/seed_demo_data.py`
- `docs/sprint3_master_execution_plan.md`

## APIs implemented

- `POST /api/v1/candidate/register`
- `POST /api/v1/auth/login` (existing JWT login reused by registered candidates)
- `GET /api/v1/candidate/examinations`
- `GET /api/v1/candidate/dashboard`
- `POST /api/v1/candidate/consents`
- `GET /api/v1/candidate/consents`
- `POST /api/v1/candidate/device-checks`
- `GET /api/v1/candidate/device-checks`
- `POST /api/v1/candidate/cameras`
- `POST /api/v1/candidate/camera-permissions`
- `POST /api/v1/candidate/examinations/{examination_id}/start`
- `POST /api/v1/evidence-events/` (extended to authorised candidates for their own active session)

Candidate registration creates linked institution-scoped identity/profile records. Candidate endpoints resolve the profile from the authenticated JWT subject and never accept a caller-supplied candidate identity. Session start rejects missing consent, failed checks, missing selection, denied permission, foreign assignments, and duplicate active sessions.

## Database changes

Alembic revision `0004_sprint3c_candidate`, chained from `0003_sprint3b_governance`, adds:

- nullable unique `candidates.user_id` for existing-data-compatible candidate identity binding;
- append-only `candidate_consents`;
- append-only `device_check_records`;
- append-only `camera_selection_records`;
- append-only `camera_permission_records`;
- consent/device/camera/permission foreign keys on `examination_sessions`.

The migration includes indexes, constraints, foreign keys, SQLite-compatible batch changes, PostgreSQL-compatible types, and a downgrade path. It does not redesign EvidenceEvent or governance tables.

## Frontend routes and browser operation

- `/register`: live candidate registration form using the registration API.
- `/candidate`: authenticated operational dashboard showing assignments, consent status, device status, camera state, readiness, live video preview, and start controls.

The dashboard uses real browser APIs:

- `navigator.mediaDevices.enumerateDevices()` for camera/microphone discovery;
- `navigator.mediaDevices.getUserMedia()` for permission and a live stream;
- media track `ended` events for `CAMERA_DISCONNECTED`;
- document visibility events for `TAB_FOCUS_LOST`;
- browser `FaceDetector`, where genuinely supported, for `FACE_DETECTED` or `FACE_NOT_DETECTED`.

No video stream or frame is persisted. When FaceDetector is unavailable, no synthetic face event is created.

## Governance integration

Candidate EvidenceEvents require an authenticated Candidate role, matching linked candidate, matching institution, and active examination session. Supported events retain the Sprint 3A persistence contract and automatically invoke the existing Sprint 3B services in the same transaction:

EvidenceEvent → ContextualAssessment → AgentRecommendation → PolicyEvaluation → GovernanceAuditRecord.

The integration does not change risk rules, recommendation authority, policy behavior, or the prohibition on automatic examination termination.

## Tests and verification

- `python -m py_compile apps\api\app\main.py`: passed
- `python -m pytest -q -p no:cacheprovider tests\test_candidate_workflow.py`: `7 passed in 41.44s`
- `python -m pytest -q -p no:cacheprovider`: `28 passed in 126.87s`
- `python -m alembic heads`: `0004_sprint3c_candidate (head)`
- Alembic base upgrade, current, downgrade to `0003_sprint3b_governance`, re-upgrade, and `alembic check`: passed; no pending operations
- `npm.cmd run typecheck -w apps/web`: passed
- `npm.cmd run test -w apps/web`: 1 test file and 1 test passed
- `docker compose config`: passed

Coverage includes registration, authentication, invalid institution, assignment isolation, explicit/versioned consent, consent immutability, device/camera gates, denied permission, session linkage, dashboard readiness, candidate session spoofing denial, EvidenceEvent persistence, and automatic Sprint 3B governance/audit creation.

## PostgreSQL verification

PostgreSQL verification was not completed and is not claimed. Docker Compose configuration is valid, but the approved `docker compose up -d db` attempt produced no running service or usable port 5432. SQLite is the verified database for this run.

## Commits

- `476bbfb` — `feat(candidate): implement registration and authentication workflow`
- `a4a4020` — `feat(consent): implement immutable consent workflow`
- `534e00d` — `feat(device): implement device compatibility and camera checks`
- `4e7e0b4` — `feat(session): implement candidate examination startup workflow`
- `52f4f79` — `test(candidate): complete Sprint 3C backend integration`

The documentation commit and push status are reported in the completion handoff.

## Remaining Sprint 3D scope

Build and harden the Next.js operational interface checkpoint without changing backend authority boundaries:

- reviewer queue, session detail, governance timeline, evidence context, and rationale-required decision UI;
- administrator institution/user/role/candidate/examination/assignment/policy management UI;
- candidate experience hardening around active-session state, recoverable browser errors, and report access where authorised;
- shared API client/types, loading/error states, accessibility, and responsive operational layouts;
- no Playwright/full deployment proof until Sprint 3E.

Project status remains **Production-Oriented Prototype — Early Alpha**.
