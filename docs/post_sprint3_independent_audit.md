# SERPS Independent Post-Sprint 3 Audit

Audit date: 2026-07-20  
Repository audited: `C:\SERPS`  
Branch: `main`  
Audited HEAD: `b9861a2ae10c7b404ba6497306851e59546a8d96`

## Executive verdict

**Recommendation: ACCEPT WITH CONDITIONS.**

The committed repository contains the Sprint 3D implementation and Sprint 3E validation/documentation checkpoints in a single intact ancestry. Backend and frontend test/build verification passes. The bounded workflow is substantially implemented, but RC1 should be accepted only as a research prototype, not as a production or hardware-validated release.

The principal condition is an evidence-integrity defect: the EvidenceEvent write endpoint intentionally authorises Candidate, Administrator, Reviewer/Proctor, and System Administrator roles. The service applies candidate-user ownership and active-session checks only when the actor is a candidate without a privileged role. Consequently, a reviewer or administrator can inject browser-shaped evidence into any same-institution session and trigger the assessment/recommendation/policy chain. A second integrity gap is that governance audit records are append-only at the ORM layer, while the general identity `AuditLog` table has no equivalent mutation guard. These facts make broad claims of candidate-authoritative evidence and universally immutable audit ambiguous.

No critical finding was identified. No implementation or existing documentation was changed during this audit.

## 1. Repository identity and history

| Check | Result |
| --- | --- |
| `git rev-parse --show-toplevel` | `C:/SERPS` |
| `git branch --show-current` | `main` |
| `git rev-parse HEAD` | `b9861a2ae10c7b404ba6497306851e59546a8d96` |
| `git rev-parse origin/main` | Same as HEAD |
| `git status --short` before audit documents | Only `?? "Complete Assessment Platform.txt"` |
| `40bba15` ancestor of `1f61c31` | Yes, exit 0 |
| `1f61c31` ancestor of `b9861a2` | Yes, exit 0 |
| Sprint 3D implementation retained | Yes; commits `c292e6f` through `40bba15` remain in linear history |

`1f61c31` has `40bba15` as its direct parent. Therefore, a statement that the Sprint 3D documentation-copy operation itself started at `e81a574` is inaccurate. `e81a574` is the declared Sprint 3D baseline in the release notes. The implementation was then committed from `c292e6f` through `40bba15`, and the documentation commit followed as `1f61c31`. The likely explanation is that the sprint baseline and the later documentation operation's starting HEAD were conflated.

The untracked file is 211 bytes with filesystem creation and last-write timestamps both at `2026-07-20 06:57:24Z`. It remained untracked and unstaged throughout this audit, and its timestamp did not change. Because Git does not track the file and no prior trusted hash was recorded, Git history cannot independently prove that it was untouched before this audit.

## 2. Staging-versus-repository verdict

All 51 paths changed between `e81a574` and `b9861a2` exist in `C:\SERPS` and are committed. Hash comparison against the available `SERPS_SPRINT3D` staging directory found no implementation file that differed from the repository. `docs/openapi.json` exists in the repository but not in that staging copy. The only staging-only files were validation databases `migration_verify.db` and `sprint3e_seed_verify.db`; neither is required implementation.

Every changed path in `e81a574..b9861a2`:

```text
M .env.example
M README.md
M apps/api/app/api/v1/routes/candidate_workflow.py
M apps/api/app/api/v1/routes/governance.py
M apps/web/src/app/admin/page.tsx
A apps/web/src/app/admin/sessions/[sessionId]/page.tsx
A apps/web/src/app/candidate/examinations/[sessionId]/page.tsx
M apps/web/src/app/candidate/page.tsx
M apps/web/src/app/globals.css
M apps/web/src/app/layout.tsx
M apps/web/src/app/page.tsx
M apps/web/src/app/reviewer/page.tsx
A apps/web/src/app/reviewer/sessions/[sessionId]/page.tsx
A apps/web/src/components/OperationalStates.tsx
M apps/web/src/components/PortalShell.tsx
A apps/web/src/components/RoleNavigation.tsx
A apps/web/src/components/SessionOperationalView.tsx
A apps/web/src/components/operational.test.tsx
M apps/web/src/lib/api.test.ts
M apps/web/src/lib/api.ts
A apps/web/src/lib/contracts.ts
A apps/web/src/lib/operational.ts
M docker-compose.yml
A docs/demo_checklist.md
A docs/demo_script.md
A docs/dissertation_alignment_matrix.md
A docs/installation_guide.md
M docs/openapi.json
M docs/project_progress.md
A docs/prototype_limitations.md
A docs/release_notes_v0.3.md
M docs/security_review.md
M docs/sprint3_master_execution_plan.md
A docs/sprint3d_operational_interfaces_report.md
A docs/sprint3e_validation_report.md
A docs/system_administration_guide.md
M docs/technology_claim_matrix.md
A docs/troubleshooting.md
A docs/user_manual.md
A docs/version_1.0_release_candidate.md
A migrations/versions/0005_sprint3d_dual_camera.py
M scripts/dev/seed_demo_data.py
M src/serps_pop/candidate_workflow/models.py
M src/serps_pop/candidate_workflow/schemas.py
M src/serps_pop/candidate_workflow/services.py
A src/serps_pop/governance/operational.py
M src/serps_pop/governance/schemas.py
M src/serps_pop/governance/services.py
M src/serps_pop/identity/models.py
M tests/test_candidate_workflow.py
A tests/test_sprint3e_e2e.py
```

Diff summary: 51 files changed, 6,337 insertions and 1,437 deletions.

## 3. Capability summary

The full evidence mapping is in `post_sprint3_claim_traceability.md`.

| Classification | Summary |
| --- | --- |
| IMPLEMENTED | 18 capabilities: registration, auth, assignment consumption, consent, camera selections, session/workspace, persistence, governance chain, queue, decision, timeline, reports, and completion |
| PARTIAL / SIMULATED | Device and permission truth is client-attested and automated with API payloads; audit immutability is split between governance and identity records |
| METADATA ONLY | Reviewer detail, administrator dashboard camera state, and administrator session oversight |
| DOCUMENTATION ONLY | None of the required capabilities exists only in documentation |
| NOT IMPLEMENTED | Remote secondary-device pairing, WebRTC signalling, raw-video storage, secure browser, and full CBT/LMS are explicit non-capabilities |

## 4. Dual-camera implementation truth

- The candidate pages contain separate primary and secondary `MediaStream` references. Setup acquires a selected stream for each role, and the workspace uses `Promise.all` to acquire both selected devices. This is source-level support for two simultaneous local streams; it was not exercised with two physical devices in this audit.
- Duplicate selection is prevented in the UI by `validateCameraPair` and in the backend by `record_camera_selection`; the backend rejection is tested.
- Setup records permission denial. The workspace handles `getUserMedia` failure, video-track `ended`, device removal, and cleanup. These paths are not hardware-browser automated tests.
- Camera role, device selection, permission, and session foreign-key metadata are persisted. Camera connection/disconnection EvidenceEvents carry `camera_id` role linkage.
- Candidate pages display live **local** previews.
- Reviewer and administrator pages display explicit placeholders plus persisted metadata/status. They do not display remote video.
- A remote secondary physical device cannot pair or connect.
- No WebRTC peer connection, signalling, TURN/STUN, or remote-media transport exists.
- No raw video is stored; persistence is metadata and structured evidence only.

The defensible phrase is: **two distinct local camera inputs with local previews and persisted role/status metadata; reviewer/admin views are metadata-only.** “Dual-camera live monitoring” is misleading unless this qualification accompanies it.

## 5. Demonstration workspace boundary

The UI and principal documents consistently call the workspace a bounded demonstration harness and disclaim a complete CBT platform and secure browser. The workspace contains three static questions, navigation, elapsed time, camera lifecycle logic, and explicit completion. It has no scoring, authoring, autosave, question bank, operating-system lockdown, process/clipboard control, LMS integration, or SEB-equivalent controls.

The README, release notes, user manual, installation guide, demo script, candidate portal, and workspace wording generally respect this boundary. The main terminology issue is “live” on reviewer/admin queue and metrics summaries: those are current API-backed metadata, not remote live media.

## 6. Security audit

### Verified controls

- HMAC-signed access JWTs validate signature, issuer, token type, and expiry.
- Protected routes enforce bearer authentication and role dependencies.
- Candidate workspace, completion, and candidate-originated evidence enforce candidate ownership.
- Reviewer decision creation requires Reviewer/Proctor or System Administrator; administrators cannot submit decisions.
- Administrator endpoints require Administrator or System Administrator.
- Institution filtering and cross-institution denial are implemented and tested.
- Consent, device checks, camera selections, and camera permissions reject ORM update/delete.
- Governance assessments, recommendations, policies, evaluations, reviewer decisions, governance audit records, and report snapshots reject ORM update/delete.
- A database constraint and service checks prohibit `automatic_exam_termination_allowed=true`; policy evaluation continues the examination.
- Compose requires externally supplied database and JWT secrets. CORS defaults to local explicit origins, not wildcard origins.

### Material findings

1. **HIGH - privileged EvidenceEvent injection.** `POST /api/v1/evidence-events/` authorises Candidate, Administrator, Reviewer/Proctor, and System Administrator. Same-institution reviewer/admin actors can create candidate-linked evidence and trigger CIE, recommendation, and policy persistence. Existing tests deliberately use an administrator as an event submitter. Introduce a narrowly scoped ingestion identity or restrict browser evidence to the session-owning candidate before relying on evidence provenance.
2. **MEDIUM - identity audit is not append-only.** `GovernanceAuditRecord` is immutable, but `identity.models.AuditLog` is not in an ORM mutation-guard list. API exposure is read-only, which reduces reachability, but database/service mutation remains possible. Narrow “immutable audit” claims or protect and test the identity log.
3. **MEDIUM - JWT role and institution claims are not reloaded from current database assignments.** `get_current_user` confirms that the user exists and is active, then trusts token role/institution claims until expiry (default 20 minutes). Documented future current-role revalidation remains necessary.
4. **MEDIUM - readiness and permission records are attestations.** The browser genuinely invokes media APIs, but the API accepts client-supplied device and permission status. A caller can satisfy prerequisites without proving an active physical stream. The UI adds an in-memory stream-active check, but the server cannot independently verify it.
5. **MEDIUM - dependency advisories.** Fresh `npm audit` reports two moderate PostCSS vulnerabilities through Next.js. The offered forced fix downgrades to Next.js 9.3.3 and is breaking.
6. **LOW - development database credential defaults.** Settings and `.env.example` include `serps:serps` for local PostgreSQL. Production Compose requires explicit secrets, so this is not an embedded production secret, but installations must replace it.
7. **LOW - browser token storage.** Access and refresh tokens are stored in `sessionStorage`. Existing documents already identify hardened cookie/session design as future work.

### Search-term disposition

- `TODO`, `FIXME`, `HACK`: no material application-source occurrences.
- `password`, `secret`, `token`: configuration placeholders, test-only passwords, password hashing, token creation/refresh, session storage, and the environment-only demo password. No committed real credential was found.
- `localhost`: local development API, CORS, and database defaults.
- `mock`, `fake`: Vitest mocks and test doubles. No runtime fabricated camera feed exists.
- `placeholder`: reviewer/admin camera UI deliberately labels remote streaming unavailable and metadata-only.
- `simulate`: validation/documentation language for non-hardware inputs; no runtime feature silently claims simulated media as real.
- `terminate`: the generic identity session state machine supports explicit/manual termination, while governance policy prohibits **automatic** termination. These are not contradictory.
- `delete`, `update`: normal candidate administration, token revocation, SQL cascade declarations, and append-only mutation hooks. The material exception is the unguarded identity `AuditLog` described above.
- `hard-coded`: no matching source marker; the development database default is nevertheless a fixed non-production credential.

## 7. Documentation claim verification

| Document | Claim | Code evidence | Test evidence | Verdict | Required correction |
| --- | --- | --- | --- | --- | --- |
| `README.md` | Complete bounded workflow and candidate ownership | Routes/services/models exist | `test_complete_operational_workflow`, candidate spoof denial | PARTIAL | Qualify evidence provenance: privileged roles can inject same-institution events. |
| `README.md` | Immutable audit | Governance model guards; identity `AuditLog` unguarded | Governance mutation test only | AMBIGUOUS | Say “append-only governance audit” or protect/test identity audit too. |
| Sprint 3D report | Live reviewer queues/admin metrics | API-backed current queries | API/component tests | SUPPORTED WITH QUALIFIER | Replace/qualify “live” as current metadata; no remote live video. |
| Sprint 3D report | Browser guards and tablet overflow fully verified | Source guards/CSS exist | No durable browser E2E artifact in repository | NOT INDEPENDENTLY REPRODUCIBLE | Describe as a historical manual observation, not automated proof. |
| Sprint 3E report | Complete database-backed workflow test | Full route/service chain | One real-JWT SQLite integration test | SUPPORTED | Retain SQLite and simulated-device qualification. |
| Sprint 3E report | Final 32-test suite in 110.82 s | Test suite exists | Fresh audit: 32 pass in 131.65 s | HISTORICAL RESULT, COUNT SUPPORTED | Label timing as the Sprint 3E run, not a stable performance measure. |
| Sprint 3E report | Nine routes generated | Next build route table | Fresh build passes | INCORRECT COUNT | “9 static pages generated” is not route count; current table has 10 application routes excluding `/_not-found`. |
| Dissertation alignment matrix | Two distinct local devices/previews implemented | Two stream refs, distinct checks, dual acquisition | Duplicate test; no hardware E2E | SUPPORTED AT CODE LEVEL | Add “not hardware-verified” in the same table row. |
| Dissertation alignment matrix | Forty live OpenAPI paths | Runtime OpenAPI generated in memory | Stored/live documents exactly equal, 40 paths | SUPPORTED | Prefer “40 registered API paths” to avoid server-runtime ambiguity. |
| Prototype limitations | Reviewer/admin metadata-only; no WebRTC/raw video | Explicit `stream_mode=metadata_only`, placeholder, no WebRTC symbols | Camera status tests | SUPPORTED | None. |
| Security review | Audit/report payloads omit passwords/tokens/raw video | Report field allowlists and audit metadata | Workflow/report equality tests | SUPPORTED | None. |
| Security review | No critical defect found | This audit found no critical issue | Full tests pass | SUPPORTED, WITH HIGH FINDING | Add privileged evidence-injection and identity-audit distinctions after approval. |
| Technology claim matrix | PostgreSQL configured, unverified | Compose/psycopg configuration | Runtime unavailable | SUPPORTED | None. |
| Technology claim matrix | Reviewer/admin portals implemented | Routes/components/API clients present | API/component tests | SUPPORTED AS METADATA | Keep remote-media limitation adjacent. |
| RC1 document | Real JWTs for three roles in complete workflow | Auth and route enforcement | `test_sprint3e_e2e.py` | SUPPORTED | None. |
| RC1 document | Nine-route build | Current build route table | Build passes | INCORRECT COUNT | Use “production build passed” or accurately count 10 application routes. |

## 8. Fresh verification from `C:\SERPS`

| Command | Exact audit result |
| --- | --- |
| `python -m py_compile apps\api\app\main.py` | Exit 0; 0.52 s. |
| `python -m pytest -q` | 32 passed in pytest-reported 131.65 s; wrapper 135.67 s; exit 0. |
| `python -m alembic heads` | `0005_sprint3d_dual_camera (head)`; exit 0; 2.80 s. |
| `python -m alembic history` | Linear `0001` through `0005`; exit 0; 2.76 s. |
| `python -m alembic upgrade head` | No output and no completion after more than 60 s because the default PostgreSQL target was unavailable; audited processes were stopped. No success claimed. |
| `python -m alembic current` | No output and no completion after more than 60 s for the same unavailable database; audited processes were stopped. |
| `npm.cmd run typecheck -w apps/web` | Exit 0; 18.17 s. |
| `npm.cmd run lint -w apps/web` | Exit 0; 25.28 s. |
| `npm.cmd run test -w apps/web` | 2 files, 18 tests passed; Vitest 1.53 s, wrapper 5.81 s; exit 0. |
| `npm.cmd run build -w apps/web` | Exit 0; 55.47 s. Compile 20.6 s, TypeScript 18.5 s, static generation 9/9. Route table contains 10 application routes plus `/_not-found`. |
| `docker compose config` | Exit 1 in 0.77 s: required `SERPS_POSTGRES_PASSWORD` missing. |
| Compose config with temporary required audit values | `docker compose config --quiet` exit 0. |
| `npm.cmd audit --workspace apps/web --audit-level=moderate` | Exit 1; two moderate PostCSS vulnerabilities; breaking forced fix only. |
| Runtime/stored OpenAPI comparison | 40 paths in each; path keys and full documents equal. |
| `docker version` | No output after more than 60 s; process stopped. Docker engine unavailable. |

## 9. Manual demonstration readiness

The documented sequence is coherent, but a complete manual demonstration cannot be executed in the present repository environment without preparation:

- `.env` is absent and none of `SERPS_DATABASE_URL`, `SERPS_JWT_SECRET`, `SERPS_DEMO_PASSWORD`, or `SERPS_POSTGRES_PASSWORD` is currently set.
- The bare seed command exits 1 with `RuntimeError: Set SERPS_DEMO_PASSWORD before seeding demonstration users.` This is correct secret handling, but it is a current blocker.
- PostgreSQL/Docker is unavailable, so migration, seed, persistence, reviewer decision, and report generation cannot presently run against the documented target database.
- Two physical browser-visible cameras were not available or exercised in this audit.
- No API or frontend server was started for a manual walkthrough; route accessibility is supported by the successful build and source/test evidence, not claimed as manually passed.

Once a database and required environment values are supplied, the seeder creates these identities with the single operator-supplied demo password:

- `candidate@miva.edu.ng`
- `reviewer@miva.edu.ng`
- `admin@miva.edu.ng`
- `sysadmin@serps.local`

Startup commands are correctly documented as Uvicorn on port 8000 and `npm.cmd run dev -w apps/web` on port 3000. The seed creates an eligible assignment but no premature session. Expected events include camera connection/disconnection, focus loss, and optional FaceDetector outcomes. Expected reviewer/admin outcomes are metadata status, assessments, policy/recommendation, human decision, audit/timeline, metrics, and report snapshots.

## 10. PostgreSQL status

**UNVERIFIED.** Alembic metadata inspection succeeds without a connection, but database-dependent `upgrade head` and `current` did not complete. Docker engine discovery also did not complete. No PostgreSQL container, connection, migration, seeded workflow, reviewer decision, or report generation was verified in this audit.

## 11. Findings by severity

### Critical

- None identified.

### High

- H-1: Same-institution reviewer/administrator actors can submit EvidenceEvents and trigger the governance chain, weakening evidence provenance.

### Medium

- M-1: Identity `AuditLog` lacks append-only mutation guards while documentation sometimes says “immutable audit” generally.
- M-2: JWT role/institution claims remain authoritative until token expiry rather than being reloaded from current assignments.
- M-3: Server readiness trusts client-submitted device/permission attestations; only the UI checks active local streams.
- M-4: Two moderate PostCSS/Next.js dependency advisories remain.
- M-5: PostgreSQL and hardware-backed dual-camera execution remain unverified acceptance conditions.

### Low

- L-1: “Nine routes” confuses generated static-page count with the build route table.
- L-2: “Live” reviewer/admin language can be mistaken for live remote video despite adjacent metadata-only disclosures.
- L-3: The prior browser/tablet walkthrough has no durable automated evidence artifact in the repository.
- L-4: A fixed local `serps:serps` database credential remains in development defaults/examples.
- L-5: Browser tokens use session storage and all seeded demo roles share one operator-supplied password.

## Acceptance conditions

1. Before relying on evidence integrity, restrict event ingestion to the owning candidate or a dedicated, independently authenticated ingestion principal and add negative reviewer/admin injection tests.
2. Protect the identity `AuditLog` against update/delete or narrow all immutability claims to governance audit records.
3. Correct the route-count and ambiguous “live”/audit wording only after findings are approved.
4. Before any production-pilot claim, pass migrations and the full workflow against real PostgreSQL, execute a two-camera hardware browser walkthrough, address token/session hardening and dependency advisories, and perform security/load testing.

## Audit change control

Created only:

- `docs/post_sprint3_independent_audit.md`
- `docs/post_sprint3_claim_traceability.md`

No implementation code or pre-existing documentation was changed. Nothing was committed or pushed.
