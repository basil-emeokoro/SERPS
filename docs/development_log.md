# SERPS POP Development Log

## Sprint 1 - Production-Oriented Prototype Foundation

- Created the separate POP repository at `C:\SERPS` while preserving the Streamlit POC at `C:\Miva_Capstone`.
- Added FastAPI, Next.js, SQLAlchemy, Alembic, Docker Compose, CI scaffold and Chapter Three diagram automation.
- Migrated the structured `EvidenceEvent` contract as the first shared domain boundary.

## Sprint 2 - Authentication, RBAC, Candidate, Examination and Session Foundation

- Added server-enforced roles for Candidate, Reviewer/Proctor, Administrator and System Administrator.
- Added password hashing, JWT access tokens, refresh token rotation and logout/revocation support.
- Added institution, user, role, candidate, examination, assignment, examination session, authentication session, refresh token and audit-log models.
- Added non-destructive Alembic migration `0002_auth_rbac_exam_foundation`.
- Added FastAPI route groups for auth, institutions, users, roles, candidates, examinations, examination sessions and audit logs.
- Added duplicate and state-transition validation with clean API errors.
- Added focused pytest coverage for login, refresh, logout, RBAC denial, candidate uniqueness, examination assignment and session transitions.
- Added role-aware Next.js landing panels for administrator, reviewer/proctor and candidate responsibilities.
- Added idempotent local demo seed script using `SERPS_DEMO_PASSWORD` or a generated one-time password.
- Regenerated OpenAPI and Chapter Three artefacts; Figure 3.19 now includes the expanded Sprint 2 database schema.
- Updated the API Docker image to copy Alembic assets and apply migrations before Uvicorn starts; Docker Compose verification confirmed the PostgreSQL schema reaches the Sprint 2 migration head.

## Current Guardrails

- The original Streamlit proof of concept remains untouched.
- Detection modules must continue to generate evidence only.
- CIE, Agentic Decision Support, IPIME and Human Review remain the governance path for future migrations.
- Private dissertation files and supervisor notes must remain untracked.

## Chapter Three Interim Diagram Freeze and POP Status Correction

- Temporarily froze the current Chapter Three diagram set so implementation can resume.
- Recorded deferred visual corrections for Figures 3.16, 3.17, 3.18 and 3.19 in `docs/dissertation/chapter3/deferred_visual_corrections.md`.
- Corrected the implementation classification of the Next.js/FastAPI POP to **Production-Oriented Prototype - Foundation/Early Alpha**.
- Added `docs/pop_implementation_status.md` to distinguish implemented POP functionality from architecture-only or Streamlit POC-derived capabilities.
- No release-candidate tag should be created from this state.
- Next implementation priority: a narrow functional vertical slice across authentication, session creation, camera/evidence boundary, CIE, Agentic advisory recommendation, IPIME, reviewer action, audit and report trace.
