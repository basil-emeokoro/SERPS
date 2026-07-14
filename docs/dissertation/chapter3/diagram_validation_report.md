# Chapter Three Diagram Validation Report

Generated at: 2026-07-14T06:23:16.406464+00:00

## Summary

- Figures requested: 21
- Figures generated: 21
- Editable Mermaid sources generated for every figure.
- SVG exports generated for every figure.
- High-resolution PNG exports generated for every figure with 300 DPI metadata.
- Official colour PNG variants: 21
- Official colour SVG variants: 21
- Official monochrome transparent PNG variants: 21
- Official monochrome transparent SVG variants: 21
- Draw.io exports were not generated in this urgent sprint; Mermaid sources remain editable and SVG is the publication authority.

## Validation Results

- Figure 3.1: PASS - Hybrid Design Science Research and Agile Development Process Adopted for SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.2: PASS - Requirements Traceability Model for SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.3: PASS - Overall System Architecture of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.4: PASS - Candidate Registration, Guided Multi-angle Facial Enrolment and Continuous Identity Assurance Architecture
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.5: PASS - Camera and Sensor Management Architecture
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.6: PASS - Multimodal Evidence Acquisition Architecture
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.7: PASS - Internal Architecture of the Contextual Intelligence Engine
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.8: PASS - Agentic Decision Support Architecture
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.9: PASS - Institutional Policy and Incident Management Engine
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.10: PASS - Governance-aware Decision Pipeline
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.11: PASS - Deployment Modes Supported by SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.12: PASS - High-Level Data Flow within SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.13: PASS - Use Case Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.14: PASS - Activity Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Square / flexible
  - Monochrome check: PASS
- Figure 3.15: PASS - Sequence Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.16: PASS - Class Diagram of SERPS
  - Visual status: PASS WITH MINOR LIMITATION
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.17: PASS - Component Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.18: PASS - Deployment Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.19: PASS - Entity Relationship Diagram of SERPS Database
  - Visual status: PASS WITH MINOR LIMITATION
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
  - Note: Dissertation ERD generated from implemented SQLAlchemy metadata using primary keys, key foreign keys and selected major attributes. Full technical schema is exported separately.
- Figure 3.20: PASS - API Interaction Diagram of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS
- Figure 3.21: PASS - Technology Stack of SERPS
  - Visual status: PASS
  - Recommended Word orientation: Landscape
  - Monochrome check: PASS

## Figure 3.19 Schema Status

Figure 3.19 was generated from the current SQLAlchemy metadata. The present POP schema includes EvidenceEvent persistence plus Sprint 2 institution, user, role, candidate, examination, assignment, session, authentication, refresh-token and audit-log tables.

## Architecture Consistency Checks

- Detection modules are shown as evidence producers only.
- CIE is shown as the central reasoning layer.
- Agentic Decision Support is shown as advisory only.
- IPIME is shown as institutional workflow/policy handling, not final decision-making.
- Human Reviewer and final institutional decision boundaries are explicit.
- PostgreSQL is represented as shared persistence, not a reasoning component.
- React/Next.js is represented as presentation/control surface, not as CIE or AI business logic.

## Sprint 2 Tagging Note

- The `v0.2.0-auth-session-foundation` tag was intentionally not created in this remediation sprint.
