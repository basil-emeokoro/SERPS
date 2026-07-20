# SERPS Examiner Demonstration Checklist

## Before the session

- [ ] Use a fresh local database or known clean demonstration volume.
- [ ] Confirm Python, Node.js, npm, and optionally Docker prerequisites.
- [ ] Configure a strong `SERPS_JWT_SECRET`, database credentials, CORS origin, and `SERPS_DEMO_PASSWORD` outside Git.
- [ ] Run migrations and confirm Alembic head `0005_sprint3d_dual_camera`.
- [ ] Seed demo users and confirm the seeder reports zero pre-created sessions.
- [ ] Connect two distinct video-input devices and test browser permission behavior.
- [ ] Start API and web services; confirm health and login pages.
- [ ] Keep `prototype_limitations.md` available for questions.

## Candidate walkthrough

- [ ] Sign in as the candidate and show the eligible assignment.
- [ ] Accept the three-part versioned consent.
- [ ] Run the device check and explain browser attestation limitations.
- [ ] Discover and select distinct primary and secondary cameras.
- [ ] Show both local previews and the no-raw-video privacy notice.
- [ ] Start the session and open the demonstration workspace.
- [ ] Show timer, sample questions, navigation, monitoring notice, and FaceDetector capability status.
- [ ] Trigger a visibility loss and, if safe, a secondary-camera disconnect.

## Reviewer walkthrough

- [ ] Sign in as reviewer and open the institution-scoped queue.
- [ ] Show primary and secondary camera metadata in one view.
- [ ] Explain CIE evidence IDs, risk score/level, confidence, and rationale.
- [ ] Show the bounded recommendation and IPIME policy outcome.
- [ ] Record a supported decision with mandatory rationale and confirmation.
- [ ] Generate and retrieve a structured report.

## Administrator walkthrough

- [ ] Sign in as administrator.
- [ ] Show live metrics, risk counts, camera failures, active policy, and recent audit.
- [ ] Open session oversight and explain that it is read-only.
- [ ] Show both camera states, reviewer history, timeline, and report metadata.

## Close

- [ ] Finish the candidate demonstration and confirm media cleanup/completed status.
- [ ] State that reviewer/admin views are metadata-only, not remote live streams.
- [ ] State PostgreSQL and hardware verification status accurately for the current environment.
- [ ] Reiterate that SERPS integrates with assessment systems and preserves human decision authority.
