# SERPS — Secure Explainable Remote Proctoring System

**Governance-aware, multimodal examination integrity research prototype**  
*Research Prototype v1.0 — Release Candidate (RC1)*

[![GitHub Actions](https://github.com/basil-emeokoro/SERPS/actions/workflows/verify.yml/badge.svg)](https://github.com/basil-emeokoro/SERPS/actions)
[![Status: Research Prototype](https://img.shields.io/badge/status-research%20prototype-334155)](docs/native_runtime_integration.md)
[![Validation: 265 tests](https://img.shields.io/badge/validated%20locally-265%20tests-0f766e)](docs/native_runtime_integration.md)
[![Deployment: Restricted staging pending](https://img.shields.io/badge/deployment-restricted%20staging%20pending-c2410c)](docs/runtime_deployment_alternatives.md)

> **Research boundary:** SERPS is an assessment-integrity and governance layer designed for integration with external examination systems. It is **not** a complete CBT platform, certified biometric system, production lockdown browser, or publicly deployed examination service. Automated evidence is advisory; consequential decisions remain with authorised human reviewers.

## Explore SERPS

| Start here | What you will find |
| --- | --- |
| [Architecture and workflow](#system-workflow) | Identity → monitoring → evidence → contextual reasoning → institutional governance |
| [Research contributions](#research-contributions) | Dual-camera monitoring, explainable evidence, bounded recommendations and policy governance |
| [Implementation and technology](#technology-stack) | Next.js, React, FastAPI, SQLAlchemy, MediaPipe and EfficientDet-Lite0 |
| [Validation and limitations](#validation-and-limitations) | Test evidence, acceptance boundaries and known integrity risks |
| [Run locally](#local-development) | Native and clean-install guidance |
| [Deployment readiness](#deployment-readiness) | Railway, Render and PostgreSQL preparation, without a live public deployment |
| [Project documentation](#documentation) | Installation, demonstrations, runtime recovery and governance evidence |

## System workflow

```mermaid
flowchart LR
    A[Candidate registration and consent] --> B[Facial enrolment and identity assurance]
    B --> C[Device readiness and camera monitoring]
    C --> D[Structured EvidenceEvents]
    D --> E[Contextual Intelligence Engine]
    E --> F[Bounded agentic recommendations]
    F --> G[Institutional policy evaluation]
    G --> H[Human reviewer decision]
    H --> I[Audit and reporting]
```

The candidate demonstration workspace supports a primary candidate-facing camera and, in Mode B, a separate environmental camera. Browser-local monitoring generates structured observations; the system correlates evidence and routes governance decisions through institutional policy and human review. No individual detector result is treated as proof of misconduct.

## Research contributions

| Capability | Implemented research-prototype scope |
| --- | --- |
| **Candidate identity assurance** | Guided facial enrolment, dynamic liveness interaction and bounded post-enrolment verification |
| **Multimodal monitoring** | Local person/phone detection, face presence and microphone RMS activity |
| **Dual-camera context** | Distinct candidate and environmental views in supported Mode B workflows |
| **EvidenceEvent provenance** | Structured observations, audit metadata and ordered delivery with explicit unresolved states |
| **Contextual Intelligence Engine (CIE)** | Deterministic contextual rules; not a trained misconduct classifier |
| **Agentic Decision Support (ADS)** | Explainable, bounded recommendations for authorised reviewers |
| **Institutional Policy and Incident Management Engine (IPIME)** | Policy-governed incident handling, reviewer authority and auditability |
| **Operational recovery** | Distinguishes network interruption from authentication expiry; supports bounded evidence replay |

## Technology stack

| Layer | Technologies |
| --- | --- |
| Web application | Next.js, React, TypeScript |
| API | Python, FastAPI, Pydantic |
| Vision and audio | MediaPipe Tasks Vision, EfficientDet-Lite0, Web Audio RMS |
| Persistence | SQLAlchemy, Alembic; SQLite native prototype, PostgreSQL deployment target |
| Testing | Pytest, Vitest, TypeScript, ESLint |
| Packaging | Docker Compose, separate API/web Dockerfiles |

## Validation and limitations

The **24 October 2026 native recovery** documented **116 backend tests** and **149 frontend tests** passing, together with TypeScript, lint, production-build and browser checks for synthetic staff login, token refresh, outage recovery and remount. The native API/frontend smoke tests returned HTTP 200. These are historical results for the reviewed commit, **not live deployment-health metrics**.

[Read the complete acceptance and rollback record](docs/native_runtime_integration.md).

**Outstanding acceptance:** physical dual-camera and biometric workflows; real sleep/resume and interruption scenarios; live PostgreSQL replay concurrency; completion-in-flight evidence race; tab-scoped evidence retention; dependency-security remediation; and synthetic staging provisioning. These limits prevent claims of production readiness.

## Local development

For the preserved Windows native installation (API **8765**, web **3100**), follow [Native runtime integration](docs/native_runtime_integration.md). **Do not overwrite existing environments or seed the preserved SQLite database.**

For a **fresh clone only**, the repository documents this baseline:

```powershell
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
npm.cmd install
python -m alembic upgrade head
```

Configure unique local secrets in `.env` (never commit it). Run the API and web app in separate terminals:

```powershell
uvicorn apps.api.app.main:app --reload --port 8000
npm.cmd run dev -w apps/web
```

The stock demo seeder has a documented provisioning incompatibility; **do not bypass candidate enrolment or identity gates** to work around it. See [Docker deployment](docs/docker_deployment.md) for container-based setup and isolation.

## Deployment readiness

**No public SERPS deployment is claimed.** [Restricted deployment alternatives](docs/runtime_deployment_alternatives.md) evaluates Railway and Render with managed PostgreSQL; Supabase is optional after connection/TLS validation. Restricted staging requires access controls, secure secrets, synthetic-only data, validated provisioning, and database rollback checks. The browser-facing API URL must be supplied at web **build time**.

## Documentation

- [Native runtime recovery, acceptance and rollback](docs/native_runtime_integration.md)
- [Restricted deployment alternatives](docs/runtime_deployment_alternatives.md)
- [Docker deployment](docs/docker_deployment.md)
- [Installation guide](docs/installation_guide.md)
- [User manual](docs/user_manual.md)
- [Demonstration script](docs/demo_script.md)
- [Historical Sprint 3E validation](docs/sprint3e_validation_report.md)
- [Open issues](https://github.com/basil-emeokoro/SERPS/issues) · [Pull requests](https://github.com/basil-emeokoro/SERPS/pulls) · [CI workflows](https://github.com/basil-emeokoro/SERPS/actions)

## Research integrity and responsible use

SERPS is designed to support evidence-informed human oversight, not autonomous disciplinary decisions. Its face representation and liveness checks are bounded prototype techniques, not certified recognition or presentation-attack resistance. Raw monitored camera/microphone media is not stored by default by the local detectors. Do not use real candidate records, biometric data or examination evidence in public demonstrations.

**Author:** Basil Oforbuike Emeokoro  
Psychometrics · AI-enabled assessment · Explainable AI · Educational technology  
[GitHub profile](https://github.com/basil-emeokoro)
