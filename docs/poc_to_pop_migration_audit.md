# SERPS POC to POP Migration Audit

## Authority

- Primary POC baseline: `C:\Miva_Capstone`
- POP repository: `C:\SERPS`
- System Specification: `C:\Miva_Capstone\System Specification.pdf`
- Dissertation chapters and approved addenda remain the implementation authority.

## Claim-to-Implementation Discipline

The POP must not claim operational technology until the repository contains code, tests and integration evidence.

| Capability | POC Evidence | POP Sprint 1 Status | Next Action |
| --- | --- | --- | --- |
| Structured EvidenceEvent | `src/fusion/event_schema.py` | Migrated as Pydantic domain contract, TypeScript shared type and persistence endpoint foundation | Harden repository integration against PostgreSQL |
| CIE | `src/contextual_intelligence/` | Not migrated | Migrate after API/database foundation stabilises |
| Agentic Decision Support | `src/orchestration/agentic_orchestrator.py` | Not migrated | Add advisory service after CIE migration |
| IPIME | `src/policy/` and `config/institutional_policies.json` | Not migrated | Add policy-as-code service after CIE alerts exist |
| Camera Management | `src/camera/` | Not migrated | Add WebRTC-ready frontend components and backend service boundary |
| Visual Intelligence | `src/vision/` | Not migrated | Add detector service modules after evidence persistence |
| Audio Intelligence | `src/audio/` | Not migrated | Add audio event service after media transport design |
| Authentication/RBAC | POC role simulator only | JWT access/refresh tokens, password hashing, roles and protected routes implemented | Add production identity-provider option later |
| PostgreSQL Persistence | POC SQLite | SQLAlchemy/Alembic scaffold plus identity/exam/session migration | Run migration against PostgreSQL and add integration tests |
| Next.js Frontend | Not applicable | App Router scaffold plus role-aware portal landing panels | Add full protected route groups |

## Migration Rule

Validated POC logic should be migrated module by module, preserving the governance pipeline and documenting origin. The POP must not become an unrelated rewrite.
