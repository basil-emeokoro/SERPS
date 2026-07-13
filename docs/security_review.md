# SERPS POP Security Review Notes

## Sprint 2 Review

### Authentication and Token Handling

- Passwords are hashed with PBKDF2-HMAC-SHA256 and per-password salts.
- JWT access tokens are signed with an environment-controlled secret when `SERPS_JWT_SECRET` is set.
- Development runs without `SERPS_JWT_SECRET` generate a process-local development secret and should not be used as production identity configuration.
- Refresh tokens are generated as opaque random values and stored only as SHA-256 hashes.
- Login failures use generic messages and do not expose account existence.
- Logout revokes the stored refresh-token record.

### Audit Discipline

Implemented audit events include login success/failure, token refresh, logout, user creation, candidate creation/update, examination creation, assignment creation, session creation and session transition.

Audit records must not contain plaintext passwords, JWTs, refresh tokens or biometric data.

### NPM Audit

Command:

```powershell
npm.cmd audit --workspace apps/web --audit-level=moderate
```

Result:

- `postcss < 8.5.10` moderate advisory via `next`.
- NPM reports 2 moderate findings.
- The only available automated fix is `npm audit fix --force`, which would install `next@9.3.3` and is a breaking downgrade from the current Next.js scaffold.

Decision:

- Do not apply the forced downgrade during Sprint 2.
- Track the finding and upgrade Next.js/PostCSS safely when the upstream dependency path supports a non-breaking update.

### Repository Discipline

- No real personal credentials should be committed.
- `scripts/dev/seed_demo_data.py` uses `SERPS_DEMO_PASSWORD` or prints a generated one-time password for newly created users.
- Private dissertation and supervisor materials remain outside the POP repository.

### Remaining Security Hardening

- Replace local development token storage in the Next.js prototype with hardened cookie-backed session handling.
- Add production secret management documentation and deployment checks.
- Add CORS origin configuration through environment variables.
- Add security headers at the web/API deployment boundary.
- Add PostgreSQL-backed integration tests for migration and tenancy enforcement.
