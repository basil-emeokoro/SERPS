# Restricted deployment alternatives

23 October 2026. Preparation only: no cloud service has been activated. Preserve Docker Compose. Never upload native SQLite, local environments, backups, biometric data or trial evidence.

## Provider configuration

Both Railway and Render can use repository-root Docker contexts with `docker/api.Dockerfile` and `docker/web.Dockerfile`, plus a separate managed PostgreSQL database. The existing API image starts migrations and port 8000 by default. For a provider-managed port, override startup with `sh -c 'exec uvicorn apps.api.app.main:app --host 0.0.0.0 --port "$PORT"'`; configure `alembic upgrade head` as a single pre-deploy step, not per replica. Confirm the selected provider plan supports that step. API health path: `/api/v1/health`. Independently verify database connectivity and `alembic current` versus `alembic heads`; HTTP health alone does not prove either.

Web startup override: `sh -c 'exec npm run start -w apps/web -- --hostname 0.0.0.0 --port "$PORT"'`. Health path: `/`. Set `NEXT_PUBLIC_API_BASE_URL` as the Docker build argument to the HTTPS browser-reachable API URL; rebuild on changes. Provider-private DNS cannot be used by the browser. Do not activate external domains in this phase.

API secret-store variables: `SERPS_ENV=staging`, `SERPS_DATABASE_URL` using `postgresql+psycopg://...`, unique high-entropy `SERPS_JWT_SECRET`, `SERPS_JWT_ISSUER`, `SERPS_JWT_AUDIENCE`, `SERPS_CORS_ORIGINS` (exact HTTPS frontend origin), `SERPS_ACCESS_TOKEN_MINUTES`, `SERPS_REFRESH_TOKEN_DAYS`. Leave `SERPS_DEMO_POLICY_CONTROLS=false`. Never put credentials in `NEXT_PUBLIC_*`, images, logs or Git. Percent-encode database credentials and require certificate-verified TLS (`sslmode=verify-full`, trusted CA/`sslrootcert`) across networks. Use provider-private networking where supported; do not disable TLS validation to fix connection problems.

Use separate staging/production secrets and databases. Add an identity-aware gateway or equivalent restricted access to both frontend and API before exposing routes; CORS and an obscure URL are not access controls. Verify preflight and browser API requests work through that gateway. Keep SERPS authentication, enrolment and institutional gates enabled.

## PostgreSQL and synthetic provisioning

Supabase PostgreSQL is optional and does not replace SERPS authentication. Prefer a direct connection for migrations and the long-lived API, or a session-mode pooler when IPv4 is needed. Validate SQLAlchemy/psycopg, certificate trust and connection limits using a disposable database. Transaction pooling/prepared statements require separate acceptance. Do not expose SERPS tables through a public client-side database interface or embed service-role keys in the frontend. Live PostgreSQL replay concurrency for this recovery remains unverified.

Use only synthetic staging accounts and normal consent/enrolment/readiness workflows. The stock demo seeder's demonstration-bypass/enrolled-only incompatibility remains a provisioning blocker on this branch. Do not weaken gates, manufacture production identity assurance or merge unrelated Phase 4 work to make it succeed. Never import native evaluation data.

## Release and rollback

Before restricted staging, close dependency-security and provisioning blockers, back up PostgreSQL and prove a restore into a new disposable database. Pin commit and image digest; migrate once, then test authentication/refresh, cross-institution and candidate denial, replay/governance atomicity, injected transaction failure, HTTPS/CORS and restricted access. Inspect logs for accidental secrets without publishing them. Container health is not camera/identity acceptance.

Rollback selects the previous compatible application images. Do not automatically downgrade migrations or overwrite newer data with an old backup. For incompatible schema changes, stop writes under a separately reviewed recovery plan and create a fresh backup first. This recovery introduces no schema migration. Persistent data belongs in PostgreSQL, not ephemeral container SQLite; no new raw-media storage is proposed.

Recommendation: Railway API/PostgreSQL is a suitable first restricted staging candidate; Render offers the same intended architecture. Supabase should remain optional until its connection mode is tested. **Public activation remains NO-GO** without separate approval, security/provisioning closure and physical acceptance. Historical npm audit findings are not remediated or re-audited by this runtime scope.

Provider references checked 23 October 2026: [Railway health](https://docs.railway.com/deployments/healthchecks), [Railway pre-deploy](https://docs.railway.com/deployments/pre-deploy-command), [Render deploys](https://render.com/docs/deploys), [Render health](https://render.com/docs/health-checks), [Supabase connections/TLS](https://supabase.com/docs/guides/database/connecting-to-postgres).
