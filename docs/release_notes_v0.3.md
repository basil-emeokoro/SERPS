# SERPS v0.3 Release Baseline

## Baseline status

Sprint 3D begins from `e81a5742ecee223279e649d6854a94915f044872` on `main`, after accepted Sprint 3A, 3B, and 3C checkpoints. The maturity at this baseline is **Production-Oriented Prototype - Integrated Early Alpha**.

## Completed capability baseline

- Sprint 3A recovered the repository and added durable, retrievable EvidenceEvent persistence.
- Sprint 3B added deterministic contextual assessment, bounded agentic recommendation, institutional policy evaluation, reviewer decisions, immutable governance audit, timelines, and structured report snapshots.
- Sprint 3C added institution-scoped candidate registration/authentication, assignments, immutable consent, browser device and camera preflight, gated session start, and automatic evidence-to-governance integration.
- Alembic migrations `0001_initial` through `0004_sprint3c_candidate` form the accepted database chain.

## Technology snapshot

- Next.js, React, and TypeScript for role-aware web interfaces.
- FastAPI and Pydantic for authenticated API contracts.
- SQLAlchemy and Alembic for persistence and schema evolution.
- PostgreSQL is the deployment target; SQLite is used for bounded local migration verification.
- Pytest and Vitest provide backend and frontend regression coverage.

## Sprint 3D update

Version 0.3 now includes a shared authenticated API/UI foundation, role navigation, a bounded demonstration examination workspace, mandatory distinct primary/secondary camera setup, candidate completion, API-backed reviewer queues, explainable dual-view session detail, human decision persistence, and institution-scoped administrator metrics. Migration `0005_sprint3d_dual_camera` extends the accepted `0004` chain.

Verification passed for 31 backend tests, 18 frontend tests, TypeScript, ESLint, the Next.js production build, Compose configuration, and an SQLite upgrade/downgrade/re-upgrade migration cycle. PostgreSQL verification remains unavailable because Docker Desktop did not expose a responsive engine.

## Known limitations

- Browser FaceDetector is capability-dependent and must never be simulated when unavailable.
- Reviewer/admin camera panels expose persisted metadata and connection evidence, not enterprise remote streams.
- PostgreSQL/Docker seeded proof, comprehensive Playwright E2E, deployment, security hardening, and milestone tagging remain Sprint 3E work.

Current maturity: **Production-Oriented Prototype - Operational Early Alpha**.

## Sprint 3E RC1 validation

The end-to-end candidate, evidence, governance, reviewer, administrator, audit, and report workflow is now covered by one database-backed validation test using real role JWTs. The demo seed was corrected to require an explicit password and to preserve candidate-authoritative session start. OpenAPI now matches all 40 documented REST paths, and Compose requires externally supplied database/JWT secrets.

At the Sprint 3E checkpoint, the backend, frontend tests, TypeScript, ESLint, production build, migration cycle, seed, and Compose configuration passed. PostgreSQL remained honestly unverified because Docker engine discovery was unresponsive, and two moderate PostCSS findings were still open; Sprint 3F resolves the dependency finding below while retaining the environment limitation.

Current maturity after Sprint 3E: **Research Prototype Version 1.0 Release Candidate (RC1)**. See `version_1.0_release_candidate.md` and `sprint3e_validation_report.md`.

SERPS integrates with external examination systems; it does not replace a full assessment platform, question bank, secure browser, or enterprise video-streaming service.

## Sprint 3F RC1 hardening

Sprint 3F preserved the independent audit and resolved its high-severity application findings:

- Candidate EvidenceEvent creation now requires candidate ownership, institution scope, an active/permitted session, an allowed event type, and the `candidate_browser` source. Reviewer/administrator injection through that endpoint is rejected before governance processing.
- Identity AuditLog update, deletion, and replacement are rejected through supported ORM interfaces. This is application/ORM-level append-only enforcement, not a database-trigger claim.
- Access JWTs are short-lived and strictly validate algorithm, signature, issuer, audience, type, expiry, issue time, subject, institution, and roles. Protected requests reload active database user state and compare trusted role/institution data.
- Device, camera, and permission records are explicitly browser-attested/client-reported inputs with bounded values, browser context, attestation status, source, client timestamp where supplied, and server receipt time.
- PostCSS was safely updated/overridden to 8.5.18; the current npm audit reports zero vulnerabilities.
- Environment examples now document required database, JWT, CORS, frontend, and demonstration variables without committing secrets.

The current backend suite contains 51 passing tests. Frontend tests, typecheck, lint, and production build pass. The application defines ten routes excluding `/_not-found`; the build separately reports nine generated static pages.

Docker/PostgreSQL and physical dual-camera execution remain unavailable in the validation environment. The correct release classification is **Research Prototype Version 1.0 RC1 — Environment Validation Pending**. No release tag has been created.
