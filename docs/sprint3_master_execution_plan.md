# SERPS Sprint 3 Master Execution Plan

## Programme objective

Sprint 3 delivers a working and testable production-oriented prototype while preserving the workflow from candidate registration and monitored evidence through explainable governance, human review, audit, and reports.

## Checkpoints

| Checkpoint | Scope | Verification status |
| --- | --- | --- |
| Sprint 3A | Repository recovery and EvidenceEvent persistence | Complete |
| Sprint 3B | CIE, bounded recommendation, IPIME, reviewer decision, audit, timeline, reports | Complete |
| Sprint 3C | Registration, consent, assignment, device/camera preflight, session start | Complete |
| Sprint 3D | Candidate demonstration workspace, dual cameras, reviewer/admin portals | Complete: automated suites, build, SQLite migration cycle, and bounded UI walkthrough passed; PostgreSQL unavailable |
| Sprint 3E | PostgreSQL/Docker seeded proof, comprehensive browser E2E, deployment validation | Not started |

## Sprint 3D delivered workflow

Candidate registration -> consent -> authentication -> assignment -> device check -> primary and secondary camera readiness -> monitored demonstration workspace -> EvidenceEvents -> CIE -> recommendation -> IPIME -> reviewer queue and decision -> administrator oversight -> immutable audit and reports.

## Controls retained

- Backend RBAC, candidate ownership, and institution isolation are authoritative.
- Frontend pages consume persisted APIs and do not reproduce governance decisions.
- Dual-camera setup requires distinct devices and honest permission/availability states.
- Metadata-only reviewer/admin camera panels do not claim remote live streaming.
- Human reviewers retain final operational decision authority.
- Sprint 3E owns final PostgreSQL, seeded full E2E, deployment, and tagging decisions.

## Integrated success criteria status

The component and API capabilities required for the full workflow are implemented through Sprint 3D. Final environment-level proof across PostgreSQL, real two-camera hardware, and comprehensive browser automation remains intentionally assigned to Sprint 3E; therefore Sprint 3E and final production readiness are not marked complete.
