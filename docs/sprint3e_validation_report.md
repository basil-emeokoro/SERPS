# Sprint 3E End-to-End Validation Report

## Executive result

SERPS satisfies the Sprint 3E research-prototype definition of done and is classified as **Research Prototype Version 1.0 Release Candidate (RC1)**. The complete application workflow is validated in one database-backed API integration test, supported by the full regression suite, frontend tests, production build, migration cycle, and prior bounded browser inspection. PostgreSQL and real two-camera browser hardware were unavailable in this environment and are not claimed as verified.

Starting checkpoint: `1f61c31d5fb91f0174da39afacf6c921ba51769a` on `main`.

## End-to-end workflow record

| Stage | Status | Evidence and boundary |
| --- | --- | --- |
| Candidate registration | Verified | Real registration API persists linked candidate/user records in `test_complete_operational_workflow`. |
| Authentication | Verified | Candidate, reviewer, and administrator obtain and use real signed JWT access tokens. |
| Consent | Verified | Accepted versioned consent persisted; append-only behavior covered by regression tests. |
| Device readiness | Simulated | API receives a browser-shaped readiness attestation; no physical device was available to this test runner. |
| Primary camera | Simulated/verified contract | Distinct primary metadata and granted permission persisted; browser media acquisition remains hardware-dependent. |
| Secondary camera | Simulated/verified contract | Distinct secondary metadata and granted permission persisted; duplicate-device rejection is tested. |
| Session creation | Verified | Candidate-authoritative start enforces all prerequisites and links their exact record IDs. |
| Demonstration workspace | Partially verified | Candidate-owned workspace API and protected route verified; physical camera interaction was unavailable. |
| EvidenceEvent generation | Verified with simulated inputs | Connected, focus-loss, face-absence, and secondary-disconnection events persist with camera-role linkage. |
| Contextual Intelligence Engine | Verified | Latest assessment contains the adverse evidence window, score, level, confidence, and explanation. |
| Agent recommendation | Verified | Bounded recommendation is persisted and requires human review at elevated risk. |
| IPIME | Verified | Active/default institutional policy is evaluated and persisted without automatic misconduct determination. |
| Reviewer queue | Verified | Real reviewer JWT retrieves the institution-scoped unresolved queue. |
| Reviewer decision | Verified | Supported decision with mandatory rationale is appended and returned. |
| Administrator oversight | Verified | Real administrator JWT retrieves completed-session metrics and dual-camera state. |
| Audit | Verified | Identity audit and governance audit entries are returned; mutation rejection has regression coverage. |
| Reports | Verified | Structured report is generated, persisted, retrieved, and equality-checked. |

## PostgreSQL status

`docker compose config` succeeds with explicitly supplied validation-only secrets. Approved `docker info` remained unresponsive for more than 60 seconds without output, matching the prior Docker Desktop engine failure. No container, PostgreSQL connection, migration, or PostgreSQL persistence success is claimed.

The full migration chain was verified using a fresh SQLite database: upgrades `0001` through `0005`, reports `0005_sprint3d_dual_camera` as the single head, downgrades `0005` to `0004`, and re-upgrades to `0005`. The corrected demo seeder then created four users, one eligible assignment, and zero premature sessions.

## Production build verification

| Command | Exact result |
| --- | --- |
| `python -m py_compile apps/api/app/main.py` | Passed, exit 0. |
| `python -m pytest -q --durations=10` final RC1 suite | 32 passed in 110.82 s. |
| `python -m pytest -q --durations=10` before RC test | 31 passed in 120.17 s; one restricted pytest-cache warning. |
| `python -m pytest tests/test_sprint3e_e2e.py -q --durations=5` | 1 passed in 21.60 s; test call 13.59 s; restricted cache warning only. |
| `npx tsc --noEmit --incremental false` | Passed, exit 0. |
| `npm.cmd run test -w apps/web` | 2 files and 18 tests passed in 3.47 s. |
| `npm.cmd run lint -w apps/web` | Passed, exit 0. |
| `npm.cmd run build -w apps/web` | Passed; compiled in 19.2 s, TypeScript 18.7 s. The application defines ten routes (excluding `/_not-found`); the build's separate static-generation phase reported nine pages. |
| `docker compose config` | Passed with required secret variables supplied. |
| `python -m alembic heads` | `0005_sprint3d_dual_camera (head)`. |
| `npm audit --workspace apps/web --audit-level=moderate` | Historical Sprint 3E result: two moderate PostCSS findings. Sprint 3F safely upgraded/overrode PostCSS to 8.5.18 and the current audit reports zero vulnerabilities. |

## Security review

| Control | Result | Notes |
| --- | --- | --- |
| RBAC and API authorization | Confirmed | Server dependencies enforce role sets; frontend navigation is supplementary only. |
| Institution isolation | Confirmed | Candidate, reviewer, and administrator cross-institution access has negative tests. |
| JWT | Hardened in Sprint 3F | HS256 signature, issuer, audience, type, expiry, issue time, subject, role, and institution are validated; protected requests reload active user state and compare trusted role/institution data. Existing access tokens remain usable until their short expiry after refresh-token revocation. |
| Candidate ownership | Confirmed | Session retrieval, completion, evidence ingestion, and assignments enforce the authenticated candidate. |
| Reviewer permissions | Confirmed | Reviewer-only decision endpoint and institution scope tested. |
| Administrator permissions | Confirmed | Oversight is institution-scoped and cannot submit reviewer decisions. |
| Camera permissions | Confirmed at contract boundary | Permission outcomes are persisted attestations; browser/OS permission integrity remains future hardening. |
| Consent immutability | Confirmed | ORM update/delete hooks and tests enforce append-only records. |
| Governance/audit immutability | Confirmed | Assessment, recommendation, policy, decision, audit, and report snapshots reject mutation/deletion. |
| Policy evaluation | Confirmed | Deterministic policy evaluation remains advisory and prohibits automatic exam termination. |
| Secrets | Improved | Compose now requires database/JWT secrets; `.env` remains ignored; no committed operational credentials found. |
| Dependencies | Resolved for the audited finding | PostCSS 8.5.18 is deduplicated across the workspace and `npm audit` reports zero vulnerabilities. Major ESLint/TypeScript upgrades were intentionally deferred. |

Future security work: cookie-backed browser sessions, CSRF protection for that session model, security headers, rate limiting, key rotation, immediate access-token revocation/versioning, external secret management, PostgreSQL tenancy tests, and privacy/retention policy enforcement.

## Performance review

Observed test-client timings are development measurements, not production benchmarks. The final 32-test suite completed in 110.82 s and is dominated by PBKDF2 authentication. Its slowest calls were the integrated workflow (10.66 s), administrator/candidate uniqueness (10.02 s), candidate-forbidden access (9.74 s), session transitions (9.37 s), login/refresh/logout (8.81 s), and generic login failure/audit (8.65 s). The integrated workflow includes three password-based logins plus seven evidence-triggered governance chains. Frontend tests completed in 3.47 s; the production build completed successfully.

Potential bottlenecks:

- Each EvidenceEvent recalculates over the current session window and appends assessment, recommendation, policy evaluation, and audit records.
- Administrator metrics and reviewer queues perform per-session assessment and camera queries, creating an N+1 scaling risk.
- PBKDF2 is deliberately CPU-expensive and requires capacity planning.
- Synchronous request processing couples evidence ingestion to governance persistence.

Scaling recommendations: profile before tuning; batch/debounce high-frequency evidence; add bounded queues/workers with idempotency; aggregate metrics in set-based queries or materialized views; index measured query paths; paginate timelines/reports; pool PostgreSQL connections; load-test realistic session/event concurrency; and scale authentication separately. None is required for the bounded RC1 demonstration.

## Final repository review

- Import, type, lint, test, build, route, and migration checks pass.
- OpenAPI was regenerated from 17 stale paths to all 40 documented REST paths.
- No tracked bytecode, `.next`, `.env`, node modules, debug statements, TODO/FIXME markers, or operational secrets were found.
- The demo seeder no longer creates a session that bypasses candidate readiness and now requires an explicit password.
- Documentation consistently distinguishes local live camera preview, simulated validation input, metadata-only reviewer/admin views, and unimplemented enterprise streaming.
- Dissertation files were read for alignment only and not modified.

## Residual limitations

PostgreSQL, real two-camera hardware, FaceDetector availability, remote media transport, secure-browser controls, production deployment, load testing, and institutional integration remain outside the verified environment. These are recorded in `prototype_limitations.md` and do not invalidate the bounded research workflow.
