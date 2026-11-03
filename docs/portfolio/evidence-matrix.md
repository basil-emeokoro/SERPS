# Capability and evidence matrix

This matrix distinguishes source implementation from demonstration and physical acceptance. No screenshots are included. Historical recovery statements refer only to revision `0cc012697fdf19311b549e5ceae17571fd53f744`, not feature parity on main.

| Feature | Source implementation | Demonstrated / tested | Independent acceptance | Outstanding limit | Evidence |
| --- | --- | --- | --- | --- | --- |
| Identity and access | Role/institution gates and bounded identity workflows | Historical prototype tests | Not established here | Real candidate biometric acceptance pending | [Identity source](../../src/serps_pop/identity/services.py) |
| C1 candidate / C2 environment | Mode-aware local observations | Historical routing and controlled tests | Current all-mode physical acceptance absent | A/C distinct-device readiness conflict; mirror is not independent feed | [Mode report](../proctoring_modes_implementation_status.md) |
| C3 response capture | Bounded demonstration question UI, not a verified general C3 subsystem | No C3 acceptance claimed | Not established | External response integration planned/unverified | [Limitations](../prototype_limitations.md) |
| Evidence to CIE to ADS | Contextual assessment and bounded advisory recommendation | Historical engineering evidence only | No physical end-to-end claim | No populated governance capture published | [Engine](../../src/serps_pop/governance/engine.py) |
| IPIME / human review | Institutional policy evaluation and reviewer decisions | Historical automated workflow tests | Not independently certified | Operational protection acceptance incomplete | [Services](../../src/serps_pop/governance/services.py) |
| Ordered outbox / atomic delivery / authentication recovery | Recovery-revision features; absent from publication baseline | Historical 149 frontend / 116 backend report, 24 October 2026 | Not fresh main acceptance | Retention, completion consistency and deployment validation pending | [Pinned recovery report](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/native_runtime_integration.md) |
| Cloud readiness | Preparation documentation | No deployment in this portfolio | Not approved | Security, provisioning and separate approval gates | [Historical deployment scope](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/runtime_deployment_alternatives.md) |

The six historical interface images and their manifest remain excluded pending provenance review. No detector, camera, identity or governance success is manufactured by these documents.
