# SERPS staging deployment and recovery runbook

No public deployment is authorized or performed by this change. Use a new staging environment with synthetic/consented test data only. Keep native SERPS, its environment backups, databases, sessions, Trial 17 and evaluation evidence separate. This is not approval for real examinations or a production security certification.

Dependency installation uses npm 11.21.0 (Node >=22.9 in the Node 22 line). Docker and CI pin this resolver; Vercel uses the pinned `npx` install command. For a clean local checkout run `npx --yes --package=npm@11.21.0 npm ci`. Do not use force or legacy peer resolution.

## Architecture and variables

Preferred: Vercel Next.js frontend; Railway API Docker service and separate persistent PostgreSQL service. A Render Docker API plus Supabase PostgreSQL can use the same API image and SQLAlchemy URL. No provider-specific database SDK or application storage is required. PostgreSQL holds users, token state, enrolment representations, audit and examination records: enable restricted access, encrypted storage/backups, retention controls and tested recovery. Do not place those records or raw media on the API's ephemeral filesystem. Local camera inference assets remain the committed assets; no detector changes are part of deployment.

| Service | Variable | Required value/handling |
| --- | --- | --- |
| Vercel | `NEXT_PUBLIC_API_BASE_URL` | Public HTTPS staging API origin, no credentials/query; compiled into browser bundles. Rebuild when it changes. |
| Vercel | Node.js | 22.x; Root Directory `apps/web`; enable access to files outside root for workspace packages. |
| Railway API | `SERPS_ENV` | `staging` (separate `production` environment later). |
| API | `SERPS_DATABASE_URL` | Secret SQLAlchemy `postgresql+psycopg://` URL, staging DB only; URL-encode credentials. Do not put on frontend. |
| API | `SERPS_JWT_SECRET` | Unique random secret of at least 32 characters, different in every environment, managed as a provider secret. |
| API | `SERPS_JWT_ISSUER`, `SERPS_JWT_AUDIENCE` | Explicit staging-specific issuer/audience, e.g. `serps-staging` / `serps-staging-api`. |
| API | `SERPS_CORS_ORIGINS` | Comma-separated exact HTTPS frontend origins, no wildcard, path or trailing slash. Do not allow arbitrary Vercel preview domains. |
| Railway API | `SERPS_RUN_MIGRATIONS` | `false`: Railway pre-deploy runs `python -m alembic upgrade head` once. Docker default remains `true`. |
| API | `PORT` | Assigned by platform; startup binds `0.0.0.0`. Docker defaults to 8000. |
| API | `SERPS_TRUSTED_PROXY_IPS` | Trusted ingress IPs only; default loopback. Use `*` only if direct ingress is blocked and all requests necessarily pass the trusted platform proxy. |
| API | `SERPS_DEMO_POLICY_CONTROLS` | `false`; hosted configuration rejects `true`. |
| API | `SERPS_ACCESS_TOKEN_MINUTES`, `SERPS_REFRESH_TOKEN_DAYS` | Defaults 10 / 7; review staging session policy. |
| API | `SERPS_BACKEND_BUILD_ID`, `SERPS_FRONTEND_BUILD_ID` | Record approved source revision/build identifier. |
| One-time bootstrap | `SERPS_BOOTSTRAP_CONFIRM` | `fresh-database`, remove after provisioning. |
| One-time bootstrap | `SERPS_BOOTSTRAP_INSTITUTION_CODE`, `SERPS_BOOTSTRAP_INSTITUTION_NAME`, `SERPS_BOOTSTRAP_EMAIL`, `SERPS_BOOTSTRAP_FULL_NAME`, `SERPS_BOOTSTRAP_PASSWORD` | Approved initial system administrator; unique password >=16 characters, privately injected, never CLI arguments/logs/Git. Remove after use. |

Do not copy native `.env`, `.env.local.pre8765`, or a development SQLite database. Browser `NEXT_PUBLIC_*` values are public: only the API origin belongs there. Do not run `env`, full `docker inspect`, full rendered Compose config, or verbose secret-bearing commands in CI logs. Startup disables Uvicorn access logs to avoid URL leakage; application/audit records stay in the restricted database. Configure provider error-log retention and access; do not log credentials, bearer tokens, facial vectors or submitted request bodies.

## Database TLS and migration controls

Use private networking where available. For a public database connection require certificate verification (`sslmode=verify-full`, provider CA via `sslrootcert` where required). Validate hostnames and certificate chain; do not silently fall back to plaintext. Railway/private-network TLS and CA availability must be confirmed for the provisioned service before approval. `sslmode=require` encrypts but does not by itself establish the intended server identity; document any private-network exception rather than treating it as equivalent. Supabase direct or session-pool connection is preferred for SQLAlchemy/migrations; do not assume transaction-pool prepared statements or IPv6 access work. Use provider-supplied correct host/port and verify connection limits. Local Compose's internal disposable DB is intentionally distinct from this hosted TLS policy.

One migration runner per deployment, no competing replicas; review migrations and take a recoverable backup first. Railway `railway.json` uses a blocking pre-deploy command and `/api/v1/ready` health check. `/health` is liveness; `/ready` checks DB reachability and migration heads, returning only generic failures. Render may use the same pre-deploy command where supported; otherwise run an approved one-off migration before starting with `SERPS_RUN_MIGRATIONS=false`. Never run migrations from Vercel or `create_all` as a substitute.

## Staging procedure (only after separate deployment approval)

1. Review CI, audit exceptions, source revision and this phase's report. Create dedicated provider staging projects and secrets; enable operator MFA and restricted staging access. No native or evaluation records may be imported.
2. Provision persistent PostgreSQL and backups; establish TLS verification and a tested restore target. Configure the API service with repository-root Docker context and `docker/api.Dockerfile`, `railway.json`, the exact approved commit and variables above. Disable automatic deploys in the provider dashboard until approved; configuration files alone are not authorization.
3. Run migrations once, confirm head and `/ready`; expose API only via HTTPS, disable direct insecure/public DB ingress. Put rate limiting and restricted access at trusted ingress for login, registration and facial endpoints before inviting testers. CORS is not authentication or abuse protection.
4. Privately run `python scripts/deploy/bootstrap.py` once using the bootstrap variables. It refuses an existing institution/user database, records `deployment.bootstrap`, and creates only a system administrator with staff `not_required` identity status and `demo_bypass=false`. A rerun must fail without resetting credentials. Remove bootstrap secrets after success. `scripts/dev/seed_demo_data.py` is now a compatibility entry point to this safe process; the old shared demo candidate seeder is retired.
5. Initial administrator signs in, configures the institution/registration schema, and provisions/approves staff through authorized workflows. Candidates use normal registration and facial enrolment. Only active, actually enrolled candidates may be assigned; no direct DB edits or invented biometric status are a provisioning step. Verify positive enrolment/assignment with consenting testers separately.
6. Configure Vercel root `apps/web`, Node 22, workspace access and staging-scoped `NEXT_PUBLIC_API_BASE_URL`. `apps/web/vercel.json` disables Git-triggered deployments by default. Deploy only the approved commit manually after authorization; use a stable staging domain and add only that exact origin to CORS. Preview branches must not share production secrets or databases.
7. Execute acceptance below. Record frontend/API build IDs, migration revision and operator approvals. Keep production separate and undeployed.

## Post-deployment acceptance

- HTTPS redirects/certificates; no mixed content; frontend `/` and `/login`, API `/health` and DB-backed `/ready` succeed. A failed DB/migration prevents readiness.
- Browser requests target the HTTPS staging API, including CORS preflight. An unapproved origin is not granted CORS. Private secrets do not appear in static bundles, logs or repository history for this change.
- Bootstrap once succeeds; repeat fails; audit exists; invalid password fails; role and tenant isolation are tested. Candidate registration, genuine facial enrolment, assignment and session continuation require explicit human acceptance; no demo bypass or policy changes.
- Foreground/background/minimise, camera recovery, sleep/resume, identity re-authentication and human-review flows are physical staging acceptance, not proven by CI. Never reuse Trial 17 or frozen detector evidence.
- Verify rate limits, staging access controls, DB TLS/certificate validation, persistent data across restart, backup restoration, log redaction/retention and alerts. Avoid destructive outage tests on a shared environment.

## Rollback and recovery

Record prior frontend/API image/source IDs, migration revision, provider settings and backup reference before promotion. Roll back frontend to its previous build together with the matching API origin; a changed public URL requires rebuilding. Roll back the API only if its schema compatibility with current DB has been reviewed. Do not automatically `alembic downgrade`, delete volumes or overwrite a live database. For incompatible schema, stop new writes, restore backup into a **new** isolated database, verify migration/schema and integrity, then switch the API secret URL after operator approval. Preserve the original for investigation. Rotate/revoke compromised credentials/tokens with a planned sign-in impact; restore never recreates a bootstrap bypass. Retest health, auth, tenancy and sessions before reopening staging.

## Provider references

- https://vercel.com/docs/monorepos
- https://vercel.com/docs/environment-variables/framework-environment-variables
- https://docs.railway.com/config-as-code/reference
- https://docs.railway.com/deployments/pre-deploy-command
- https://docs.railway.com/deployments/healthchecks

Portability is configuration-level; no Vercel, Railway, Render or Supabase deployment was executed in this phase.
