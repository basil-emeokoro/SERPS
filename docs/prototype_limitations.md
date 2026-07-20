# SERPS RC1 Prototype Limitations

## Scope statement

SERPS RC1 is a dissertation research prototype. It demonstrates a coherent, explainable, human-governed monitoring workflow and is not certified for live institutional examinations.

## Examination and secure-browser boundary

The included workspace is a demonstration examination harness with three static sample questions, navigation, a timer, and explicit completion. It has no question-bank administration, scoring, autosave guarantees, result processing, operating-system lockdown, process blocking, clipboard enforcement, network control, or equivalence to Safe Exam Browser.

## Camera and media boundary

The candidate browser can enumerate and preview two distinct local video-input devices. RC1 persists camera-role metadata and EvidenceEvents, not raw video. Reviewer and administrator panels are metadata/status views; they do not receive production remote video. There is no enterprise WebRTC infrastructure, TURN service, adaptive bitrate, distributed second-device pairing, media recording, or retention pipeline.

## Browser capability differences

`getUserMedia`, device labels, track events, and device-change behavior differ by browser, operating system, permissions, and secure-context policy. FaceDetector is not universally available. When absent, SERPS states that limitation and does not create a fabricated face result. A two-camera demonstration requires hardware and a browser that exposes both devices.

## Validation environment

The integrated workflow used SQLite and simulated browser/device attestations through the real API contracts. PostgreSQL was not verified because Docker Desktop did not expose a responsive engine. The prior browser walkthrough verified route guards and responsive rendering, but the current environment did not provide a complete hardware-backed two-camera browser run.

## Identity and biometric boundary

RC1 provides account authentication, candidate ownership, consent, device readiness, and bounded browser face-status events. It does not implement production facial enrolment, biometric templates, liveness certification, fairness evaluation, presentation-attack resistance, or an external identity provider.

## Governance boundary

The CIE uses deterministic bounded rules, not a general-purpose autonomous adjudicator. Agent recommendations are advisory. IPIME applies workflow policy and explicitly avoids automatic examination termination. A human reviewer records the operational action; SERPS does not declare misconduct.

## Security and privacy boundary

JWT and RBAC controls are implemented, including short-lived access tokens and protected-request revalidation of active database user state. Browser tokens still use session storage rather than hardened cookies, and refresh-token revocation does not immediately revoke an already issued access token. Production needs TLS termination, security headers, rate limiting, key rotation, secret management, database encryption/backup, retention/deletion rules, incident response, monitoring, penetration testing, DPIA/ethics approval, and institutional access governance. The audited PostCSS findings were resolved with a compatible update; `npm audit` now reports zero vulnerabilities.

## Scale and performance boundary

RC1 has no production load-test evidence or service-level objective. Evidence governance is synchronous and may create multiple immutable records per event. Queue/metric queries may exhibit N+1 behavior as session volume grows. The single-machine demonstration assumption must not be extrapolated to institutional concurrency.

## Future institutional integration

Production integration requires stable assessment-platform APIs, SSO/identity federation, institutional policy configuration, remote-media design, operational monitoring, retention agreements, accessibility testing, support processes, PostgreSQL proof, disaster recovery, and controlled pilot evaluation.

These limitations are research findings and design boundaries, not hidden defects. They define the work needed to move from RC1 to a production pilot.
