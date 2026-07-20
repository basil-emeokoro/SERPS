# SERPS RC1 User Manual

## Purpose

SERPS is an explainable monitoring and governance layer for assessment-system integration. RC1 includes a bounded examination workspace for demonstration; it is not a full assessment platform or secure browser.

## Candidate

1. Open `/register`, enter the active institution code, candidate identifier, name, email, and password.
2. Sign in at `/login` with the institution code and candidate credentials.
3. Open the Candidate Portal and verify the assigned demonstration.
4. Read and accept monitoring consent, privacy notice, and institutional policy. Each submission creates a new record; earlier consent is not edited.
5. Select **Discover cameras and check device**. Permit required browser camera/microphone access.
6. Choose two different physical devices: primary is candidate-facing; secondary shows the room, desk, or side angle.
7. Preview each camera separately. If only one camera exists or permission fails, readiness remains incomplete and session start is blocked.
8. Start the demonstration only when the readiness summary passes.
9. In the workspace, answer sample questions, use Previous/Next, observe elapsed time and both local previews, and read the monitoring/FaceDetector status.
10. Select **Finish demonstration**, review the confirmation, and finish. SERPS stops local media tracks and preserves evidence/governance records.

Browser focus loss, supported face results, camera connection, and disconnection can create EvidenceEvents. SERPS stores operational metadata, not raw video.

## Reviewer / Proctor

1. Sign in with a Reviewer/Proctor account and open `/reviewer`.
2. Filter by risk, unresolved status, and active/completed state.
3. Open a session. Inspect candidate/examination details, both camera status panels, last-seen values, risk assessment, contributing evidence, recommendation, policy outcome, timeline, prior decisions, and reports.
4. Select one supported action: Continue, Request Reauthentication, Acknowledge, Escalate, or Request More Evidence.
5. Enter a substantive rationale, review the confirmation, and submit once.
6. Confirm the persisted message and refreshed timeline. Generate a structured report when required.

Reviewer decisions are append-only operational records. They are not automated misconduct declarations.

## Administrator

1. Sign in with an Administrator account and open `/admin`.
2. Review institution-scoped candidate/session totals, risk counts, unresolved cases, camera connections/failures, active policy, and audit activity.
3. Open a session to inspect its read-only dual-camera, governance, reviewer, timeline, and report state.
4. Use reviewer credentials for reviewer decisions; the administrator oversight view deliberately has no decision action.

## Session and error messages

- **Authentication required/session expired:** sign in again.
- **Forbidden:** the account lacks the required server-side role.
- **Dual-camera readiness unavailable:** connect a second distinct camera and retry discovery.
- **Permission denied/disconnected:** restore browser/OS permission or reconnect the device; no successful status is fabricated.
- **FaceDetector unavailable:** camera and focus monitoring continue; no face result is claimed.
- **API unavailable:** confirm API health and the configured public base URL, then retry.

See `troubleshooting.md` for operator diagnostics and `prototype_limitations.md` for research boundaries.
