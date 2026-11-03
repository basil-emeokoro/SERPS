# Research statement

## Problem and motivation

SERPS investigates how local multimodal observations can support accountable human review in educational assessment without treating a sensor event as a misconduct verdict. The engineering problem is to preserve the chain from observation to contextual explanation, institutional policy and reviewer rationale. The research problem is whether that chain improves decisions without adding unjustified surveillance, bias or measurement error.

The prototype joins computer vision, explainable rules, secure software interfaces and institutional governance. Its proposed research gap is an evaluation question: how should uncertainty, operational failure and conflicting evidence be represented to reviewers? This portfolio does not claim that a literature review has established novelty or that existing systems lack these capabilities.

## Objectives and research questions

1. Separate an observation (for example, a phone-class detection) from an interpretation and an authorized operational action.
2. Study whether evidence-linked explanations help reviewers identify incorrect alerts, rather than merely increase their confidence.
3. Quantify the effects of missing modalities, connectivity interruptions and device quality on monitoring availability and false alerts.
4. Investigate whether monitoring changes assessment participation, response processes or score interpretations across groups and accommodations.

Candidate questions include: When does a second camera add useful information rather than correlated error? How should a system abstain when observations are unreliable? Can privacy-reduced representations preserve useful review evidence? What explanation content changes reviewer error rates and workload?

## Existing work and proposed contributions

The [contextual engine](../../src/serps_pop/governance/engine.py) combines supported events within bounded temporal rules and returns evidence-linked explanations. [Governance services](../../src/serps_pop/governance/services.py) persist advisory recommendations, policy evaluations and reviewer actions. This is a concrete prototype implementation, not a learned causal model or independently validated decision system.

Potential doctoral contributions are proposed: an uncertainty-aware multimodal evidence representation; experiments comparing explanation interfaces; an evaluation protocol joining monitoring performance with assessment validity; and a privacy/utility analysis with explicit missing-data treatment. Their originality would need a systematic literature review and comparative evaluation before any novelty claim.

## Explainability and human oversight

CIE reasoning, ADS recommendations and IPIME policy evaluation are separate stages. A rule explanation describes how a score arose; it does not establish that an observed event implies intent or misconduct. Human oversight must itself be evaluated for automation bias, disagreement, fatigue and inappropriate reliance. Candidate recourse, accessible explanations and documented review criteria should be designed with institutions, not assumed from a reviewer button.

## Psychometric validity and fairness

A monitoring score is not an ability estimate or evidence that an examination score is valid. Proposed studies should define the intended score interpretation and examine whether monitoring introduces construct-irrelevant demands, changes response processes, or disadvantages accommodated participation. No item calibration, reliability coefficient, differential-item-functioning analysis, criterion validity or subgroup fairness result is claimed here.

Future work should separate detector error, reviewer error and assessment-score effects. Prespecified subgroup analyses need adequate samples, consent and uncertainty intervals; failure to detect a difference must not be reported as proof of fairness. Accommodation requirements should be established before data collection. Demographic characteristics must not be inferred from camera data to manufacture fairness labels.

## Ethics, privacy and evidence

Local inference and metadata-only reviewer views limit raw-media transfer but do not make the system anonymous or risk-free. Derived identity representations remain sensitive. An institutional study needs a justified purpose, proportionate collection, retention/deletion controls, withdrawal procedures where applicable, and independent ethics review. Security controls and consent screens do not substitute for those approvals.

Current evidence is engineering evidence: source, controlled fixtures and dated regression reports. See [evaluation and reproducibility](evaluation-and-reproducibility.md). No participant dataset or model-performance benchmark is supplied by this portfolio. Candidate identity and physical-camera acceptance are incomplete; Operational protection acceptance remains incomplete. The prototype is not a full CBT platform, secure browser, certified biometric system or autonomous adjudicator.

## Validation path

Begin with reproducible synthetic fault injection and an explicitly consented hardware study, followed by a reviewer experiment with blinded, independently adjudicated cases. Only then consider a restricted institutional pilot. Define stopping rules, safety monitoring and a non-punitive participation design before collecting data. These are proposals, not completed collaborations or approved studies.

[Engineering case study](engineering-case-study.md) · [Doctoral directions](phd-research-directions.md) · [README](../../README.md)
