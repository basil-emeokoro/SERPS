# SERPS RC1 User Manual

## Purpose

SERPS is an explainable monitoring and governance layer for assessment-system integration. RC1 includes a bounded examination workspace for demonstration; it is not a full assessment platform or secure browser.

## Candidate

1. Open `/register?type=candidate`, enter the institution code, candidate identifier, name, email, and a matching 12-character password, then accept the biometric-processing notice. The prototype records an automatic bounded email-verification result; it does not claim access to an institutional identity registry.
2. Continue to `/enrolment`. Grant camera permission and wait for both **Camera active** and **Detector ready**. The MediaPipe model and WebAssembly runtime load from the SERPS application; no detector CDN is required.
3. Align exactly one face with the central guide. Confirm that the requested and detected orientations agree, then hold the pose until the stability indicator reaches 100 percent.
4. Complete the ordered observations: forward, left, right, upward, downward, and return to centre. Each step checks one-face presence, lighting, distance, roll, the required geometric pose proxy, and a stable hold before progressing.
5. Complete the randomized movement/liveness prompts deliberately and in the displayed order. A rapid static sequence is rejected. Retry or cancel if any prompt cannot be validated. Raw images and video remain local; only an experimental derived numeric descriptor, quality summary, confidence, and timestamps are persisted.
6. Sign in at `/login` with institution code, email, and password. Normal candidates then complete a separate randomized facial-authentication stage. Only `Verified` proceeds to the Candidate Portal; `Retry Required`, `Manual Review`, and `Authentication Failed` do not.
6. Open the Candidate Portal and verify the assigned demonstration. Read and accept monitoring consent, privacy notice, and institutional policy.
7. Select **Discover cameras and check device**. Permit required browser camera/microphone access.
8. Choose two different physical devices: primary is candidate-facing; secondary shows the room, desk, or side angle. Duplicate device identifiers are rejected.
9. Preview both cameras simultaneously. Camera labels, privacy-safe device identifiers, roles, timestamps, readiness, and connection EvidenceEvents are persisted; raw video is not.
10. Start only when identity verification, consent, device checks, permissions, and both distinct cameras pass. A normal biometric candidate may receive a bounded periodic identity prompt after two minutes in the demonstration workspace.
11. Complete the sample questions and select **Finish demonstration**. SERPS stops local media tracks and preserves evidence/governance records.

Browser focus loss, supported face results, camera connection, and disconnection can create EvidenceEvents. SERPS stores operational metadata, not raw video.

## Reviewer / Proctor

1. Sign in with a Reviewer/Proctor account and open `/reviewer`.
2. Filter by risk, unresolved status, and active/completed state.
3. Open a session. Inspect privacy-safe facial enrolment status, authentication outcome, identity confidence, liveness result, both camera status panels, risk assessment, evidence, policy, decisions, and reports. Raw biometric representations are never exposed.
4. Select one supported action: Continue, Request Reauthentication, Acknowledge, Escalate, or Request More Evidence.
5. Enter a substantive rationale, review the confirmation, and submit once.
6. Confirm the persisted message and refreshed timeline. Generate a structured report when required.

Reviewer decisions are append-only operational records. They are not automated misconduct declarations.

## Administrator

1. Sign in with an Administrator account and open `/admin`.
2. Review institution-scoped registration status, pending approvals/enrolments, candidate/session totals, risk counts, camera connections/failures, active policy, and audit activity.
3. Open a session to inspect its read-only dual-camera, governance, reviewer, timeline, and report state.
4. Use reviewer credentials for reviewer decisions; the administrator oversight view deliberately has no decision action.

## Session and error messages

- **Authentication required/session expired:** sign in again.
- **Forbidden:** the account lacks the required server-side role.
- **Dual-camera readiness unavailable:** connect a second distinct camera and retry discovery.
- **Permission denied/disconnected:** restore browser/OS permission or reconnect the device; no successful status is fabricated.
- **Local face detector unavailable:** confirm WebAssembly support and that `/mediapipe/wasm` and `/mediapipe/models/face_landmarker.task` are served by the frontend. No face result is claimed when initialisation fails.
- **API unavailable:** confirm API health and the configured public base URL, then retry.

## Registration approval and demonstration accounts

Reviewer and administrator requests remain `pending approval` until a System Administrator records an approval or rejection rationale. Candidates use bounded prototype verification and must enrol before activation. The four seeded dissertation identities are explicitly marked **Demonstration Account** and bypass registration, enrolment, and facial authentication only to preserve the defence workflow. This bypass must not be enabled for normal accounts or represented as a production control.

See `troubleshooting.md` for operator diagnostics and `prototype_limitations.md` for research boundaries.
