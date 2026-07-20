# RC1 Defence Readiness Checklist

## Classification

- [x] Use **Research Prototype Version 1.0 RC1 — Environment Validation Pending**.
- [x] State that SERPS is a bounded research prototype, not production-ready.
- [x] State that SERPS integrates with an assessment platform and is not a complete CBT, LMS, or secure browser.
- [x] Do not create an RC1 tag before approval.

## Audit and security

- [x] Independent audit and traceability documents committed.
- [x] Candidate EvidenceEvent creation restricted to the owning candidate and allowed browser evidence.
- [x] Reviewer/administrator candidate-evidence injection denied.
- [x] Cross-institution and cross-candidate access denied.
- [x] Denied evidence does not trigger the governance chain.
- [x] Identity AuditLog create allowed; update/delete/replacement rejected.
- [x] Append-only claim limited to supported application/ORM interfaces.
- [x] JWT algorithm, signature, issuer, audience, type, expiry, issue time, subject, institution, and role validated.
- [x] Protected requests reload active trusted user state.
- [x] Refresh/access revocation limitation documented.
- [x] Browser tokens/session-storage limitation documented.
- [x] Device/camera/permission inputs labelled browser-attested or client-reported.
- [x] No browser attestation described as independent hardware proof.

## Operational claim boundaries

- [x] Ten application routes distinguished from nine pages reported by static generation.
- [x] Candidate-side distinct dual-camera acquisition and local previews described as implemented.
- [x] Reviewer/admin camera panels described as metadata/status placeholders.
- [x] Remote reviewer video streaming described as not implemented.
- [x] WebRTC signalling and remote secondary-device pairing described as not implemented.
- [x] Raw-video storage described as not implemented.
- [x] Bounded three-question workspace described as a demonstration harness.
- [x] Human reviewer retains decision authority; CIE/recommendation/IPIME remain advisory.

## Verification evidence

- [x] Backend compile gate prepared.
- [x] Full backend suite: 51 passed in 145.06 seconds.
- [x] Frontend suite: 18 tests.
- [x] TypeScript gate.
- [x] ESLint gate.
- [x] Production build gate.
- [x] OpenAPI regenerated after schema hardening.
- [x] Alembic single head/history checked.
- [x] SQLite migrations 0001-0005 and seed verified as bounded fallback evidence.
- [x] Compose configuration validated.
- [x] npm audit: zero vulnerabilities.
- [x] `git diff --check` and final repository status required before handoff.

## Environment and manual evidence

- [ ] Docker engine runtime — blocked; commands were unresponsive.
- [ ] PostgreSQL migrations/workflow — blocked; Docker unavailable and no installed local PostgreSQL found.
- [x] Candidate browser authentication.
- [x] Immutable consent submission.
- [x] Reviewer portal authentication and scoped queue rendering.
- [x] Administrator portal authentication and scoped oversight rendering.
- [ ] Two physical cameras — unavailable in the controlled browser.
- [ ] Simultaneous dual local previews — blocked by hardware.
- [ ] Manual session start/workspace/governance/review/completion — blocked by honest readiness enforcement.
- [x] Automated/simulated workflow evidence labelled separately from manual evidence.
- [x] Hardware and environment blockers retained in the final classification.

## Dissertation demonstration preparation

- [x] Candidate-readiness screenshot excludes credentials and tokens.
- [x] Reviewer screenshot accurately shows metadata/API-backed portal state.
- [x] Administrator screenshot accurately shows institution-scoped oversight.
- [x] Screenshots stored under `docs/screenshots/` in the final repository package.
- [x] Demo script includes a stop-and-disclose path when two cameras are unavailable.
- [x] Limitations, security review, release document, progress, and hardening report agree.
- [x] Examiner can defend why no remote video is shown.
- [x] Examiner can explain client attestation versus trusted server evidence.
- [x] Examiner can explain human-controlled governance and immutable record boundaries.

## Repository hygiene

- [x] Local `.env` files ignored and excluded.
- [x] No real credentials, tokens, or database dump committed.
- [x] `Complete Assessment Platform.txt` remains untracked and untouched.
- [x] Separate logical checkpoints used and pushed.
- [x] No unrelated WebRTC, SEB, LMS, CBT, or architectural redesign added.

## Defence decision

SERPS is ready for a controlled dissertation demonstration with disclosed environment limitations. It is not ready for production or an institutional pilot. The next phase is evidence capture and Chapter 3-5 alignment; Docker/PostgreSQL and two-camera validation should be repeated when the required environment is available.
