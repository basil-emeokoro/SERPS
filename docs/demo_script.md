# SERPS RC1 Dissertation Demonstration Script

## Demonstration objective and duration

Demonstrate that SERPS converts bounded browser/camera evidence into explainable, policy-governed, human-controlled operational records across candidate, reviewer, and administrator portals. Recommended duration: **15-18 minutes**, plus 3 minutes for questions.

## Preparation

Use a migrated fresh database, seeded accounts, two distinct cameras, and three browser profiles or private windows for candidate/reviewer/admin roles. Pre-test permissions. Keep `demo_checklist.md`, `prototype_limitations.md`, and API health available. Never display passwords, tokens, environment files, or private candidate data.

## Script

### 1. Position the research contribution (1 minute)

Say: “SERPS is an explainable multi-modal identity assurance, monitoring, and governance layer for integration with assessment systems. This workspace is a bounded demonstration harness, not a complete CBT platform or secure browser. Evidence informs policy and human review; it does not automatically declare misconduct.”

Show the landing page and governance pipeline.

### 2. Candidate registration and authentication (2 minutes)

Register a fresh candidate or explain the seeded candidate. Sign in and show that role-aware navigation exposes only the Candidate Portal. Point out institution binding and backend authorization.

### 3. Consent and readiness (3 minutes)

Accept monitoring, privacy, and institutional-policy consent. Explain that consent records are versioned and append-only. Run device discovery. Select two different cameras: primary candidate-facing and secondary environmental. Show both local previews and the message that raw video is not persisted. If a second camera is unavailable, stop and classify this step as an environmental limitation; do not simulate success in the UI.

### 4. Demonstration workspace and evidence (3 minutes)

Start the session. Show candidate/institution/examination/session identity, timer, question navigation, monitoring notice, both previews, and FaceDetector capability disclosure. Change tab visibility and, if safe, disconnect/reconnect the secondary camera. Explain the resulting EvidenceEvent types and camera-role metadata. Finish only after the reviewer demonstration if keeping the session active is useful.

### 5. Explainable reviewer workflow (4 minutes)

Sign in as reviewer. Filter/open the session. Show both camera metadata panels in one view. Walk through contributing evidence IDs, CIE risk score/level/confidence/explanation, bounded recommendation, and IPIME outcome. Emphasize that no fabricated remote video is shown. Choose **Request More Evidence** or another supported action, enter a clear rationale, confirm, and show the appended decision/timeline. Generate a structured report.

### 6. Administrator oversight (2 minutes)

Sign in as administrator. Show institution-scoped totals, risk distribution, unresolved cases, primary/secondary connections, failures, policy, and recent audit. Open the read-only session view and explain separation of reviewer decision authority.

### 7. Close and defend limitations (1-3 minutes)

Finish the candidate session and confirm completed status/media cleanup. State the exact database/hardware verification status. Summarize future work: PostgreSQL proof where unavailable, comprehensive hardware/browser E2E, production identity provider, secure-browser integration, remote media infrastructure, load testing, privacy operations, and deployment hardening.

## Recommended screenshots

1. RC1 landing page and governance pipeline.
2. Candidate readiness summary with two distinct camera previews (only with real hardware).
3. Demonstration workspace showing timer, monitoring notice, and dual local views.
4. Reviewer queue with risk and both camera statuses.
5. Reviewer detail showing CIE explanation, recommendation, and IPIME outcome.
6. Decision confirmation and persisted timeline entry.
7. Administrator metrics and dual-camera oversight.
8. Structured report/timeline summary.

Crop screenshots to exclude credentials, tokens, device IDs that are not privacy-safe, browser profile data, and unrelated desktop content. Caption metadata-only panels accurately; never caption them as live remote video.

## Contingency script

If cameras or PostgreSQL are unavailable, use the passing integrated API workflow and existing component tests as evidence, clearly label device inputs as simulated, and demonstrate protected portal routes/metadata. Do not conceal the limitation or delay the viva attempting infrastructure repair.
