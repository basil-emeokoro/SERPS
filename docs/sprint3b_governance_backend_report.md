# Sprint 3B Governance Backend Report

## Status

Sprint 3B implements the persisted governance backend vertical slice as a **Production-Oriented Prototype — Early Alpha**. The implementation remains advisory and human-governed: it cannot declare misconduct, impose a penalty, or terminate an examination automatically. Sprint 3C–3E remain incomplete.

## Repository starting state

- Repository: `C:\SERPS`
- Branch: `main`
- Starting checkpoint: `30176c1` (`fix(evidence): persist and retrieve session evidence events`)
- Starting verification: 14 tests passed; no blockers
- Sprint 3A implementation and Chapter Three diagrams were not redesigned or resumed.

## Files created and modified

Created:

- `src/serps_pop/governance/__init__.py`
- `src/serps_pop/governance/models.py`
- `src/serps_pop/governance/engine.py`
- `src/serps_pop/governance/schemas.py`
- `src/serps_pop/governance/services.py`
- `apps/api/app/api/v1/routes/governance.py`
- `migrations/versions/0003_sprint3b_governance.py`
- `tests/test_governance.py`
- `docs/sprint3_master_execution_plan.md`
- `docs/sprint3b_governance_backend_report.md`

Modified:

- `apps/api/app/api/v1/router.py`
- `migrations/env.py`

## Persistence and migration

Alembic revision `0003_sprint3b_governance`, chained from `0002_auth_rbac_exam`, creates:

- `contextual_assessments`
- `agent_recommendations`
- `institutional_policies`
- `policy_evaluations`
- `reviewer_decisions`
- `governance_audit_records`
- `session_report_snapshots`

The migration contains institution/session/time/status indexes, foreign keys, normalized score/confidence constraints, an automatic-termination prohibition, and a complete downgrade path. It does not recreate or alter `evidence_events`. SQLAlchemy lifecycle guards reject updates and deletes for all governance record models; corrections require a new superseding record.

SQLite migration verification completed successfully:

- head: `0003_sprint3b_governance`
- upgrade from base to head: passed
- current revision: `0003_sprint3b_governance (head)`
- downgrade to `0002_auth_rbac_exam`: passed
- re-upgrade to head: passed
- `alembic check`: `No new upgrade operations detected.`

## Contextual Intelligence Engine

The CIE is deterministic rule logic, not a machine-learning model. Rule version `CIE-RULES-1.0` uses a configurable 60-second default window and supports normalized event names for camera connection/disconnection, face detection/absence, and tab-focus loss.

Risk contributions:

- `FACE_NOT_DETECTED`: 1 = 0.15; 2 = 0.35; 3+ = 0.60
- `CAMERA_DISCONNECTED`: 1 = 0.35; 2+ = 0.65
- `TAB_FOCUS_LOST`: 1 = 0.10; 2 = 0.20; 3+ = 0.40
- camera disconnection combined with face absence adds 0.15
- total score is bounded to 0.0–1.0

Level thresholds:

- Low: 0.00–0.2999
- Moderate: 0.30–0.5999
- High: 0.60–0.8499
- Critical: 0.85–1.00

Each assessment stores score, level, confidence, actual contributing EvidenceEvent IDs, temporal bounds, generated explanation, rule version, actor, institution, candidate, and session. Recalculation creates a new record linked through audit history.

## Agentic Decision Support and IPIME

Bounded advisory mapping:

- Low → `CONTINUE_MONITORING`
- Moderate → `REQUEST_CANDIDATE_ACKNOWLEDGEMENT`
- High → `NOTIFY_REVIEWER`
- Critical → `ESCALATE_INCIDENT`

Every recommendation stores confidence, explanation, priority, reviewer requirement, current session context, and source assessment. Explanations explicitly state that no misconduct determination is made.

IPIME lazily provisions a versioned default policy per institution when no active policy exists. High and Critical actions are policy-controlled; reviewer notification and candidate acknowledgement thresholds are evaluated; reauthentication expectation is recorded. Every evaluation forces `continue_examination = true`. Both service logic and the database prohibit automatic examination termination.

## Reviewer, audit, timeline, and report workflow

The reviewer queue includes candidate, examination, session status, latest evidence, current assessment score/level/explanation, recommendation, policy outcome, and resolved status. It supports institution, risk-level, unresolved, examination, and active-session filters.

Only reviewers and sysadmins can record decisions. The API validates institution access, session ownership, the complete assessment → recommendation → policy-evaluation chain, allowed decision values, reviewer identity, and non-blank rationale. The decision and its audit record are flushed and committed in the same transaction.

Governance audit records store actor, institution, session, action, entity, predecessor, timestamp, structured details, and a SHA-256 hash of canonicalized details. Audit records are append-only.

The combined timeline returns persisted EvidenceEvents, assessments, recommendations, policy evaluations, reviewer decisions, and audit entries chronologically. Report snapshots store candidate details, examination/session data, EvidenceEvent counts and IDs, risk history, explanations, recommendations, evaluations, reviewer decisions, and audit history as a complete structured JSON payload.

## API routes

- `POST /api/v1/examination-sessions/{session_id}/contextual-assessments`
- `GET /api/v1/examination-sessions/{session_id}/contextual-assessments`
- `POST /api/v1/contextual-assessments/{assessment_id}/recommendations`
- `POST /api/v1/agent-recommendations/{recommendation_id}/policy-evaluations`
- `GET /api/v1/reviewer/sessions`
- `POST /api/v1/examination-sessions/{session_id}/reviewer-decisions`
- `GET /api/v1/examination-sessions/{session_id}/governance-timeline`
- `POST /api/v1/examination-sessions/{session_id}/reports`
- `GET /api/v1/examination-sessions/{session_id}/reports/{report_id}`

All routes reuse JWT/RBAC dependencies and enforce institution boundaries server-side. There are no update or delete governance endpoints.

## Verification results

- `python -m py_compile apps\api\app\main.py`: passed
- `python -m pytest -q -p no:cacheprovider`: `21 passed in 59.23s`
- focused Sprint 3B suite: `7 passed`
- `python -m alembic heads`: `0003_sprint3b_governance (head)`
- SQLite upgrade/current/downgrade/re-upgrade: passed
- `python -m alembic check`: no pending operations
- `npm.cmd run typecheck -w apps/web`: passed
- `npm.cmd run test -w apps/web`: 1 test file and 1 test passed
- `docker compose config`: passed (Docker client emitted a sandbox warning while reading the user-level Docker config)

## PostgreSQL/Docker verification

PostgreSQL verification was **not completed and is not claimed**. The Docker CLI was present, but initial sandboxed daemon access was denied. After daemon access approval, `docker compose up -d db` remained unresponsive, `docker compose ps` returned no running service, and localhost port 5432 was unavailable. Therefore no PostgreSQL migration or seeded governance-chain result is reported. SQLite migration and application tests remain the verified database results for this run.

## Commits

- `5797120` — `feat(governance): add sprint three governance persistence models`
- `e426c54` — `feat(cie): implement contextual evidence assessment engine`
- `54e893f` — `feat(governance): add advisory policy review and report workflows`
- `5d2eebf` — `test(governance): cover sprint three governance backend slice`

The documentation commit and final push status are reported in the completion handoff.

## Known limitations

- PostgreSQL execution remains unverified because the local Docker database was unavailable.
- CIE is transparent deterministic logic and has not been calibrated as a statistical or machine-learning model.
- Default institutional policy provisioning is minimal; policy administration UI and richer version lifecycle are later work.
- Reviewer notification delivery is represented by persisted workflow state; no external notification channel is implemented.
- Report payloads are structured JSON snapshots; downloadable files are deferred to Sprint 3D or Sprint 3E.
- Candidate UI, consent, device/camera discovery, Next.js operational portals, and Playwright E2E remain outside Sprint 3B.

## Exact Sprint 3C recommendation

Implement only the candidate pre-examination backend/runtime workflow: candidate registration, explicit consent acceptance with a traceable consent record, candidate authentication, assigned-examination retrieval, device compatibility checks, camera discovery and permission state, and authorised examination-session start. Connect successful session start to real EvidenceEvent production using the existing Sprint 3A persistence contract. Reuse the Sprint 3B governance APIs without redesigning their authority model. Do not begin Next.js dashboard implementation, PostgreSQL deployment hardening, Playwright, or full E2E work assigned to Sprint 3D and Sprint 3E.
