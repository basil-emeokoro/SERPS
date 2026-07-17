# Deferred Chapter Three Visual Corrections

The Chapter Three diagrams are frozen temporarily as interim dissertation artefacts so implementation can resume. The current set is suitable for immediate review and report drafting, but the items below must be revisited after the functional vertical slice and schema stabilise.

## Figures Accepted for Immediate Use

The following figures are sufficiently clear for current Chapter Three use, subject to normal resizing in Word or landscape placement where needed:

- Figure 3.3 - Overall System Architecture
- Figure 3.4 - Candidate Registration, Guided Multi-angle Facial Enrolment and Continuous Identity Assurance Architecture
- Figure 3.8 - Agentic Decision Support Architecture
- Figure 3.13 - Use Case Diagram
- Figure 3.15 - Sequence Diagram

Figure 3.15 should preferably be inserted as SVG or placed on a landscape page because text becomes small at normal portrait page width.

## Deferred Corrections

### Figure 3.16 - Class Diagram

- Several associations still cross entity boxes or text.
- CandidateExamAssignment and Examination require clearer spacing.
- Incident relationships need cleaner routing.
- Multiplicity notation should be made more conventionally UML-compliant.
- Implemented and conceptual/domain classes should be visually distinguished.

### Figure 3.17 - Component Diagram

- Camera-related dependencies still create long connector paths.
- Evidence Service to persistence routing should be clearer.
- Application services, detection services, and intelligence/governance services should be visually separated more cleanly.
- The diagram is readable enough as an interim architecture figure but not final repository-package quality.

### Figure 3.18 - Deployment Diagram

- Deployment boundary and connector labels need more space.
- WebRTC/media routing should avoid crossing the centre of the deployment environment.
- AI monitoring service text should be less cramped.
- Sync and event metadata labels need clearer placement.
- Implemented Docker topology and future production deployment options should be distinguished more explicitly.

### Figure 3.19 - Logical Entity Relationship Diagram

- The diagram should be refined into a stricter implemented-versus-conceptual logical ERD after schema freeze.
- Cardinality labels should be closer to their relationships.
- Staff activity to AuditLog relationship needs clearer semantics.
- ContextualAlert and Incident should be marked as conceptual until fully implemented as POP tables.
- The final package should use cleaner ERD notation and avoid explanatory text clipping.

## Re-generation Rule

These figures should be regenerated after the functional vertical slice and schema freeze. Until then, the generated artefacts remain interim Chapter Three implementation diagrams, not a final production-quality dissertation figure package.
