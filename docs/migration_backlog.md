# SERPS POP Migration Backlog

## Sprint 2 Recommendation

1. Implement authentication and RBAC foundation with server-enforced roles. **Completed.**
2. Persist EvidenceEvent records through PostgreSQL-backed repositories. **Sprint 1 foundation remains in place; deeper repository hardening remains open.**
3. Add candidate, institution, examination and session schema migrations. **Completed.**
4. Add role-aware Next.js route groups for candidate, reviewer and administrator portals. **Partially completed as portal landing panels; full route groups remain open.**
5. Add OpenAPI export script and API client generation placeholder. **OpenAPI export completed; client generation remains open.**

## Sprint 3 Recommendation

1. Harden PostgreSQL integration tests and migration execution against Docker Compose.
2. Expand candidate self-profile binding and reviewer assignment scoping.
3. Add route-level pagination/filtering for high-volume candidate, session and audit views.
4. Add API client generation or typed frontend service wrappers from `docs/openapi.json`.
5. Prepare media-transport service boundaries without migrating detector logic prematurely.

## Guardrails

- Do not migrate the POC role simulator as authentication.
- Do not claim AI detector operation until live integration and tests exist.
- Do not bypass CIE, Agentic Decision Support, IPIME or Human Review.
- Do not expose reviewer intelligence to candidate routes.
