# SERPS RC1 Security Review

## Confirmed controls

- PBKDF2-HMAC-SHA256 passwords use per-password salts; generic login failures avoid account enumeration.
- Access JWTs validate HMAC signature, issuer, access-token type, and expiry. Opaque refresh tokens are stored as SHA-256 hashes and revoked on logout.
- API role dependencies enforce Candidate, Reviewer/Proctor, Administrator, and System Administrator authority.
- Candidate assignments, sessions, completion, and evidence enforce authenticated ownership.
- Reviewer and administrator access is institution-scoped; negative cross-institution tests pass.
- Reviewer decisions require a supported action and rationale; administrator oversight is read-only.
- Consent/readiness and governance models use ORM update/delete hooks to enforce append-only records.
- IPIME remains advisory and explicitly prohibits automatic examination termination.
- Raw video, authentication tokens, passwords, and biometric templates are not persisted in audit/report payloads.
- `.env` is ignored; Compose requires externally supplied database and JWT secrets.

## Needs improvement

- Browser tokens remain in session storage; production should adopt secure, HttpOnly, SameSite cookies with CSRF design.
- JWT roles/institution are claims for the short token lifetime; sensitive deployments should revalidate current assignments or use revocation/versioning.
- Add security headers, TLS policy, rate limiting, account lockout/monitoring, key rotation, and central secret management.
- Browser device/permission data is an operational attestation, not tamper-proof hardware evidence.
- Add PostgreSQL-backed tenancy/security tests, dependency scanning in CI, SAST/DAST, and penetration testing.
- Establish formal retention, subject-rights, encryption, backup, incident, DPIA, and ethics processes.

## Dependency audit

`npm audit --workspace apps/web --audit-level=moderate` reports two moderate findings through `postcss <8.5.10` and Next.js. The only registry-proposed automated fix forces a breaking downgrade to Next.js 9.3.3, so it was not applied. Track a compatible upstream upgrade and reassess before a production pilot.

## RC1 conclusion

No known critical security defect was found in the bounded research workflow. These controls support a controlled dissertation demonstration, not production certification. Full findings and future controls appear in `sprint3e_validation_report.md` and `prototype_limitations.md`.
