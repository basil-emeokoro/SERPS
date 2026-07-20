# Dissertation Implementation Alignment Matrix

## Review basis

This review compares the repository implementation with the Chapter Three design assets and the implementation/results/limitations topics expected in Chapters Four and Five. Chapter Three source artifacts were inspected read-only. Complete Chapter Four and Five manuscript files are not present in this repository, so claims about their prose are not made and no dissertation file was modified.

| Dissertation component | Implemented | Partial | Future work / dissertation qualification |
| --- | --- | --- | --- |
| Methodology | Yes |  | Sprint checkpoints provide traceable design-build-evaluate evidence consistent with the hybrid Design Science/agile process. |
| Overall architecture | Yes |  | Next.js, FastAPI, domain services, persistence, governance, and role boundaries correspond to the logical architecture. |
| System design | Yes |  | Candidate, reviewer, administrator, evidence, governance, and report flows are integrated. |
| Database | Yes |  | SQLAlchemy schema and migrations 0001-0005 implemented; PostgreSQL runtime remains unverified in this environment. |
| Governance-aware pipeline | Yes |  | Evidence -> CIE -> recommendation -> IPIME -> human decision -> audit/report is fully persisted. |
| Explainability | Yes |  | Risk score/level, evidence IDs, rule version, confidence, explanation, recommendation, and policy explanation are exposed. |
| Identity assurance |  | Yes | Candidate authentication, ownership, consent, and browser-originated face status exist; guided enrolment/production biometric templates are future work. |
| Dual camera |  | Yes | Two distinct local devices, permissions, previews, events, and unified metadata views implemented; no remote WebRTC transport. |
| Reviewer portal | Yes |  | Queue, filters, dual status, explanation, timeline, rationale-required decision, and reports implemented. |
| Administrator portal | Yes |  | Institution metrics, policy, audit, risk distribution, and read-only session oversight implemented. |
| Demonstration workspace | Yes |  | Bounded question harness, timer, navigation, camera lifecycle, evidence, and completion; not a complete CBT system. |
| Reports | Yes |  | Append-only structured session report snapshots generated and retrieved. |
| Privacy |  | Yes | Metadata-only storage and no raw video are implemented; formal retention, DPIA, encryption operations, and institutional policy are future work. |
| Deployment modes |  | Yes | Mode field and Compose packaging exist; distributed/enterprise modes and production orchestration remain future work. |
| API interaction | Yes |  | Forty live OpenAPI paths document role-oriented REST interaction. Real-time WebSocket/SSE/WebRTC interfaces remain planned. |
| Limitations | Yes |  | Dedicated limitations and validation documents explicitly bound every unsupported claim. |
| Future enhancements |  | Yes | PostgreSQL proof, remote media, secure browser integration, load testing, detector migration, production identity provider, and deployment hardening. |

## Chapter-oriented interpretation

- Chapter Three can cite the implemented architecture, data model, workflow, governance, and deployment package while labelling WebRTC, advanced detectors, and production biometrics as planned boundaries.
- Chapter Four can report the 32-test API suite, 18 frontend tests, nine-route production build, single migration head, SQLite migration cycle, one complete workflow test, and the environmental PostgreSQL limitation.
- Chapter Five can conclude that the research workflow is technically feasible and explainable at RC1 prototype scale, while recommendations must retain the limitations above.

The defensible thesis position is: SERPS validates an explainable multi-modal governance layer that integrates with assessment systems; it does not demonstrate a production secure browser, enterprise surveillance platform, or final misconduct classifier.
