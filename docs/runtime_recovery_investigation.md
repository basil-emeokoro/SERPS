# Integrated runtime investigation and repair

21 October 2026. Isolated branch codex/integrated-runtime-recovery, based on native committed baseline97322281c63929f21c96c3aa66ebdb06a4f8b730. Native C:\SERPS, its SQLite database, environment files, next-env.d.ts change, Phase4 worktree, detector assets and Trial17 are preserved. No deployment/merge/push performed.

## Diagnosis before modification

- api.ts cleared credentials for any refresh exception, including network/5xx and cancellation. GET retry treated cancellation like transport failure. Workspace and PortalShell cleanup could apply stale asynchronous state updates.
- Workspace evidence emits were fire-and-forget promises with no retained queue, retry or acknowledgement tracking. POST assigned new evidence IDs, so retrying ambiguous failures could duplicate evidence and CIE/policy evaluations.
- Login also referenced DomainNotFound without importing it in the rejection path; the missing import and a failed-login regression are included.
- FacialVerification discovery/observation callbacks could outlive cleanup. Detector initialize methods could create multiple instances or publish an instance after close. Actual detectForVideo calls are synchronous; no close-during-active-inference race was established. Existing fair detector queue/per-track capture guards remain unchanged.
- At inspection, ports3100/8765/8000 had no reachable service and no SERPS Next process was found. Native apps/web/.env.local targets8765; root.env has an8000 frontend URL. Previously saved runtime configuration differs; no environment file was overwritten. Next consumes its app environment and public URL at build time, so verify served build rather than infer it from an unrelated root variable.
- Exact MediaPipe messages and development timing logs were unavailable (confirmed by user). No specific MediaPipe informational/error classification or cause of Next dev slowness is claimed. Inference exceptions remain visible; no console filtering/model/threshold changes.

## Repair

Transport/cancellation/HTTP errors are distinct. Cancellation is not retried, and request headers have a25second transport deadline. Credentials survive transport/5xx interruptions; definitive refresh rejection expires only the matching session. Refresh remains single-flight and detects superseding sign-ins. Async workspace/portal callbacks ignore cancelled mounts.

Each candidate/session has an ordered metadata-only outbox in sessionStorage, with stable UUID delivery identity, observed timestamp and sequence. One event is in flight at a time; transient transport/408/429/5xx errors retry at most three attempts per retry cycle. Other failures halt ordered delivery and remain visible for explicit retry. New events do not bypass an unresolved predecessor. Queued data survives same-tab navigation/remount/reload; closing the tab deletes sessionStorage. Before-unload warns about pending delivery. Storage failure keeps in-memory entries and warns the user to keep the tab open; corrupt persisted data is not overwritten. This is not an offline examination mode or indefinite durable evidence archive.

The backend derives a session/candidate-scoped deterministic evidence primary key from delivery UUID and checks the exact payload hash after authorization. Replays return existing evidence without repeating governance. Altered replay payloads and unauthorized access are refused. Legacy events retain existing behaviour. Existing primary-key uniqueness prevents duplicate inserts; a concurrent losing transaction may return an error and retry against the committed event. No schema migration/live database modification is required. Sequence/timestamps are browser-provided metadata, not trusted proof of observation time.

Completion is refused when the outbox reports unresolved entries/failures. Outstanding server policy/identity protection is not cleared by this queue. Existing policy evaluation, quality gates, model thresholds and examination modes remain intact.

Facial observations are serialized and generation-checked; late discovery cannot acquire a camera after unmount. Detector initialization is shared and release is terminal: a late-created task is closed instead of reactivated. Existing synchronous inference and camera acquisition architecture remain unchanged. Cleanup failures are recorded rather than becoming unhandled rejections.

## Verification

Final validation recorded on 22 October 2026:

| Check | Actual result |
| --- | --- |
| Clean dependency install | npm 11.21.0 `npm ci --no-audit --no-fund` passed; lockfile unchanged |
| Full backend regression | 110 passed, one Starlette/httpx deprecation warning |
| Final backend targeted regression | 22 passed after the missing authentication import correction; auth/RBAC and evidence API tests |
| Final full frontend regression | `npm test`: 148 passed across 21 files |
| Static checks | `npm run lint`, `npm run typecheck`, `git diff --check`: passed |
| Final production build | `npm run build -w apps/web`: passed, Next 16.2.12; isolated API URL http://127.0.0.1:34081 |
| Real browser/API integration | Headless Edge: staff login, portal initialization, refresh rotation, API outage retaining credentials, API reconnection and portal remount passed; no page errors/unhandled rejections observed |

The full backend suite preceded the last authentication import fix; the final 22-test targeted suite covers that change. The final frontend run includes the structurally corrupt outbox regression. Unit tests cover retained event identity/order, retry exhaustion/recovery, storage failures, replay authorization and duplicate governance suppression, detector ownership and existing camera/workspace mode regressions. Browser testing used a newly created synthetic SQLite fixture and ports 34001/34081; its own subprocesses were stopped afterward. No real candidate verification gate was bypassed. No real-camera/biometric acceptance is claimed.

Detailed logs and the browser harness/results are retained outside Git in `C:\Miva_Capstone\serps-runtime-evidence` (`frontend-closure.log`, `lint-closure.log`, `typecheck-closure.log`, `build-closure.log`, `backend-full.log`, `backend-final-targeted.log`, `browser-results.json`). Native services were not deployed or changed. The repair must be deployed with its frontend and backend idempotency changes together.

## Remaining acceptance limits

- Exact earlier MediaPipe messages and slow development request logs remain unavailable; their particular causes are unverified.
- Browser integration exercised staff authentication, not candidate biometric login or a live examination. Camera/inference regression tests use controlled doubles; hardware acceptance is pending.
- The outbox is tab-scoped, not an indefinite offline archive. Tab closure or storage loss can lose locally retained metadata; warnings and unresolved-delivery status are provided. Existing in-memory answer state is not converted to durable assessment storage.
- An event generated while the completion request is already in flight can remain unresolved if the server closes the session. It is retained/reported, not silently discarded; closed-session authorization is not relaxed.
- Request timeout covers receiving response headers; it is not a separate response-body deadline. Cross-tab delivery coordination and concurrent replay load testing are not claimed.
- Clean installation warned about unapproved sharp/unrs-resolver install scripts; the recorded frontend checks/build nevertheless passed. Dependency/security upgrades were outside this runtime repair.

## Changed files

- API/authentication: `apps/api/app/api/v1/routes/auth.py`, `apps/api/app/api/v1/routes/evidence.py`, `src/serps_pop/evidence/services.py`.
- Frontend runtime: `apps/web/src/lib/api.ts`, `apps/web/src/lib/evidenceDelivery.ts`, `apps/web/src/lib/faceDetection.ts`, `apps/web/src/lib/objectDetection.ts`, `apps/web/src/components/FacialVerification.tsx`, `apps/web/src/components/PortalShell.tsx`, `apps/web/src/app/candidate/examinations/[sessionId]/page.tsx`.
- Regression tests: `apps/web/src/lib/api.test.ts`, `apps/web/src/lib/evidenceDelivery.test.ts`, `apps/web/src/lib/detectorOwnership.test.ts`, `apps/web/src/lib/cameraWorkspace.test.tsx`, `tests/test_auth_rbac_sessions.py`, `tests/test_evidence_api.py`.
- Report: `docs/runtime_recovery_investigation.md`.

Physical follow-up requires genuine candidate enrolment/login, actual face/object inference, independent camera recovery, navigation/remount, network loss/recovery and OS sleep/resume on new synthetic sessions. Never use Trial17. Browser fixtures and unit doubles are tests only, not production responses or enrolment bypasses.
