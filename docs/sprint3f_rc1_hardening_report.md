# Sprint 3F RC1 Hardening Report

## Executive result

Starting HEAD: `b9861a2ae10c7b404ba6497306851e59546a8d96` on `main`.

Sprint 3F resolves the independent audit's high-severity application findings, remediates the verified dependency finding, corrects public claims, and produces defence evidence. Docker/PostgreSQL and physical dual-camera execution were unavailable, so the final classification is:

**Research Prototype Version 1.0 RC1 — Environment Validation Pending**

SERPS is ready for a bounded dissertation demonstration with the limitations in this report. It is not production-ready.

## Audit disposition

| Audit Finding | Severity | Resolution | Verification | Status |
| --- | --- | --- | --- | --- |
| Candidate EvidenceEvent endpoint accepted reviewer/administrator input | High | Restricted creation to the owning candidate, same institution, permitted active state, allowlisted types, and `candidate_browser`; authorization failure occurs before governance processing | Evidence/candidate tests and full 51-test suite | Resolved |
| Identity AuditLog lacked append-only protection | High | ORM update, deletion, and replacement guards added; history remains retrievable | Four focused immutability tests and full suite | Resolved at application/ORM boundary |
| JWT role/institution claims remained trusted until expiry | High | Strict HS256/issuer/audience/type/expiry/iat/subject/role/institution validation; short access lifetime; active DB user and claims revalidated per protected request | Token-security, auth, RBAC, disabled-user, and full-suite tests | Resolved proportionately |
| Device/permission readiness could be mistaken for server proof | Medium | Schemas reject extra/invalid values and records identify browser-attested source, context, status, timestamps, server receipt, and client-reported trust boundary | Ownership/isolation/value tests, OpenAPI regeneration, UI wording | Resolved |
| Operational documentation blurred routes/static pages and local/remote video | Low | Ten application routes distinguished from nine generated static pages; reviewer/admin panels labelled metadata/API-backed; remote streaming boundaries made explicit | Documentation search, production build, browser inspection | Resolved |
| Two moderate PostCSS advisories | Medium | Compatible PostCSS 8.5.18 direct dependency/override, deduplicated for Next.js and Vite | `npm audit`: zero vulnerabilities; frontend gate | Resolved |

## Corrective checkpoints

- `07966c2` — independent audit documents.
- `f1a5c8c` — candidate evidence authorization.
- `8a9190f` — identity audit append-only guards.
- `19548e3` — JWT and trusted-claim hardening.
- `1e0d08e` — browser-attestation boundaries.
- `9e334be` — compatible dependency remediation.
- `5cfadf0` — reproducible environment configuration.
- `b31e46a` — complete-workflow fixture aligned with the hardened evidence source.

## Security evidence

Candidate evidence creation is denied for another candidate, another institution, reviewer/administrator actors, disallowed event types, disallowed sources, and invalid session state. Denied submissions do not create CIE assessments, recommendations, IPIME evaluations, governance audit entries, or reports.

Identity AuditLog is append-only through supported SQLAlchemy ORM interfaces. No database trigger or database-level immutability claim is made.

Access tokens default to ten minutes and require environment-supplied secrets. Logout/revocation invalidates refresh tokens; an already-issued access token remains usable until its short expiry. Browser tokens still use session storage. Immediate access-token revocation, hardened cookies, CSRF design, TLS/security headers, rate limiting, rotation, central secret management, PostgreSQL tenancy tests, and penetration testing remain production work.

## Dependency evidence

PostCSS 8.5.18 is used by the root workspace, Next.js, and Vite. `npm audit` reports zero vulnerabilities. ESLint 10 and TypeScript 7 major upgrades were reviewed but deferred because they are unrelated breaking changes and are not required to resolve the audit.

## Environment and database evidence

`docker compose config --quiet` passed with the ignored local validation environment. `docker version`, `docker info`, `docker compose up -d db`, and `docker compose ps` produced no usable response within bounded waits. No existing local PostgreSQL service or `psql` installation was found. No infrastructure was installed.

A temporary SQLite database outside the repository was used only for bounded validation. Alembic upgraded 0001 through 0005, reported `0005_sprint3d_dual_camera`, and the demo seeder created four role accounts and an eligible examination assignment. This is not PostgreSQL evidence.

## Manual demonstration record

Automated tests are not counted as manual passes. The browser used the production Next.js build and a temporary SQLite-backed API.

| Step | Result | Manual evidence / boundary |
| --- | --- | --- |
| Candidate registration | Simulated | Seeded demo candidate used; registration remains API-tested, not manually re-created in this run. |
| Authentication | Passed | Candidate, reviewer, and administrator signed in through the browser UI with role-aware redirects. |
| Consent | Passed | Candidate accepted `CONSENT-1.0`; UI confirmed a new immutable record and readiness changed to pass. |
| Device readiness | Environmental blocker | Browser reported fewer than two video-input devices. |
| Primary camera selection | Environmental blocker | No selectable camera exposed in the controlled browser. |
| Secondary camera selection | Environmental blocker | No second device exposed; readiness correctly remained false. |
| Session start | Environmental blocker | Correctly disabled because device/camera prerequisites were unmet. |
| Demonstration workspace | Environmental blocker | Not entered because bypassing readiness would invalidate the manual evidence. |
| EvidenceEvent generation | Simulated | Verified by the integrated workflow and focused tests, not manually generated after blocked session start. |
| CIE processing | Simulated | Persisted chain verified by tests against browser-shaped inputs. |
| Agent recommendation | Simulated | Persisted advisory output verified by tests. |
| IPIME evaluation | Simulated | Persisted policy evaluation verified by tests. |
| Reviewer queue | Partially passed | Reviewer portal and institution-scoped empty queue loaded; no manually started session existed. |
| Reviewer session review | Environmental blocker | No manually started session was available. |
| Reviewer decision | Simulated | Rationale-required decision verified by integration tests. |
| Administrator oversight | Passed | Institution metrics, policy state, audit state, and session oversight loaded through the browser. |
| Audit inspection | Partially passed | Administrator audit section loaded empty; populated append-only history is test-verified. |
| Report inspection | Simulated | Structured report persistence/retrieval is integration-tested; no manual session report existed. |
| Session completion | Simulated | Completion is integration-tested; no manual session was started. |

Screenshots contain no passwords, tokens, or private device identifiers:

- `screenshots/candidate-readiness.png`
- `screenshots/reviewer-portal.png`
- `screenshots/admin-oversight.png`

## Physical dual-camera result

The controlled browser did not expose two physical camera devices. Discovery produced an explicit dual-camera-unavailable warning, distinct selections and simultaneous previews could not be exercised, and session start remained disabled. This is an environmental/hardware blocker, not a pass.

Implemented in code and tests: candidate-side acquisition, distinct-device enforcement, two local preview elements, permission/track/device lifecycle handling, camera-role metadata, and EvidenceEvents.

Not implemented: remote reviewer video streaming, WebRTC signalling, remote secondary-device pairing, media recording, or raw-video storage.

## Verification summary

- Backend: 51 passed in 145.06 seconds.
- Frontend: 18 tests, TypeScript, ESLint, and production build pass.
- Production routes: ten application routes excluding `/_not-found`; static-generation phase reports nine pages.
- OpenAPI: 40 documented REST paths; attestation contracts regenerated.
- Alembic: one head at 0005; SQLite current/seed verified; PostgreSQL current pending.
- Docker Compose configuration: pass; Docker engine/runtime pending.
- Dependency audit: zero vulnerabilities.
- Secrets: `.env` and `apps/web/.env.local` are ignored and excluded from commits.
- Excluded user file: `Complete Assessment Platform.txt` remains untracked and untouched.

## Unresolved limitations and risk

| Limitation | Risk | Required next evidence |
| --- | --- | --- |
| Docker/PostgreSQL runtime unavailable | Medium | Run migrations, seed, workflow, persistence, and reports against target PostgreSQL. |
| Two-camera hardware unavailable | Medium | Execute discovery, distinct selection, simultaneous previews, denial, termination, disconnection, metadata, and lifecycle evidence with two devices. |
| Access tokens not immediately revocable | Low for bounded demo; higher for production | Add token version/revocation checking or hardened session design. |
| Browser session storage | Medium for production | Move to secure HttpOnly/SameSite cookies with CSRF design. |
| No remote media or raw-video pipeline | Explicit scope boundary | Design only if later research scope authorizes it. |
| No production load/security/privacy certification | High for deployment | Load test, penetration test, DPIA/ethics, retention, backup, monitoring, and incident controls. |

Final risk rating: **Medium, environment validation pending**. No known critical defect remains in the bounded workflow.

## Recommendation

Proceed to dissertation evidence capture and Chapter 3-5 alignment using the exact claim boundaries above. Do not tag or describe SERPS as production-ready. Promotion beyond environment-pending RC1 requires PostgreSQL/Docker and physical dual-camera evidence.
