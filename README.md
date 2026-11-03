<p align="center"><img src="docs/portfolio/assets/serps-header.svg" alt="SERPS: Evidence with context. Decisions with oversight. Research prototype; physical acceptance pending." width="100%"></p>

<p align="center"><strong>Research prototype RC1</strong> - <strong>Source-linked engineering evidence</strong> - <strong>No public deployment</strong></p>

# SERPS POP

**Revision boundary:** The recovery capability descriptions document historical revision [`0cc0126`](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/README.md), with validation reported 24 October 2026. They do not establish identical functionality or acceptance on current `main`. In particular, the ordered outbox, atomic delivery and authentication recovery belong to that recovery revision; this documentation update does not add them to main.


SERPS is a research-oriented, production-oriented prototype investigating trustworthy multimodal AI for educational assessment. It connects local computer-vision observations to explainable evidence, institutional policy and accountable human review. The engineering work asks how to preserve evidence and authority boundaries; the research agenda asks whether those mechanisms support valid, fair and privacy-conscious assessment.

**Scope:** a Production-Oriented Prototype with a bounded demonstration examination workspace. It is not a complete CBT platform, secure browser, certified biometric system or autonomous misconduct adjudicator.

[Evidence matrix](docs/portfolio/evidence-matrix.md) - [Evidence boundaries](#evidence-and-acceptance) - [Architecture](#architecture-and-operating-modes) - [Run locally](#deployment-and-verification) - [Limitations](#acceptance-boundaries)

## Research and engineering portfolio

| Read for | Start here | What it establishes |
| --- | --- | --- |
| Research motivation and psychometrics | [Research statement](docs/portfolio/research-statement.md) | Questions and hypotheses, not validated fairness or score validity |
| Architecture and engineering decisions | [Engineering case study](docs/portfolio/engineering-case-study.md) | Source-linked boundaries, trade-offs and failure modes |
| Evidence and reproducibility | [Evaluation ledger](docs/portfolio/evaluation-and-reproducibility.md) | Revision-specific software results; no invented model benchmarks |
| Doctoral research potential | [Two research directions](docs/portfolio/phd-research-directions.md) | Trustworthy multimodal AI and handwriting-centered human-AI assessment proposals |

The practical motivation is to make monitoring evidence inspectable without equating a detected object or unavailable camera with misconduct. Implemented bounded reasoning and human-review records provide an engineering foundation. Their effects on reviewer decisions, assessment validity, fairness and learning remain research questions.

## Capabilities and revision boundaries

| Capability | Implementation boundary | Portfolio evidence |
| --- | --- | --- |
| Identity and access | Registration, enrolment, authentication, roles and institution isolation | Source implementation; no candidate biometric acceptance claim |
| Local monitoring | MediaPipe face geometry, EfficientDet-Lite0 person/phone classes, Web Audio activity | Source and historical tests; no new physical-camera acceptance evidence |
| Recovery-revision evidence delivery | Ordered metadata, stable delivery IDs, bounded retries and visible unresolved failures | Historical recovery report only; absent from this main baseline; not indefinite offline storage |
| Explainable governance | Evidence - CIE - ADS advisory recommendation - IPIME - human review/audit | Implemented code; populated governance views not captured |
| Operational protection | Independent policy, identity, connectivity and monitoring concerns | Exam Protect anomaly remains unresolved; no acceptance claim |

## Architecture and operating modes

The architecture below describes the historical recovery revision. It is not a deployment or feature-parity statement for main.

![SERPS architecture: local observations, authenticated evidence API, contextual assessment, institutional policy, human review and audit](docs/portfolio/assets/architecture.svg)

The Next.js browser performs bounded local inference. FastAPI enforces authentication, ownership and institutional access; SQLAlchemy persists structured records. SQLite supports the native prototype; PostgreSQL is the configured deployment target. Reviewer interfaces receive metadata and explanations, not live camera or microphone feeds.

| Mode | Intended arrangement | Interpretation |
| --- | --- | --- |
| A | Candidate-facing primary camera | Primary inference; no independent environmental corroboration |
| B | Candidate-facing primary + distinct environment camera | Independent configured roles can contribute contextual corroboration |
| C | Primary camera + physical mirror | Same image source; a mirror is not an independent digital camera |

Readiness currently retains distinct-device prerequisites even for A/C. Historical routing tests do not establish current physical acceptance of all modes. See [mode implementation status](docs/proctoring_modes_implementation_status.md).

**C1 - candidate:** primary-camera observations. **C2 - environment:** secondary observations in Mode B, or a mirror view within the primary image in Mode C. **C3 - response capture:** a conceptual integration boundary; the bounded question UI must not be presented as a validated general response-capture or external CBT integration. No explicit C3 implementation was located in this audit.

### IPIME, identity and privacy

IPIME evaluates institutional policy against contextual assessments and bounded recommendations. It is policy-as-code within a research prototype, not a certification or an autonomous disciplinary engine. Operational protection and a human misconduct decision are distinct. An absent phone does not establish that all independent protections should be inactive.

Normal candidate workflows retain consent, enrolment, identity and readiness gates. Browser face/liveness outputs are bounded attestations; the documented luminance descriptor and geometric proxies are not certified recognition or presentation-attack resistance. Local monitoring does not upload raw audiovisual streams to staff portals. This does not mean identity data is non-sensitive: protect biometric representations, account data and institutional records separately.

## Evidence and acceptance

**Interface screenshot gallery withheld pending provenance review; no candidate/camera/governance acceptance is implied.**

This portfolio publishes explanatory diagrams and source-linked engineering documentation, not application screenshots. See the [evidence matrix](docs/portfolio/evidence-matrix.md) and [publication scope](docs/portfolio/provenance.md). Missing candidate identity, camera readiness, active examination and populated governance captures are not evidence of successful acceptance. Issue #2 remains unresolved.

## Deployment and verification

For the historical recovery installation only, consult [native runtime integration](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/native_runtime_integration.md). Preserve its environment and database; do not run a fresh-install seeder against existing data. Native reference ports are frontend 3100 and API 8765. `NEXT_PUBLIC_API_BASE_URL` is compiled at frontend build time.

Historical deployment references (not validated installation instructions for main): review [Docker deployment](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/docker_deployment.md) and [restricted deployment alternatives](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/runtime_deployment_alternatives.md). The stock demo seeder's bypass-profile/enrolled-only assignment incompatibility is recorded as a provisioning blocker for the recovery baseline. No cloud activation is represented here.

Run validation only in a configured disposable development/test environment:

```powershell
npm.cmd ci
npm.cmd run test -w apps/web
npm.cmd run typecheck -w apps/web
npm.cmd run lint -w apps/web
npm.cmd run build -w apps/web
python -m pytest -q
```

The [24 October 2026 recovery-revision report](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/native_runtime_integration.md) records 149 frontend tests, 116 backend tests, successful TypeScript/lint/build and isolated staff browser recovery checks. These are historical engineering results, not fresh runs, independent certification, detector accuracy metrics or physical acceptance.

## Acceptance boundaries

- Issue #2: Exam Protect can reflect monitoring integrity independently of phone-positive evidence; investigation is unfinished.
- Current real-camera, candidate biometric, background/minimisation and sleep/resume acceptance remains separate.
- In the recovery revision, the evidence outbox is tab-scoped. Corrupt storage blocks delivery visibly; tab closure can lose retained metadata.
- An event generated while completion is already in flight can remain unresolved after session closure.
- Live PostgreSQL concurrency for the runtime recovery and response-body timeout handling remain unverified.
- Historical dependency-security findings were not remediated or re-audited by this runtime work. No production-security approval is implied.
- Interface captures are withheld. Never publish private fixtures, credentials, tokens, biometric records or Trial 17 evidence.

## Research and innovation

The proposed research contribution under study is the integration of local multimodal observations, contextual explanations, institutional policy and accountable human review. This is a design proposition, not a claim of novelty, superior accuracy or peer-reviewed validation.

Trace the implementation through [governance services](src/serps_pop/governance/services.py), [contextual engine](src/serps_pop/governance/engine.py), [historical recovery evidence services](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/src/serps_pop/evidence/services.py), [prototype limitations](docs/prototype_limitations.md) and the [dissertation alignment matrix](docs/dissertation_alignment_matrix.md). Historical reports must be read with their dates and validation scopes.

## Roadmap

1. Resolve and independently test Issue #2 without weakening independent protections.
2. Complete consenting-volunteer identity/camera acceptance and genuine governance-view capture.
3. Close dependency-security and synthetic provisioning blockers.
4. Validate PostgreSQL concurrency and completion/evidence integrity boundaries.
5. Evaluate restricted staging only after separate authorization; external assessment integration remains bounded/planned work.

## Contribute and contact

Use [SERPS issues](https://github.com/basil-emeokoro/SERPS/issues) for reproducible, non-sensitive reports. Describe expected behaviour, actual behaviour and synthetic reproduction steps. Never attach credentials, tokens, biometric imagery or confidential examination records. Propose a private disclosure channel with the maintainer before sharing sensitive security details.

Maintainer: [Basil Emeokoro](https://github.com/basil-emeokoro). Changes to identity, evidence integrity or policy need focused regression evidence and human review. No production readiness, legal compliance or institutional endorsement is claimed.
