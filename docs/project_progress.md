# SERPS Project Progress

## Current status

**Production-Oriented Prototype - Operational Early Alpha**

Sprint 3D is implementation-complete. Candidate, reviewer, and administrator operational interfaces expose the accepted Sprint 3A-3C services while preserving backend RBAC, institution isolation, append-only governance, and human decision authority.

## Completed Sprint 3 checkpoints

- Sprint 3A: repository recovery and persistent, retrievable EvidenceEvents.
- Sprint 3B: contextual assessment, bounded recommendation, institutional policy evaluation, reviewer governance, immutable audit, timelines, and structured reports.
- Sprint 3C: candidate registration/authentication, assignments, immutable consent, browser/device preflight, gated session start, and automatic evidence-to-governance integration.
- Sprint 3D: shared frontend foundation, bounded demonstration workspace, mandatory dual-camera setup, reviewer dual-view review, administrator oversight, accessibility/error states, and operational tests.

## Sprint 3D verification

- API entrypoint compilation: passed.
- Full Python suite: `31 passed in 145.77s` (cache-write warning only under the restricted workspace).
- Frontend Vitest: `2 files, 18 tests passed`.
- TypeScript: passed with `tsc --noEmit --incremental false`.
- ESLint: passed.
- Next.js production build: passed; nine application routes generated.
- Docker Compose configuration: valid.
- Alembic single head: `0005_sprint3d_dual_camera`.
- SQLite migration cycle: fresh upgrade 0001-0005, downgrade 0005-0004, and re-upgrade to 0005 passed.
- PostgreSQL: unavailable because the local Docker engine did not respond; no PostgreSQL success is claimed.
- Manual UI: landing maturity text, six protected operational routes, candidate workspace guard, and 768px layout without horizontal overflow verified.

## Honest prototype boundaries

- Candidate camera previews are live local browser streams where two distinct devices and permissions exist.
- Camera connection evidence and privacy-safe metadata are persisted; raw video is not recorded.
- Reviewer and administrator dual views are verified metadata/status panels, not enterprise remote video streaming.
- Face detection runs only when the browser exposes FaceDetector; unsupported browsers show an explicit limitation and produce no fabricated face event.
- The workspace is an assessment demonstration harness, not a complete CBT platform, Safe Exam Browser equivalent, or operating-system lockdown tool.

## Remaining Sprint 3E work

Sprint 3E retains PostgreSQL/Docker seeded proof, complete browser-and-hardware E2E, production deployment validation, remote-stream architecture decisions, security hardening, and any release-tag decision. Sprint 3E is not started or marked complete.
