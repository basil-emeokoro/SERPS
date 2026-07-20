# SERPS Project Progress

## Current status

**Production-Oriented Prototype — Early Alpha**

Sprint 3C is complete. The repository now implements the candidate pre-examination journey from institution-scoped registration through authenticated examination start and real browser EvidenceEvent ingestion. Sprint 3A and Sprint 3B remain frozen and integrated.

## Completed Sprint 3 checkpoints

- Sprint 3A: repository recovery and persistent EvidenceEvents.
- Sprint 3B: deterministic contextual assessment, bounded recommendation, institutional policy evaluation, reviewer governance, immutable audit, timeline, and report APIs.
- Sprint 3C: candidate registration/authentication, assignments, immutable consent, browser/device/camera preflight, gated session start, and automatic evidence-to-governance integration.

## Sprint 3C commit range

Starting checkpoint: `2ecde4c`

- `476bbfb` — candidate registration, account binding, persistence, authenticated assignments/dashboard, and session prerequisites
- `a4a4020` — immutable consent workflow client
- `534e00d` — browser device compatibility, camera discovery/permission, and functional candidate dashboard
- `4e7e0b4` — candidate-owned EvidenceEvent ingestion and automatic Sprint 3B governance integration
- `52f4f79` — complete candidate backend integration tests

The documentation commit follows this report.

## Verified capabilities

- Candidate accounts are persisted as linked `User` and `Candidate` records with the Candidate role.
- Registration validates active institution codes and preserves institution isolation.
- Existing password hashing, JWT access/refresh tokens, and RBAC secure candidate authentication.
- Candidate APIs expose only the authenticated candidate's assignments and dashboard state.
- Consent records preserve version, three explicit acknowledgements, acceptance state, timestamp, candidate, institution, IP address, and user agent; records are append-only.
- Device checks persist browser-reported secure context, browser support, camera availability, and microphone availability.
- Camera discovery uses `navigator.mediaDevices.enumerateDevices()` and permission uses `getUserMedia()`; only device metadata is persisted.
- Session start requires a valid current consent, a passed device check, selected camera, granted permission, an eligible same-institution assignment, and authenticated candidate ownership.
- Sessions link the exact consent, device check, camera selection, and permission records used at start.
- Live browser camera, track-ended, visibility, and supported `FaceDetector` observations create EvidenceEvents.
- Supported events automatically create persisted contextual assessments, recommendations, policy evaluations, and governance audit entries without modifying Sprint 3B behavior.

## Verification

- Python compile: passed.
- Focused Sprint 3C tests: `7 passed in 41.44s`.
- Full Python suite: `28 passed in 126.87s`.
- Alembic head: `0004_sprint3c_candidate`.
- SQLite upgrade, downgrade to Sprint 3B, re-upgrade, and metadata alignment: passed.
- Web TypeScript check: passed.
- Web Vitest suite: 1 file and 1 test passed.
- Docker Compose configuration: valid.
- PostgreSQL: not verified because the local Docker database did not become available.

## Known limitations

- PostgreSQL lifecycle verification remains outstanding.
- Browser Face Detection is emitted only when the browser exposes the `FaceDetector` API; the system does not fabricate face results when unsupported.
- Browser device reports are operational client attestations and should receive stronger integrity controls before production use.
- External reviewer notifications, downloadable reports, hardened browser token storage, and full browser E2E remain later work.

## Remaining Sprint 3 work

Sprint 3D must expose and harden the complete workflow through Next.js operational interfaces, especially reviewer and administrator portals, while reusing the existing API authority boundaries. Sprint 3E owns PostgreSQL/Docker seeded proof, migrations in the deployment environment, Playwright full E2E, and validation of every original Sprint 3 success criterion.
