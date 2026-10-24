# Conditional GO: isolated evidence-integrity remediation

23 October 2026. This report supplements `runtime_recovery_investigation.md` and supersedes its concurrency limitations where explicitly tested below. Native integration remains subject to a separate **NATIVE INTEGRATION GO**. No native service restart, source integration, push or public deployment is authorized or performed by this phase.

## Backup and rollback verification

The operator confirmed that the running API uses `C:\SERPS\.env` with no database URL override. Windows did not expose the running API process environment to this session, so that confirmation is part of the configuration evidence. The SQLite path resolves outside the repository; copying C:\SERPS alone would not preserve its records.

A read-only SQLite source connection and SQLite backup API created a consistent snapshot. That snapshot was restored through the same backup mechanism into a second disposable database. Both passed integrity checking, had zero foreign-key violations and identical logical dumps/table counts across all 30 tables. The recorded migration revision is `0009_exam_management_courses`. No migration, reseed or write was performed against native data; all records, including any Trial 17 records present in the database snapshot, were copied without selecting or changing that trial.

The checkpoint directory `C:\Miva_Capstone\serps-runtime-evidence\conditional-go` is restricted to the current Windows account and SYSTEM. It contains a verified Git bundle, worktree/index patches, Git status, checksum-verified copies of `.env`, `.env.example`, `Run SERPS Locally.txt`, `apps/web/.env.local`, `apps/web/.env.local.pre8765` and the modified `apps/web/next-env.d.ts`, plus the snapshot, disposable restore and private verification manifest. Secret-bearing files/database contents are not in Git or printed in this report. Source file hashes and Git status matched at completion of the backup operation.

The source database path and per-table counts are recorded in the restricted `backup-verification.json`. Backup integrity proves a recoverable point-in-time snapshot, not coverage of later writes by the still-running native services. Before any eventual native cutover, refresh the backup/checkpoint. Prefer code-only rollback while retaining all later database writes. Restoring an old snapshot over live data is not an automatic rollback step.

## Reproduced defects and corrections

### Corrupt evidence queue

Before correction, retry cleared the failure even though corrupt saved data still prevented delivery. A regression test reproduced that disappearance when no new events were in memory. The correction makes the corruption barrier persistent in every snapshot and makes retry publish that state without clearing it or touching stored data. The UI explicitly displays investigation-required status and disables ordinary retry for corrupt storage. Completion remains blocked by the failure. New recoverable in-memory evidence and original unreadable storage are retained; corruption is not silently purged or treated as an empty delivered queue. Normal network/authorization retry behavior is unchanged. Corrupt data requires investigation; automatic reconstruction of unreadable contents is not claimed.

### Concurrent replay and transaction failure

The controlled interleaving reproduced one evidence row but two contextual assessments, recommendations and policy evaluations. Simultaneous insertion also reproduced a unique-key exception. Failure injection after each governance stage demonstrated that partial work could remain in the Session and be committed by a caller that caught the exception (normal request dependency cleanup would ordinarily roll it back).

The fix removes the route's separate preflight replay lookup. A single database `INSERT ... ON CONFLICT DO NOTHING ... RETURNING` against the existing evidence primary key determines whether the current transaction created the event. Only the insert winner executes governance. A loser reads and validates the committed payload fingerprint and returns the existing event without governance. The route commits evidence and governance together and explicitly rolls back any persistence/governance/commit exception. A failed claim is therefore retryable. Authorization, institution/candidate ownership, active-session checks, allowed sources/types and changed-payload rejection remain before or alongside persistence; no verification or policy gate is relaxed.

SQLite and PostgreSQL dialect implementations are provided. SQLite must support RETURNING (3.35 or later); verify the eventual native API interpreter meets that requirement before cutover. No schema migration, dependency upgrade, detector threshold/model change or policy configuration change is included. The legacy domain-returning service function remains available; the API uses a new service result carrying the insert-ownership flag. This is database arbitration, not a process-local lock. Exactly-once governance here is scoped to the same stable delivery identity; events without an identity retain legacy behavior, and distinct identities are distinct events.

## Validation evidence

- Before-fix logs: `frontend-reproduction.log` records the corrupt-retry failure; `backend-reproduction.log` records both concurrency failures and three failure-injection failures.
- After-fix focused backend: **18 passed**, including simultaneous/interleaved duplicate requests with independent SQLite connections and rollback/retry after assessment, recommendation and policy-stage failures.
- After-fix focused queue: **6 passed**. The accompanying camera-workspace worker failed to start (Vitest worker-response timeout), so that combined invocation is not counted as a clean pass. Full frontend validation uses one worker and no parallel files to reduce process-start contention; production code/timeouts were not altered for this runner issue.
- The full fork-worker attempt completed 91 tests in 12 files with nine worker-start errors. A single-thread-worker retry completed 112 tests in 17 files with four worker-start errors. These are incomplete runs, not full-suite passes. Only the four remaining files (camera workspace, camera lifecycle, reviewer pages and reviewer detail) are being retried; no assertions or application timeouts were relaxed.
- Final targeted frontend retry: **37 passed across all four remaining files** in 57.59s (`frontend-remaining-retry.log`). Combined with the 112 passing tests, all **149 tests across 21 files** passed across runs; this is not a claim of one uninterrupted full-suite pass.
- Full backend run: **115 passed, one failed** in 3696.88s. The operational workflow expected a connected primary camera but observed unavailable. Its isolated rerun passed unchanged in 46.41s (`backend-e2e-retry.log`). All 116 backend tests therefore have passing evidence across runs; the original timing-sensitive failure remains recorded rather than erased.
- TypeScript, lint and isolated production build: **passed**, each exit 0 (`static-results.json`). No application threshold or timeout was changed for validation.
- Final preservation verification: native HEAD, Git status and all six preserved file hashes remain unchanged. Ports 3100 and 8765 were not reachable at the final read-only probe; this phase did not stop, start or modify either service. Native runtime availability must be checked before any later acceptance/cutover.

Logs are in the restricted checkpoint directory. Tests use disposable SQLite databases, not the native database. Physical candidate/camera acceptance is pending; mocked camera tests and staff browser smoke tests are not physical acceptance.

## Files in this follow-up

- `apps/web/src/lib/evidenceDelivery.ts`: persistent corruption barrier and investigation flag.
- `apps/web/src/app/candidate/examinations/[sessionId]/page.tsx`: explicit blocked status and disabled ordinary retry.
- `apps/web/src/lib/evidenceDelivery.test.ts`: corrupt retry regression.
- `src/serps_pop/evidence/services.py`: atomic database claim/result.
- `apps/api/app/api/v1/routes/evidence.py`: winner-only governance and explicit transaction rollback.
- `tests/test_evidence_api.py`: concurrent replay and stage-failure regressions.
- `docs/runtime_recovery_conditional_go.md`: this report.

## Remaining limits and native integration proposal

Final review package: six modified source/test files and this new report; `git diff --check` passes. Follow-up remains uncommitted for the mandatory review gate. Proposed commit title: `fix(evidence): make replay governance atomic and retain corrupt queue barriers`. `proposed-followup.patch` and `proposed-native-integration.patch` in the restricted checkpoint directory contain the tracked diffs; this new report is supplied separately. Existing isolated HEAD is `ace87292486461236166e16f5c7bf3cf8fcbd5d9`. No native integration, push or deployment was performed.

The backend workflow's connected/unavailable result depends on the existing 35-second wall-clock heartbeat freshness check in `governance/operational.py`. The long-run failure and unchanged successful retry are consistent with test execution delay; no production freshness control was weakened. The suite is still susceptible to this timing failure on a heavily delayed runner.

The queue remains tab-scoped sessionStorage: tab loss/storage corruption cannot guarantee indefinite offline retention. The previously documented completion-in-flight race remains: newly generated evidence can be retained but rejected after session completion. Requests have a response-header deadline, not a separate body deadline. PostgreSQL live concurrency has not been exercised in this native SQLite phase. Browser crashes, power loss and real-camera behavior are not proven by these tests.

Recent user logs supersede the earlier 'logs unavailable' note: API refresh/workspace/evidence requests succeeded; the examination page timing was 5.1s (Next.js 4.7s, application 346ms). This does not isolate backend, rendering or inference latency. MediaPipe's XNNPACK INFO message uses console.error through its WASM output plumbing; no global filtering was introduced.

Subject to passing final validation and explicit NATIVE INTEGRATION GO, preserve the native original branch, create `codex/integrate-runtime-recovery` at `97322281c63929f21c96c3aa66ebdb06a4f8b730`, and cherry-pick recovery `ace87292486461236166e16f5c7bf3cf8fcbd5d9` plus the validated follow-up as a coherent frontend/backend unit. Preserve the unrelated generated-file edit and both untracked files exactly. Keep Phase 4 separate. Rebuild for the native backend URL rather than copying the isolated port-34081 build. Coordinate any future cutover with an idle maintenance window; do not allow an API auto-reloader to consume a partially applied patch. No push is proposed.
