# SERPS Project Progress

## Current status

**Research Prototype Version 1.0 RC1 — Environment Validation Pending**

Sprint 3F resolves the independent audit's application-level security conditions and preserves an honest environment qualification. Docker Desktop did not expose a responsive engine, no installed local PostgreSQL instance was available, and the browser exposed fewer than two cameras. SERPS is therefore suitable for a bounded dissertation demonstration, not production deployment.

## Completed checkpoints

- Sprint 3A: repository recovery and persistent EvidenceEvents.
- Sprint 3B: CIE, bounded recommendation, IPIME, reviewer decisions, audit, timelines, and reports.
- Sprint 3C: candidate registration/authentication, assignment, immutable consent, readiness, session start, and automatic governance.
- Sprint 3D: operational candidate/reviewer/administrator portals and mandatory dual-camera presentation.
- Sprint 3E: integrated workflow validation, build/security/performance review, migrations, examiner documentation, and RC1 candidate evidence.
- Sprint 3F: independent-audit preservation; candidate evidence authorization; identity-audit append-only enforcement; JWT/active-user hardening; browser-attestation boundaries; dependency remediation; reproducible configuration; manual browser evidence; claims correction; and defence-readiness reporting.

## Sprint 3F verified state

- Backend: 51 tests passed in 145.06 seconds after correcting a stale Sprint 3E evidence-source fixture.
- Frontend: 18 tests pass; TypeScript, ESLint, and production build pass.
- Routes: ten application routes excluding `/_not-found`; the Next.js build separately reports nine generated static pages.
- OpenAPI: 40 documented REST paths, regenerated after attestation-schema hardening.
- Alembic: single head `0005_sprint3d_dual_camera`; migrations 0001-0005 and seed passed against temporary SQLite.
- Docker Compose configuration: valid.
- Docker/PostgreSQL runtime: pending because Docker commands were unresponsive and no safe installed local PostgreSQL service existed.
- Browser demonstration: candidate authentication and immutable consent passed; reviewer and administrator portals loaded; device/camera/session stages were correctly blocked by missing dual-camera hardware.
- Dependency audit: zero vulnerabilities with PostCSS 8.5.18 deduplicated across Next.js and Vite.
- Security: all high-severity audit conditions resolved at the supported application/ORM boundary; no database-trigger immutability claim is made.

## Boundaries

Candidate-side two-camera acquisition, distinct selection, local previews, lifecycle handling, metadata persistence, and EvidenceEvents are implemented. Remote reviewer video, WebRTC signalling, secondary-device pairing, raw-video storage, a complete CBT platform, secure-browser enforcement, production biometric enrolment, institutional-scale operation, and production certification are not implemented or claimed.

The next phase is dissertation evidence capture and Chapter 3-5 alignment, not further core development.
