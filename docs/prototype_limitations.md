# SERPS RC1 Prototype Limitations

## Scope statement

SERPS RC1 is a dissertation research prototype. It demonstrates a coherent, explainable, human-governed monitoring workflow and is not certified for live institutional examinations.

## Examination and secure-browser boundary

The included workspace is a demonstration examination harness with three static sample questions, navigation, a timer, and explicit completion. It has no question-bank administration, scoring, autosave guarantees, result processing, operating-system lockdown, process blocking, clipboard enforcement, network control, or equivalence to Safe Exam Browser.

## Camera and media boundary

The candidate browser can enumerate and preview two distinct local video-input devices. RC1 persists camera-role metadata and EvidenceEvents, not raw video. Reviewer and administrator panels are metadata/status views; they do not receive production remote video. There is no enterprise WebRTC infrastructure, TURN service, adaptive bitrate, distributed second-device pairing, media recording, or retention pipeline.

## Browser capability differences

`getUserMedia`, device labels, track events, and device-change behavior differ by browser, operating system, permissions, and secure-context policy. SERPS bundles MediaPipe Tasks Vision and its model locally, but WebAssembly, camera permission, and suitable browser support remain required. When the detector cannot initialise, SERPS states that limitation and does not create a fabricated face result. A two-camera demonstration requires hardware and a browser that exposes both devices.

## Validation environment

The automated identity lifecycle and complete workflow use SQLite and real API contracts with deterministic descriptor fixtures. Docker PostgreSQL is healthy, but the application remains configured for SQLite because the existing PostgreSQL volume credentials do not match the local application configuration. Physical two-camera and human movement validation remains a manual demonstration step and must not be inferred from deterministic tests.

## Identity and biometric boundary

The candidate lifecycle includes automatic prototype email verification, a one-time enrolment challenge, six ordered face observations, randomized movement prompts, a stored derived numeric representation, password-then-face sign-in, recent-identity session gating, periodic identity prompts, registration approval, and privacy-safe reviewer status. The implementation uses locally bundled MediaPipe face landmarks and bounded geometric movement proxies. Its 8-by-8 luminance descriptor is an experimental similarity representation, not a biometric-grade face embedding. The system is not production facial recognition, certified liveness detection, blink analysis, depth sensing, presentation-attack resistance, identity-registry verification, fairness validation, or a substitute for human identity proofing. Raw images/video are not stored, but the derived descriptor is sensitive and still requires production encryption and retention governance.

## Governance boundary

The CIE uses deterministic bounded rules, not a general-purpose autonomous adjudicator. Agent recommendations are advisory. IPIME applies workflow policy and explicitly avoids automatic examination termination. A human reviewer records the operational action; SERPS does not declare misconduct.

## Security and privacy boundary

JWT and RBAC controls are implemented, including short-lived access tokens and protected-request revalidation of active database user state. Browser tokens still use session storage rather than hardened cookies, and refresh-token revocation does not immediately revoke an already issued access token. Production needs TLS termination, security headers, rate limiting, key rotation, secret management, database encryption/backup, retention/deletion rules, incident response, monitoring, penetration testing, DPIA/ethics approval, and institutional access governance. The audited PostCSS findings were resolved with a compatible update; `npm audit` now reports zero vulnerabilities.

## Scale and performance boundary

RC1 has no production load-test evidence or service-level objective. Evidence governance is synchronous and may create multiple immutable records per event. Queue/metric queries may exhibit N+1 behavior as session volume grows. The single-machine demonstration assumption must not be extrapolated to institutional concurrency.

## Future institutional integration

Production integration requires stable assessment-platform APIs, SSO/identity federation, institutional policy configuration, remote-media design, operational monitoring, retention agreements, accessibility testing, support processes, PostgreSQL proof, disaster recovery, and controlled pilot evaluation.

These limitations are research findings and design boundaries, not hidden defects. They define the work needed to move from RC1 to a production pilot.
