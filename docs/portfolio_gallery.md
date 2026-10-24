# SERPS portfolio gallery — public-safe capture plan

**Status:** Capture plan only. No screenshots or live deployment are represented as completed by this document.

## Gallery storyboard

| Asset | Capture target | Caption standard |
| --- | --- | --- |
| `01-landing.png` | Research landing page and governance pipeline | Research prototype overview |
| `02-candidate-readiness.png` | Camera/device readiness with synthetic account | Two distinct local camera previews, only when genuine hardware is available |
| `03-exam-workspace.png` | Demonstration questions, monitoring notice and evidence state | Bounded examination demonstration; not a secure browser |
| `04-evidence-context.png` | EvidenceEvent timeline and contextual explanation | Explainable structured metadata; not proof of misconduct |
| `05-reviewer-governance.png` | Reviewer queue, contextual assessment and policy decision | Human-in-the-loop review and audit |
| `06-admin-oversight.png` | Institution-scoped administrative summary | Governance oversight, not reviewer decision authority |
| `07-test-evidence.png` | Sanitised test/CI output | Label with exact commit, test scope and date |
| `08-deployment-architecture.png` | Conceptual staging diagram | Proposed infrastructure; no live deployment claimed |

## Privacy and provenance checklist

- [ ] Use disposable synthetic accounts, institutions, candidate IDs and sessions.
- [ ] Remove names, emails, tokens, passwords, local paths, device serials, database content, browser profiles and private URLs.
- [ ] Never publish real biometric images, facial descriptors, exam evidence, live camera scenes with identifiable people or raw audio.
- [ ] Confirm the screenshot matches the actual commit and functioning interface; do not substitute mockups without a clear **Concept** label.
- [ ] Mark simulated detectors and camera doubles as **Synthetic test**, never **Physical acceptance**.
- [ ] Crop or redact before committing; inspect embedded image metadata and visible browser/devtools information.
- [ ] Include alt text, a concise caption, capture date, and source commit for each accepted asset.
- [ ] Keep images reasonably sized and accessible on mobile.

## Publishing workflow

1. Capture and independently review the assets; do not upload raw captures to a public repository.
2. Add approved images under `docs/assets/screenshots/`.
3. Insert a small gallery into the README using relative links and meaningful alt text.
4. Link each screenshot to the relevant [user manual](user_manual.md), [demonstration script](demo_script.md) or [architecture reference](architecture_overview.md).
5. Verify GitHub rendering, broken links, file sizes and privacy redaction in a draft PR.

A screenshot gallery is **not** evidence of real-camera, security or production acceptance. Keep the release's [known limitations](native_runtime_integration.md) visible.
