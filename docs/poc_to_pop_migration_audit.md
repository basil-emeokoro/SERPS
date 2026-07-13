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
| Structured EvidenceEvent | `src/fusion/event_schema.py` | Migrated as Pydantic domain contract and TypeScript shared type | Add repository-backed persistence endpoint |
| CIE | `src/contextual_intelligence/` | Not migrated | Migrate after API/database foundation stabilises |
| Agentic Decision Support | `src/orchestration/agentic_orchestrator.py` | Not migrated | Add advisory service after CIE migration |
| IPIME | `src/policy/` and `config/institutional_policies.json` | Not migrated | Add policy-as-code service after CIE alerts exist |
| Camera Management | `src/camera/` | Not migrated | Add WebRTC-ready frontend components and backend service boundary |
| Visual Intelligence | `src/vision/` | Not migrated | Add detector service modules after evidence persistence |
| Audio Intelligence | `src/audio/` | Not migrated | Add audio event service after media transport design |
| Authentication/RBAC | POC role simulator only | Not implemented | Implement real JWT/session auth, not the simulator |
| PostgreSQL Persistence | POC SQLite | SQLAlchemy/Alembic scaffold | Run migration against PostgreSQL |
| Next.js Frontend | Not applicable | App Router scaffold | Add role-aware candidate/reviewer/admin routes |

## Migration Rule

Validated POC logic should be migrated module by module, preserving the governance pipeline and documenting origin. The POP must not become an unrelated rewrite.
