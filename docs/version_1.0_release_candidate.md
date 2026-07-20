# SERPS Research Prototype Version 1.0 Release Candidate (RC1)

## Classification

SERPS is currently classified as **Research Prototype Version 1.0 RC1 — Environment Validation Pending**. It implements the explainable governance workflow at bounded prototype scale, but Docker/PostgreSQL and physical dual-camera validation remain unavailable in the current environment. It is not production-certified and must be evaluated with `prototype_limitations.md`.

## Included capabilities

- Institution-scoped candidate registration, password authentication, JWT access/refresh, and RBAC
- Eligible examination assignments and candidate ownership
- Versioned append-only consent and browser/device readiness
- Mandatory distinct primary and secondary camera roles, local previews, and lifecycle evidence
- Bounded demonstration examination workspace with timer, questions, navigation, and explicit finish
- Durable EvidenceEvents with candidate/session/institution/camera linkage
- Deterministic CIE assessment, bounded agent recommendation, IPIME policy evaluation
- Institution-scoped reviewer queue, dual-status detail, mandatory-rationale human decision
- Administrator metrics, audit visibility, policy, and read-only session oversight
- Append-only governance audit and structured report snapshots
- Forty-path OpenAPI contract, migrations 0001-0005, Docker packaging, and examiner documentation

## RC1 verification evidence

- Complete database-backed workflow test with real JWTs for all three operational roles: passed.
- Full backend suite after adding the RC1 workflow test: 32 passed in 110.82 s.
- Frontend: 18 tests, TypeScript, ESLint, and production build passed. The application defines ten routes excluding `/_not-found`; the build separately reports nine generated static pages.
- Migration: one head at `0005`; fresh SQLite upgrade/downgrade/re-upgrade and corrected seed passed.
- Docker Compose: configuration validated with externally supplied secrets.
- PostgreSQL: not verified because the local Docker engine was unresponsive; no success claim.

## Known release constraints

No production secure browser, enterprise WebRTC, raw-video storage, distributed second-device pairing, production biometric enrolment, load-test evidence, or certified institutional deployment. FaceDetector is browser-dependent. Reviewer/admin camera views are metadata-only.

The audited PostCSS findings were resolved with a compatible 8.5.18 update/override; the current npm audit reports zero vulnerabilities. Major toolchain upgrades were deferred to avoid unrelated breaking change.

## Examiner entry points

- Installation: `installation_guide.md`
- Candidate/reviewer/admin use: `user_manual.md`
- Administration: `system_administration_guide.md`
- Demonstration: `demo_script.md` and `demo_checklist.md`
- Validation: `sprint3e_validation_report.md`
- Dissertation traceability: `dissertation_alignment_matrix.md`
- Limitations and troubleshooting: `prototype_limitations.md`, `troubleshooting.md`

## Promotion criteria after RC1

Before a production pilot: verify PostgreSQL and migrations in the target environment; complete hardware/browser E2E and load/security testing; implement hardened browser sessions, secret/key rotation, security headers/rate limiting; establish remote-media and retention architecture; complete accessibility/privacy/ethics review; integrate institutional identity and assessment APIs; validate backup/restore and monitoring; resolve dependency findings.
