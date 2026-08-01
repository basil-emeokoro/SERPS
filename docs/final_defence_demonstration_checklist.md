# SERPS Final Defence Demonstration Checklist

Use this checklist for a controlled dissertation demonstration of the SERPS POP research prototype. Do not claim certified biometric identity, production liveness, remote video streaming, or hardware validation that has not been observed on the defence machine.

## Before the defence

- [ ] Connect the primary candidate-facing camera and a distinct secondary room/side-angle camera.
- [ ] Close applications that may hold either camera or the selected ports.
- [ ] Confirm the frontend points to the active Application Services port.
- [ ] Confirm the demonstration database contains the seeded institution, four role accounts, assignment, and active policy.
- [ ] Keep the demonstration password outside source control and available to the presenter.
- [ ] Use a current Chromium-based browser and clear stale SERPS site permissions if camera discovery fails.
- [ ] Disable notifications and hide unrelated tabs, secrets, terminal history, and personal data.

## Startup sequence

1. Start Docker Desktop only if PostgreSQL evidence is required; wait for the engine and database health check.
2. For the reliable local path, activate the Python environment and start Application Services on the configured backend port.
3. Start the Next.js frontend on the configured frontend port.
4. Open the home page and confirm the landing page, navigation drawer, governance cards, and service-health indicator.
5. Confirm `/health` is healthy and the frontend can reach Application Services.

## Login sequence

- [ ] Enter institution code `MIVA` for institution-scoped accounts.
- [ ] Sign in with each seeded role and verify the role-specific redirect.
- [ ] Confirm Candidate cannot open reviewer or administrator pages.
- [ ] Confirm Reviewer/Proctor, Administrator, and System Administrator reach their authorised portals.
- [ ] Sign out between roles so prior session state cannot affect the demonstration.

## Registration and identity lifecycle

- [ ] Show Candidate, Reviewer, and Administrator registration choices.
- [ ] Register a disposable candidate and explain bounded prototype email verification.
- [ ] Show the centred guide, live lighting/distance/one-face feedback, and six ordered captures.
- [ ] Complete the randomized movement sequence and explain that it is browser-attested prototype liveness.
- [ ] Sign in with password first, then complete the separate facial-authentication stage.
- [ ] Show that only `Verified` reaches the Candidate Portal.
- [ ] Submit a disposable reviewer or administrator request and show `pending approval`.
- [ ] As System Administrator, record an approval/rejection rationale and show the resulting audit/status change.
- [ ] Identify seeded defence users discreetly as demonstration accounts and explain their explicit bypass.

## Candidate walkthrough

1. Sign in as Candidate and show the password and facial-authentication separation. The seeded defence candidate uses the explicit demonstration bypass.
2. Read and accept monitoring consent, privacy notice, and institutional policy.
3. Select **Discover cameras and check device** and approve browser camera/microphone permission.
4. Select two different devices: primary for face/upper body and secondary for room, desk, or side angle.
5. Preview both cameras and verify both local previews are simultaneously visible.
6. Show the readiness summary. Do not proceed if any camera, permission, device check, consent, or assignment is incomplete.
7. Start the bounded workspace, navigate sample questions, and explain the timer and local indicators.
8. Generate only observable evidence, such as a tab focus change or camera connection event.
9. Finish the demonstration and confirm both local media tracks stop.

## Camera demonstration

- [ ] Browser permission is granted for the selected SERPS origin.
- [ ] Device discovery reports at least two video-input devices.
- [ ] Primary and secondary selections use different device identifiers.
- [ ] Both local previews are live at the same time.
- [ ] Camera labels, roles, connection status, last-seen timestamps, and failure reasons are recorded as metadata.
- [ ] Explain that raw video is not persisted and reviewer/administrator screens are metadata/status views.
- [ ] If fewer than two cameras are exposed, show the blocked readiness state and do not claim dual-camera validation.
- [ ] If `FaceDetector` is unavailable, show the stated fallback and do not claim facial-recognition or enrolment success.

## Evidence and governance demonstration

1. Open the reviewer queue after candidate evidence is recorded.
2. Show the timeline, contextual assessment, risk level, explanation, and contributing evidence.
3. Explain that the recommendation is advisory and institutional policy constrains the response.
4. Record one justified human reviewer action and show its append-only audit/timeline entry.
5. Generate or open the structured report and relate it to evidence, policy, recommendation, and review.
6. Open Administrator Oversight and show metrics, camera status, unresolved cases, policy, and audit activity.
7. Open System Administration and explain the research-prototype boundary of its summaries.

## Reviewer walkthrough

- [ ] Filter the queue by risk, review status, and session state.
- [ ] Open a session and inspect both metadata-only camera panels.
- [ ] Trace a risk assessment to contributing EvidenceEvents.
- [ ] Compare the advisory recommendation with the institutional-policy outcome.
- [ ] Submit a supported action with a substantive rationale and confirmation.
- [ ] Confirm persistence in history, timeline, audit trail, and report.

## Administrator walkthrough

- [ ] Show candidate/session totals, unresolved cases, risk counts, and camera metrics.
- [ ] Show the active institutional policy and recent governance activity.
- [ ] Open a session in read-only oversight mode.
- [ ] Explain that oversight does not silently replace the reviewer’s human decision.
- [ ] Show platform summaries with System Administrator credentials without claiming unimplemented account-lifecycle controls.

## Screenshots to capture

- [ ] Landing page, open navigation drawer, and expanded governance cards.
- [ ] Academic authentication page without visible credentials.
- [ ] Candidate/reviewer/administrator registration selection.
- [ ] Six-direction facial enrolment progress and live guidance.
- [ ] Randomized liveness prompt and facial-authentication outcome.
- [ ] System Administrator registration approval queue.
- [ ] Candidate assignment, consent, device readiness, and camera selection.
- [ ] Both local camera previews simultaneously.
- [ ] Examination workspace with camera status and sample question.
- [ ] Evidence timeline and contextual explanation.
- [ ] Reviewer queue, session detail, and persisted human decision.
- [ ] Structured governance report.
- [ ] Administrator metrics/policy and System Administrator overview.
- [ ] Honest blocked state if fewer than two cameras are available.

## Likely examiner questions

**Why two cameras?** The primary view observes the candidate while the secondary provides room or side-angle context. They are complementary evidence sources, not automatic proof of misconduct.

**Does SERPS record video?** The prototype displays local previews and persists operational metadata and EvidenceEvents. It does not persist raw video or provide production remote-media streaming.

**Is facial recognition implemented?** A bounded research-prototype comparison is implemented. It uses browser face detection, spatial movement proxies, and a compact 8x8 luminance descriptor; it is not certified recognition, identity proofing, blink/depth analysis, anti-spoofing, or production liveness.

**Can SERPS automatically fail a candidate?** No. Deterministic assessment and bounded recommendations support governance; institutional policy and a human reviewer control the operational decision.

**How is access controlled?** Backend authentication, role checks, institution scoping, and active-user validation protect role-specific operations. Seeded accounts are used for the controlled demonstration.

**Why SQLite?** SQLite is the reliable local dissertation path. The architecture supports PostgreSQL, but engine health and credential alignment must be verified before claiming a PostgreSQL-backed run.

**What remains before production?** Validated biometric algorithms, anti-spoofing, fairness/calibration studies, encrypted biometric storage, subject-rights and retention controls, trusted institutional verification, production media architecture, hardened token handling, PostgreSQL deployment proof, accessibility/security/load testing, and controlled pilot evaluation.

## Final reset

- [ ] Sign out, stop camera tracks, and close the demonstration tab.
- [ ] Preserve only approved screenshots with no credentials or personal data.
- [ ] Record backend/frontend versions, database mode, browser, camera count, and observed limitations.
- [ ] Stop local services after the session if no longer required.
