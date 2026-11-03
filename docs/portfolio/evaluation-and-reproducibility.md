# Evaluation and reproducibility

## What has and has not been evaluated

This ledger separates software behavior from model quality, human performance and psychometric validity. This documentation phase does not run application tests or experiments. No private examination records or participant material are used.

| Evidence | Revision / setting | Quantitative information | Interpretation |
| --- | --- | --- | --- |
| Recovery regression report | Recovery `0cc012697fdf19311b549e5ceae17571fd53f744`; completed 24 October 2026; native SQLite tests and isolated synthetic staff browser workflow | 149 frontend tests across 21 files; 116 backend tests, 339.57 seconds | Historical software tests, not participants, accuracy, throughput or current main acceptance |
| Recovery browser checks | Same report; synthetic staff fixture; isolated synthetic environment | No participant sample size or model metric reported | Login, refresh, outage/reconnection and remount checks; not candidate biometric or physical-camera acceptance |
| Earlier Sprint 3E report | Report identifies starting checkpoint `1f61c31d5fb91f0174da39afacf6c921ba51769a`; SQLite and simulated device attestations | 32 backend and 18 frontend tests reported | Earlier historical suite; report's starting checkpoint is not a verified final tested commit, so not pooled with recovery totals |
| Detector/hardware observations | Dated [mode report](../proctoring_modes_implementation_status.md), 1 August 2026 | No benchmark denominator or confidence interval established here | A bounded Mode A diagnostic is not validation of all modes or a detector performance study |

Sources: [pinned recovery report](https://github.com/basil-emeokoro/SERPS/blob/0cc012697fdf19311b549e5ceae17571fd53f744/docs/native_runtime_integration.md); [Sprint 3E report at the Phase 2 base](https://github.com/basil-emeokoro/SERPS/blob/6ca36a7964c53174d70f8c1ceaeb882e72f94fce/docs/sprint3e_validation_report.md). The older report mixes dated audit statements; it is not evidence of current dependency safety or current database service health.

## Data and experimental setting

Repository tests include synthetic database records, deterministic descriptors and controlled event inputs. They are software fixtures, not a representative participant dataset. No reusable consented human dataset, recruited sample size, demographic distribution, handwriting corpus or adjudicated misconduct benchmark is supplied in this portfolio. The absence of published sample information must not be converted into invented counts or performance claims.

No verified precision/recall, false-alert rate, biometric false-accept/reject rate, calibration error, subgroup disparity, reviewer agreement, handwriting error rate or psychometric reliability result is claimed. Test runtime is not inference latency or production capacity.

## Reproducibility requirements

Pin the revision and record dependency versions, model assets, browser/device conditions and the scope of each test. Main and historical recovery revisions must remain separate evidence units. Use synthetic, disposable fixtures and retain results with their exact revision; never include private participant data or sensitive operational logs in a public reproduction package.

The repository's [test fixtures](../../tests/conftest.py) and versioned manifests provide the software starting point. Reproduction requires environment-specific preparation and does not itself establish deployment or hardware acceptance. Candidate studies require consent, normal identity/readiness controls and appropriate ethics review. Detailed operational procedures belong in development records, not this research summary.

## Proposed experiments and metrics

| Objective | Proposed design | Metrics to report, not existing results |
| --- | --- | --- |
| Monitoring utility | Consent-based crossed lighting/device/pose/mode conditions; held-out participants; independent annotation | Event precision/recall, false alerts per hour, unavailable time, latency distributions; uncertainty intervals |
| Robustness | Controlled missing-modality, reconnect and delayed-delivery scenarios | Recovery time, duplicate/lost/reordered event counts, unauthorized continuation incidents |
| Explanation utility | Randomized reviewer comparison with blinded adjudicated cases | Decision error, disagreement, time, workload and inappropriate reliance |
| Fairness and assessment validity | Prespecified accommodations/groups, justified sample-size planning, response-process study | Error differences and intervals; assessment-score effects; construct-irrelevant variance hypotheses |
| Privacy/utility | Compare justified metadata representations and retention policies | Review utility, exposure surface, reidentification/threat analysis; no automatic privacy guarantee |

## Threats to validity

Synthetic input realism, non-independent event windows, device selection, small convenience samples, label uncertainty, reviewer expectancy and train/test leakage can distort conclusions. Participant-separated splits, blinded annotation, preregistered hypotheses, versioned protocols and independent replication are proposed mitigations. Repeated frames from one person must not be counted as independent participants. Missing observations may be non-random; report missingness rather than coding it as innocence or misconduct.

Hardware, candidate liveness, PostgreSQL concurrency, field security and institutional pilots remain outside the acceptance established by this portfolio. No software count should be presented as psychometric evidence.
