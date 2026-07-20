# Sprint 3D Operational Interfaces Report

## Starting state

- Repository: `C:\SERPS`
- Branch: `main`
- Starting HEAD: `e81a5742ecee223279e649d6854a94915f044872`
- Accepted maturity: Production-Oriented Prototype - Integrated Early Alpha
- A pre-existing untracked user file, `Complete Assessment Platform.txt`, was preserved and excluded from every commit.

## Delivered interfaces

- `/candidate`: consent, device discovery, two distinct camera selections, separate previews/permissions, readiness, session start/resume.
- `/candidate/examinations/[sessionId]`: bounded sample questions, stable elapsed timer, navigation, primary/secondary local previews, capability disclosure, browser-originated events, explicit finish and track cleanup.
- `/reviewer`: live institution-scoped queue with risk, unresolved/session filters, recommendation, policy, event, reviewer-action, and both-camera states.
- `/reviewer/sessions/[sessionId]`: unified two-camera metadata/status view, CIE explanation, recommendation, IPIME result, timeline, decisions, reports, and confirmed rationale-required human action.
- `/admin`: live operational metrics, risk distribution, active policy, recent audit, and session oversight.
- `/admin/sessions/[sessionId]`: read-only institution-scoped dual-camera, risk, policy, reviewer, report, and timeline detail.

## Shared frontend foundation

Typed contracts and one API client now handle authentication tokens, cancellation, bounded retry, consistent error parsing, session expiry, access denial, candidate/reviewer/admin endpoints, timelines, and reports. Shared components cover loading, empty/error states, confirmation, capability disclosure, camera status, readiness, risk, metrics, and role navigation.

## Backend and database additions

- Candidate-owned session detail and session completion endpoints.
- Camera-role metadata for primary and secondary selections/permissions, distinct-device enforcement, and both-role readiness.
- Reviewer/admin operational session detail, administrator metrics, and active institutional policy endpoints.
- Queue and timeline camera/status enrichment.
- Migration `0005_sprint3d_dual_camera`, chained from `0004_sprint3c_candidate`, adds role columns and secondary session links with downgrade support.

## Live versus metadata-only

- Live: local getUserMedia previews, device enumeration, permission results, track-ended/device-change/visibility events, optional browser FaceDetector, API-backed governance and metrics.
- Metadata-only: reviewer/admin camera panels show persisted configuration, connection state, latest evidence timestamp, and failure reason. They never fabricate video.
- Demonstration-only: three static sample questions and answer navigation. No scoring, authoring, autosave, secure-browser enforcement, or production CBT claim.

## Accessibility and responsive behavior

Operational states use status/alert semantics, visible focus, text plus color, labelled controls, confirmation dialogs, reduced-motion support, and tablet stacking. A 768x900 browser check reported no horizontal overflow. Evidence readability remains prioritized over forced narrow mobile density.

## Automated verification

- `python -m py_compile apps/api/app/main.py`: passed.
- `python -m pytest -q`: 31 passed in 145.77 seconds; one restricted-cache warning.
- `python -m alembic heads`: `0005_sprint3d_dual_camera (head)`.
- SQLite fresh upgrade, current, downgrade to 0004, re-upgrade/current: passed.
- `npm.cmd run typecheck -w apps/web` equivalent with incremental output disabled: passed.
- `npm.cmd run test -w apps/web`: 2 files, 18 tests passed.
- `npm.cmd run lint -w apps/web`: passed.
- `npm.cmd run build -w apps/web`: passed; nine routes generated.
- `docker compose config`: passed.

## Bounded manual walkthrough

Fully verified: production landing content, authentication guards for candidate/reviewer/admin list and detail routes, candidate workspace guard, route rendering, and tablet overflow behavior. Backend integration tests fully verify candidate ownership, dual-role readiness, completion, persisted camera evidence, governance processing, reviewer/admin access, institution scoping, and metrics.

Partially verified: the complete operational sequence is proven across backend integration tests, frontend component/client tests, and browser route inspection, but not as one hardware-backed browser transaction.

Unavailable: real two-camera hardware permission exercise, reviewer-side remote live streaming (not implemented), and PostgreSQL execution. Docker Compose was valid, but Docker Desktop did not provide a responsive engine.

## Known limitations and Sprint 3E

Sprint 3E must provide PostgreSQL/Docker seeded validation, comprehensive browser/hardware E2E, deployment and security hardening, remote-stream architecture decisions, and release-tag evaluation. No Sprint 3E work was started.

SERPS is not a replacement for an assessment platform or secure examination browser. It is an explainable multi-modal identity assurance, monitoring, and governance layer designed to integrate with existing examination systems. The bounded workspace generates realistic monitored interactions; the dual-camera architecture presents candidate-facing and environmental status in one reviewer/administrator interface without unsupported enterprise-streaming claims.
