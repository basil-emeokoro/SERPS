# Doctoral research directions

Two connected proposals, not completed findings, funded projects or established collaborations. Their originality requires literature review, suitable supervision, ethics approval and comparative evidence. SERPS offers a bounded engineering starting point, not validated research conclusions.

## Direction 1: Explainable, privacy-preserving multimodal AI for human assessment

**Motivation.** Assessment monitoring must handle uncertainty without turning a weak sensor correlation into a disciplinary conclusion. Privacy reduction, operational availability and useful human explanations may conflict.

**Questions.** How should heterogeneous and missing observations be fused with calibrated uncertainty? When should a system abstain? Which evidence-linked explanations improve review correctness rather than confidence alone? What privacy/utility trade-offs are acceptable to candidates and institutions?

**Proposed methodology.** Begin with the existing deterministic CIE as a transparent baseline, compare prespecified fusion/abstention alternatives, and maintain independent role and policy gates. Use consented participant-separated data, controlled missingness and unseen-device evaluation. Follow with a blinded reviewer study comparing explanation formats. Sample sizes should follow a power/precision analysis for the chosen outcome, not an invented target.

**Potential contribution.** An evaluable evidence representation and abstention protocol connecting model uncertainty, policy boundaries and human review; a reproducible multi-objective evaluation protocol. No novelty or superiority is yet established.

**Evaluation.** Event-level and session-level errors, calibration, coverage/abstention, availability, reviewer error and workload, subgroup uncertainty and privacy threat analysis. Include single-modality and no-automation baselines; separate detector errors from policy and reviewer errors.

**Ethics and challenges.** Consent under institutional power imbalance, accommodations, sensitive identity representations, spurious correlations, adversarial behavior and automation bias need explicit treatment. Proposed data minimization is not a differential-privacy guarantee. Avoid operational sanctions during exploratory experiments.

**Connection to SERPS.** Source implements local observations, bounded CIE/ADS/IPIME stages and reviewer records. Learning-based fusion, calibrated uncertainty, privacy guarantees and independent human-subject validation are proposed work. Issue #2 and operational integrity must be resolved before any pilot that relies on protection behavior.

## Direction 2: Handwriting-centered human-AI assessment

**Motivation.** Handwriting and digital ink may support assessment tasks that require working, diagrams or mathematical reasoning. Recognition errors and device affordances could distort the construct being assessed. This is a research hypothesis, not a demonstrated SERPS capability.

**Questions.** Can spatial/temporal ink representations retain evidence needed for valid assessment? How do recognition errors affect feedback or scoring across scripts, writing styles, disabilities and devices? When should an assistant defer to a human? Can feedback improve learning without revealing answers or introducing construct-irrelevant assistance?

**Proposed methodology.** Design a consented digital-ink capture protocol with timestamps, stroke geometry and device metadata only where justified. Compare offline-image and online-ink recognition baselines; separate transcription from semantic scoring. Use writer-separated and task-separated evaluation, independently labelled responses and uncertainty-aware human correction. Progress from recognition validation to formative-feedback studies before any high-stakes scoring use.

**Potential contribution.** A response-provenance model linking ink, recognition uncertainty, reviewer correction and assessment interpretation; methods for auditable feedback and measurement-aware error analysis. No handwriting model, dataset or response-capture subsystem has been delivered by this portfolio.

**Evaluation framework.** Character/word error rates for text, expression/structure accuracy for mathematics, correction effort and calibration; then rubric agreement, score error, response-process evidence and learning outcomes with an appropriate comparison group. Psychometric analyses require a defined construct, test design and adequate samples. A high transcription score does not establish valid grading.

**Ethics and unresolved challenges.** Handwriting can identify a person; retain only justified signals and establish deletion/access controls. Accommodations, language/script coverage, annotation ownership, children’s participation where relevant, feedback leakage and automation bias require separate approval. Learning analytics should not silently become surveillance or personality inference.

**Connection to SERPS.** C3 response capture is currently conceptual/unverified beyond a bounded question UI. Existing event provenance and human-governance concepts could inform a future integration; no functional C3, handwriting recognition, feedback engine, learning analytics or psychometric calibration is claimed on main.

## A staged programme

First: structured literature review and stakeholder requirements, with a precise contribution hypothesis. Second: low-risk offline baselines and data governance. Third: consented controlled studies and independent validation. Finally: a restricted pilot only after safety and validity criteria are met. These stages are proposed, not completed milestones.

[Research statement](research-statement.md) · [Evaluation framework](evaluation-and-reproducibility.md) · [Engineering case study](engineering-case-study.md)
