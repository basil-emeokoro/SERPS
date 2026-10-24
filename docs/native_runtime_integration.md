# Native runtime recovery integration

Completed 24 October 2026, continuing the 23 October checkpoint. Scope: the reviewed runtime recovery and evidence-integrity follow-up, not unrelated Phase 4 changes. Branch: `codex/native-runtime-recovery`, based on `97322281c63929f21c96c3aa66ebdb06a4f8b730`. The original recovery `ace87292486461236166e16f5c7bf3cf8fcbd5d9` was cherry-picked as `b05c171f530745366f4622b6245432d8b799e7cb` without conflict. The six-file follow-up and conditional-GO report bring the reviewed recovery inventory to 18 files. README/deployment documentation is a separate publication update. The conditional-GO report is historical pre-integration evidence; this document supersedes its pending native-integration status.

## Preservation and rollback

A new access-restricted checkpoint was created before integration, separate from the previous conditional-GO checkpoint. It contains a verified complete-history Git bundle, worktree/index patches, status, six checksum-verified local/environment files, SQLite snapshot and disposable restoration. Both databases passed integrity checks, zero foreign-key violations, migration revision `0009_exam_management_courses`, counts across 30 tables and identical logical dumps. Private paths, database contents, credentials and logs are not published.

The native generated `apps/web/next-env.d.ts` modification, `Run SERPS Locally.txt`, `apps/web/.env.local.pre8765` and all existing environments are excluded from commits and preserved byte-for-byte. No native reseed, migration or database restoration is part of this recovery.

For rollback, arrange an idle maintenance window; identify only the API/frontend processes started for this integration. Stop those processes, preserve any subsequent local changes and take a new consistent database snapshot before any data recovery. Return to the original baseline branch only after checking unrelated changes will be preserved. Restore the prior frontend build retained during installation, or rebuild the baseline with the same API URL. Never use reset/clean/stash or restore an old database over later writes automatically. This patch adds no schema migration. Any database restoration requires separate approval and a disposable restoration check first.

## Native configuration

The verified launch interpreter is `C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe` (Python 3.13.6, SQLite 3.50.4). Its in-memory insert/conflict/RETURNING probes passed. Launch from `C:\SERPS` so the existing root `.env` supplies the native database and authentication configuration. Do not use a test database override in the native API terminal.

```powershell
cd C:\SERPS
$env:PYTHONPATH = 'C:\SERPS\src'
& 'C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe' -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8765
```

The existing frontend `.env.local` targets `http://127.0.0.1:8765`; root `.env` has an older public API value for port 8000. Preserve both files and resolve precedence explicitly with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8765` in the production build process. This variable is compiled into the browser bundle; setting it only at server startup does not change an old build. Use `npm run start -w apps/web -- --hostname 127.0.0.1 --port 3100` after a successful correct-target build. Do not copy the earlier isolated port-34081 build.

Next.js generates `next-env.d.ts` during builds. To preserve the existing native modification, build identical reviewed frontend source in the isolated checkout, verify source identity, then install only the build output while preserving the previous output for rollback. No source or environment files are replaced by this build transfer.

## Validation and acceptance boundary

Post-integration validation recovered from saved logs and exit codes, without repeating completed checks:

| Check | Result |
| --- | --- |
| Native full frontend suite | 149 passed across 21 files |
| Native full backend suite | 116 passed in 339.57s; no failures |
| TypeScript and lint | Passed, exit 0 each |
| Production build | Passed, exit 0; API target `http://127.0.0.1:8765` |
| Source/preservation verification | All 18 reviewed files identical to approved source; all six preserved-file hashes unchanged |
| Isolated browser acceptance | Passed staff login, portal initialization, refresh rotation, API outage credential retention, reconnection and portal remount; no observed page errors/unhandled rejections |
| Native startup smoke | API health and frontend login HTTP 200; ten served script files byte-matched installed build |

Installed build ID: `8G2m3xDj1q7zLUh8VKG-B`. The prior native build was retained in the restricted checkpoint. The browser bundle contains target 8765 and not the old isolated 34081 target. Native services were started only after backup and integration validation; no migration or seeding was performed. Native smoke requests were read-only health/login-page requests, not candidate operations.

Initial backend/static/build command sessions disappeared before recording results and were inconclusive. Only those incomplete checks were retried; the completed frontend suite was retained. The successful full backend run includes evidence concurrency, governance failure-injection/rollback, ownership/institution isolation, authentication and audit/reporting regressions. Unit tests use disposable synthetic databases and camera doubles. Browser acceptance used a disposable synthetic staff database on ports 34001/34081, with test-only request routing from the compiled API target to the isolated API. Those test processes were stopped by the harness. No routing override was added to production code. This proves staff authentication and transport recovery, not real candidate biometric acceptance or the completion-in-flight race.

The earlier timing-sensitive backend failure did not recur in this complete native run; the 35-second freshness control remains unchanged. `git diff --check` is required before each publication commit. Logs, exit codes, source checks, launch process IDs and health results are retained outside Git in the restricted native-integration checkpoint. No sensitive logs or database artifacts are included in the publication.

Required physical acceptance, using new synthetic sessions only: genuine candidate enrolment/login; independent primary/secondary camera initialization, disconnection and recovery; EfficientDet/MediaPipe stability; navigation/remount; foreground/background/minimisation; API interruption/recovery; OS sleep/resume. Protection must remain until required connectivity and monitoring readiness recover. Never execute Trial 17 for acceptance. Do not infer successful physical acceptance from previews, unit tests or HTTP health.

The completion-in-flight race remains: an event generated after the completion request begins can be rejected after the session closes. Retention and visible failure do not resolve that integrity boundary. Session storage remains tab-scoped; corrupt storage requires investigation, and closing the tab can lose locally retained evidence. Live PostgreSQL concurrency, response-body timeout behavior and hardware/browser crash recovery remain limitations. No dependency security remediation or public deployment is claimed.
