# SERPS RC1 Security Review

## Confirmed controls

- PBKDF2-HMAC-SHA256 passwords use per-password salts; generic login failures avoid account enumeration.
- Access JWTs validate HS256 signature, issuer, audience, access-token type, expiry, issue time, subject, roles, and institution. Opaque refresh tokens are stored as SHA-256 hashes and revoked on logout.
- Protected requests reload the active database user and reject tokens whose role or institution claims no longer match trusted state.
- API role dependencies enforce Candidate, Reviewer/Proctor, Administrator, and System Administrator authority.
- Candidate assignments, sessions, completion, and evidence enforce authenticated ownership.
- Reviewer and administrator access is institution-scoped; negative cross-institution tests pass.
- Reviewer decisions require a supported action and rationale; administrator oversight is read-only.
- Identity audit, consent/readiness, and governance models use supported ORM update/delete guards to enforce application-level append-only records.
- IPIME remains advisory and explicitly prohibits automatic examination termination.
- Raw images and video are not transmitted or persisted by the biometric workflow. The backend stores a compact numeric luminance descriptor and its hash; reviewer and administrator responses expose only enrolment/authentication status, confidence, liveness result, and timestamps.
- Password and facial authentication are separate stages for normal candidates. One-time enrolment/authentication challenge tokens are generated with cryptographic randomness, stored only as SHA-256 hashes, expire after ten minutes, and cannot be reused after completion.
- Reviewer and administrator registration requests require a System Administrator approval decision and rationale before role assignment.
- `.env` is ignored; Compose requires externally supplied database and JWT secrets.

## Needs improvement

- Browser tokens remain in session storage; production should adopt secure, HttpOnly, SameSite cookies with CSRF design.
- Refresh-token revocation does not immediately invalidate an already issued access token; sensitive deployments should add access-token revocation/versioning or reduce the already short lifetime further.
- Add security headers, TLS policy, rate limiting, account lockout/monitoring, key rotation, and central secret management.
- Browser device/permission data is an operational attestation, not tamper-proof hardware evidence.
- Browser Face Detection and spatial pose proxies are not presentation-attack resistant, independently trusted, or certified liveness detection. Production requires a reviewed biometric algorithm, anti-spoofing, calibrated thresholds, fairness evaluation, encryption, revocation/re-enrolment, and subject-rights controls.
- The derived facial descriptor is sensitive biometric-adjacent data and is not application-layer encrypted in RC1. Production must use envelope encryption, strict retention/deletion controls, access monitoring, and a DPIA/ethics-approved lawful basis.
- Add PostgreSQL-backed tenancy/security tests, dependency scanning in CI, SAST/DAST, and penetration testing.
- Establish formal retention, subject-rights, encryption, backup, incident, DPIA, and ethics processes.

## Dependency audit

Sprint 3F applied a compatible PostCSS 8.5.18 override and direct development dependency. `npm audit` now reports zero vulnerabilities, and `npm ls postcss` confirms Next.js and Vite resolve to 8.5.18. Major ESLint 10 and TypeScript 7 upgrades remain deferred because they are unrelated breaking changes, not current audit findings.

## RC1 conclusion

No known critical security defect was found in the bounded research workflow. These controls support a controlled dissertation demonstration, not production certification. Full findings and future controls appear in `sprint3e_validation_report.md` and `prototype_limitations.md`.
