# SERPS POP Migration Backlog

## Sprint 2 Recommendation

1. Implement authentication and RBAC foundation with server-enforced roles.
2. Persist EvidenceEvent records through PostgreSQL-backed repositories.
3. Add candidate, institution, examination and session schema migrations.
4. Add role-aware Next.js route groups for candidate, reviewer and administrator portals.
5. Add OpenAPI export script and API client generation placeholder.

## Guardrails

- Do not migrate the POC role simulator as authentication.
- Do not claim AI detector operation until live integration and tests exist.
- Do not bypass CIE, Agentic Decision Support, IPIME or Human Review.
- Do not expose reviewer intelligence to candidate routes.
