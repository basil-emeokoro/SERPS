# SERPS Sprint 3 Master Execution Plan

## Programme objective

Sprint 3 delivers a working and testable **Production-Oriented Prototype — Early Alpha**. The implementation sequence below does not change, reduce, redesign, or reorder the final runtime workflow:

Candidate Registration → Consent Acceptance → Candidate Authentication → Assigned Examination Retrieval → Device Compatibility Check → Camera Discovery → Camera Permission → Examination Session Creation → EvidenceEvent Generation → Contextual Intelligence Engine → Agentic Decision Support → IPIME Policy Evaluation → Reviewer Dashboard Notification → Reviewer Decision → Immutable Audit Logging → Candidate/Reviewer Report.

## Checkpoints

| Checkpoint | Scope | Relationship to the original Sprint 3 | Verification status |
| --- | --- | --- | --- |
| Sprint 3A | Repository recovery and EvidenceEvent persistence | Establishes the evidence foundation | Complete: repository recovered; EvidenceEvents persist and can be retrieved; 14 tests passed at checkpoint `30176c1` |
| Sprint 3B | CIE, Agentic Decision Support, IPIME, reviewer decision, audit and report API | Implements the governance backend chain | In progress; mark complete only after migration, tests, and operational chain verification |
| Sprint 3C | Registration, consent, assignment retrieval, device and camera checks, session start | Implements the candidate pre-examination workflow | Not started |
| Sprint 3D | Next.js candidate, reviewer and administrator portals | Exposes the complete workflow through operational interfaces | Not started |
| Sprint 3E | PostgreSQL, Docker, migrations, seeded workflow, Playwright and full E2E validation | Proves every original Sprint 3 success criterion | Not started |

## Original Sprint 3 success criteria

Only verified Sprint 3A foundation capabilities are marked complete above. None of the end-to-end criteria below is complete yet because each requires later checkpoints and final integrated verification.

- [ ] Register a candidate.
- [ ] Accept consent.
- [ ] Log in.
- [ ] View assigned examinations.
- [ ] Complete device and camera checks.
- [ ] Start an examination.
- [ ] Generate real EvidenceEvents.
- [ ] Observe CIE risk assessment.
- [ ] Receive an Agentic recommendation.
- [ ] See IPIME evaluate institutional policy.
- [ ] Review the session in the reviewer dashboard.
- [ ] Record a reviewer decision.
- [ ] Verify immutable audit records.
- [ ] Generate a traceable session report.

## Checkpoint controls

- Sprint 3B uses persisted database records throughout the governance chain and remains advisory, explainable, traceable, append-only, and human-governed.
- Sprint 3C must implement only the candidate pre-examination workflow and real event-production dependencies; it must not change the governance authority boundary.
- Sprint 3D must expose already-verified backend workflow through operational portals rather than duplicate business logic in the browser.
- Sprint 3E owns PostgreSQL/Docker seeded workflow proof, Playwright, full end-to-end validation, and possible milestone tagging.
- Chapter Three diagrams and documentation architecture remain frozen unless an implemented capability strictly requires a factual correction.
