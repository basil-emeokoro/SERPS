# Engineering case study

## From problem to architecture

| Requirement | Implementation evidence | Engineering boundary |
| --- | --- | --- |
| Restrict evidence to authorized sessions | [Evidence service](../../src/serps_pop/evidence/services.py), [API tests](../../tests/test_evidence_api.py) | Authorization tests do not prove the browser observation is genuine |
| Explain contextual reasoning | [CIE engine](../../src/serps_pop/governance/engine.py) | Deterministic bounded rules; confidence is not demonstrated probability calibration |
| Separate advice from authority | [Governance service](../../src/serps_pop/governance/services.py), [governance tests](../../tests/test_governance.py) | Recommendations are advisory; policy protection is not a misconduct verdict |
| Preserve role/institution boundaries | [Identity services](../../src/serps_pop/identity/services.py), [RBAC tests](../../tests/test_auth_rbac_sessions.py) | No penetration-test or deployment certification claim |
| Handle heterogeneous camera arrangements | [Mode implementation report](../proctoring_modes_implementation_status.md) | Mode A/C readiness still retains distinct-device prerequisites |

## Technology choices and trade-offs

Next.js/React/TypeScript provides a browser-facing interface and typed contracts; FastAPI/Pydantic provides API boundaries; SQLAlchemy/Alembic separates persistence and schema evolution. These are observable choices, not evidence of a comparative technology-selection experiment. Browser inference limits routine raw-media transfer and avoids a remote streaming dependency, at the cost of device-dependent latency, permissions and resource contention. SQLite supports bounded local tests; PostgreSQL configuration is not proof of equivalent concurrency behavior.

## Monitoring and evidence pipeline

Primary candidate and secondary environment roles are distinct where Mode B supplies separate cameras. Mode A uses primary observations; Mode C uses a mirror within the same image and cannot claim independent corroboration. MediaPipe face geometry, EfficientDet-Lite0 person/phone classes and audio activity provide limited signals, not intent recognition. Audio RMS is activity measurement, not speech recognition.

Supported observations become structured EvidenceEvents. The CIE evaluates bounded temporal context and distinguishes unavailable detectors from adverse observations. ADS provides bounded advisory recommendations; IPIME applies institutional workflow policy. Reviewers receive structured evidence and explanations rather than remote raw video. Reports and audit records make actions inspectable, but storage immutability controls do not establish forensic tamper-proofing against every privileged attacker.

## Recovery work is revision-specific

A separate [24 October recovery report](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/native_runtime_integration.md) describes an ordered tab-scoped outbox, stable delivery identities, atomic evidence/governance handling and authentication interruption recovery. Those features belong to recovery revision `0cc0126`, not the main-based publication code. Do not copy their tests/results into a claim that main includes them.

Trade-offs remain: tab closure can lose pending metadata; a completion request can race with a new event; synchronous governance couples ingestion latency to downstream work; PostgreSQL replay concurrency remains unverified. The design must report unresolved delivery rather than silently erase it. No repair is made in this documentation phase.

## Quality assurance and security

The [workflow test](../../tests/test_sprint3e_e2e.py) exercises API contracts with synthetic inputs; it cannot validate actual cameras or human liveness. [Token tests](../../tests/test_token_security.py) and negative role/ownership tests cover selected security boundaries. Historical build, lint and type checks establish a revision-specific engineering result, not production readiness. See the [evaluation ledger](evaluation-and-reproducibility.md).

The documented identity descriptor is a bounded experimental representation, not certified biometric recognition. Session-storage tokens, access-token revocation timing, secret management, TLS, retention controls and independent security review require explicit deployment treatment. Historical dependency audits are time-bound; no current zero-vulnerability claim is made. [Prototype limitations](../prototype_limitations.md) contains historical statements that must be interpreted in their original context, not as live operational status.

## Open engineering work

Issue #2 remains unresolved: phone-policy controls and independent integrity protection must not be conflated. Recovery must not allow unauthorized continuation. Physical foreground/background, interruption and sleep/resume checks remain necessary. Scale testing needs a defined workload, service-level targets, database isolation and failure scenarios. A future fix must preserve governance authority and candidate evidence, not merely hide monitoring errors.

[Research statement](research-statement.md) · [Evaluation](evaluation-and-reproducibility.md) · [README](../../README.md)
