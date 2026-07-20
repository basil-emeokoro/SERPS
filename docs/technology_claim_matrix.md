# SERPS RC1 Technology Claim Matrix

| Technology/component | RC1 status | Evidence | Qualification / next action |
| --- | --- | --- | --- |
| FastAPI | Implemented | 40 live OpenAPI paths across identity, candidate, evidence, governance, reviewer/admin, audit, and reports | Add production gateway, telemetry, and rate limiting. |
| Next.js/React/TypeScript | Implemented | Nine built routes; candidate/reviewer/admin operational portals; 18 frontend tests | Add comprehensive hardware/browser E2E. |
| SQLAlchemy | Implemented | Identity, readiness, evidence, governance, audit, and report models/services | Profile and remove N+1 aggregation queries before scale. |
| Alembic | Implemented | Single chain 0001-0005; SQLite upgrade/downgrade/re-upgrade passed | Verify against target PostgreSQL. |
| PostgreSQL | Configured, unverified | Compose target and psycopg URL; Docker engine unavailable | Run migrations and full workflow on PostgreSQL before pilot. |
| Docker Compose | Configured/validated | Secret-required Compose config passes | Engine/build/runtime validation remains environmental. |
| JWT/RBAC | Implemented | Signed access tokens, hashed refresh tokens, role dependencies, negative access tests | Harden browser session storage and key/revocation operations. |
| Dual local cameras | Partial | Distinct selection, permission, two local previews, lifecycle EvidenceEvents | Real hardware E2E and distributed secondary-device design remain. |
| WebRTC/remote media | Future | No implementation claim | Design TURN/signalling/privacy/retention before remote streaming. |
| FaceDetector | Capability-dependent | Explicit feature detection; no fabricated face event | Migrate/evaluate production detector with fairness and liveness testing. |
| CIE | Implemented, bounded | Deterministic temporal rules, evidence linkage, risk/confidence/explanation | Validate rules empirically and tune under ethics governance. |
| Agentic decision support | Implemented, bounded | Persisted advisory actions and explanations | No autonomous misconduct authority; evaluate model/rule alternatives later. |
| IPIME | Implemented | Persisted institutional policy evaluation and reviewer requirement | Add controlled policy administration/version lifecycle. |
| Reviewer/admin portals | Implemented | Queue, dual metadata, decisions, reports, metrics, audit oversight | Remote media and production notification integrations remain. |

The matrix describes research-prototype evidence, not production certification.
