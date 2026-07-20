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

Version 0.3 now includes a shared authenticated API/UI foundation, role navigation, a bounded demonstration examination workspace, mandatory distinct primary/secondary camera setup, candidate completion, live reviewer queues, explainable dual-view session detail, human decision persistence, and institution-scoped administrator metrics. Migration `0005_sprint3d_dual_camera` extends the accepted `0004` chain.

Verification passed for 31 backend tests, 18 frontend tests, TypeScript, ESLint, the Next.js production build, Compose configuration, and an SQLite upgrade/downgrade/re-upgrade migration cycle. PostgreSQL verification remains unavailable because Docker Desktop did not expose a responsive engine.

## Known limitations

- Browser FaceDetector is capability-dependent and must never be simulated when unavailable.
- Reviewer/admin camera panels expose persisted metadata and connection evidence, not enterprise remote streams.
- PostgreSQL/Docker seeded proof, comprehensive Playwright E2E, deployment, security hardening, and milestone tagging remain Sprint 3E work.

Current maturity: **Production-Oriented Prototype - Operational Early Alpha**.

SERPS integrates with external examination systems; it does not replace a full assessment platform, question bank, secure browser, or enterprise video-streaming service.
