# Docker deployment and isolated validation

This path is separate from the native SERPS evaluation runtime. Do not use its database, environment files, sessions, detector trials or evidence. Container startup is not physical camera/detector acceptance.

## Prerequisites and fresh clone

Install Git and Docker Engine/Docker Desktop with Linux containers and Compose v2. Docker Desktop must finish starting: both commands below must succeed, including a Server section from `docker version`. An installed CLI alone is insufficient. No host Python, Node.js, PostgreSQL, native `.env`, or `apps/web/.env.local.pre8765` is required by the images.

```powershell
docker version
docker compose version
git -c core.longpaths=true clone --branch codex/stabilize-mode-workflows-governance --single-branch https://github.com/basil-emeokoro/SERPS.git SERPS-docker
Set-Location SERPS-docker
git rev-parse HEAD
```

The clone option supports the repository's long documentation paths on Windows without modifying global Git settings. Record the commit hash being deployed; use a clean checkout of that commit for repeat validation. Base image tags and backend dependency ranges are not digest/version locked, so these instructions promise a repeatable deployment procedure, not bit-identical image bytes across future dependency releases.

## Isolated configuration (PowerShell)

The following creates fresh credentials outside the checkout and a new Compose project/volume. It uses frontend port 33000 and API port 33080, leaving native SERPS ports 3100/8765 alone. Check the two selected ports are free first; select different ports if needed. No PostgreSQL host port is published.

```powershell
$webPort = 33000
$apiPort = 33080
if (Get-NetTCPConnection -State Listen -LocalPort $webPort,$apiPort -ErrorAction SilentlyContinue) { throw 'Choose unused validation ports' }
$project = 'serps-check-' + (Get-Date -Format yyyyMMddHHmmss)
$envFile = Join-Path $env:LOCALAPPDATA ('SERPS\' + $project + '.env')
if (Test-Path -LiteralPath $envFile) { throw 'Do not overwrite an existing deployment environment' }
[IO.Directory]::CreateDirectory((Split-Path $envFile)) | Out-Null
$dbPassword = [guid]::NewGuid().ToString('N')
$jwtSecret = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
@"
SERPS_ENV=production
SERPS_POSTGRES_PASSWORD=$dbPassword
SERPS_DATABASE_URL=postgresql+psycopg://serps:${dbPassword}@db:5432/serps_pop
SERPS_JWT_SECRET=$jwtSecret
SERPS_BIND_ADDRESS=127.0.0.1
SERPS_WEB_PORT=$webPort
SERPS_API_PORT=$apiPort
SERPS_CORS_ORIGINS=http://localhost:$webPort,http://127.0.0.1:$webPort
NEXT_PUBLIC_API_BASE_URL=http://localhost:$apiPort
SERPS_IMAGE_TAG=$project
"@ | Set-Content -LiteralPath $envFile -Encoding ascii
Remove-Variable dbPassword,jwtSecret
```

Keep the environment file private and stable for any retained database volume. Never commit or print it. Shell environment variables take precedence over `--env-file`; run from a shell without conflicting SERPS/NEXT_PUBLIC overrides. Do not reuse native database URLs. `SERPS_DATABASE_URL` must reference Compose host `db`, database `serps_pop`, user `serps`, and the same password provided as `SERPS_POSTGRES_PASSWORD`. Generated hexadecimal credentials avoid URL-escaping issues; externally supplied credentials require appropriate URL encoding.

`NEXT_PUBLIC_API_BASE_URL` is a public **browser-reachable build argument**, not a secret or the container-internal URL `http://api:8000`. Changing it requires rebuilding the web image. Runtime environment variables cannot rewrite already compiled browser JavaScript. CORS origins must exactly match the browser frontend origin. Remote camera/microphone access requires HTTPS; localhost is suitable for this isolated check. Public deployment additionally needs an operator-managed HTTPS reverse proxy, domain, firewall and secret management. This guide does not configure those external services.

## Build, initialize and verify

```powershell
docker compose --env-file "$envFile" -p "$project" config --quiet
docker compose --env-file "$envFile" -p "$project" build
docker compose --env-file "$envFile" -p "$project" up -d --wait --wait-timeout 180
docker compose --env-file "$envFile" -p "$project" ps
(Invoke-WebRequest "http://localhost:$webPort" -UseBasicParsing).StatusCode
Invoke-RestMethod "http://localhost:$apiPort/api/v1/health"
docker compose --env-file "$envFile" -p "$project" exec -T api python -m alembic current
docker compose --env-file "$envFile" -p "$project" exec -T api python -m alembic heads
docker compose --env-file "$envFile" -p "$project" exec -T db psql -U serps -d serps_pop -c 'SELECT version_num FROM alembic_version;'
```

Use `config --quiet`, not a full rendered configuration dump, to avoid printing secrets. Expected services: `db` (`postgres:16-alpine`, internal 5432), `api` (`serps-api:$project`, internal 8000), `web` (`serps-web:$project`, internal 3000). Only loopback host ports selected above are published. The named volume is scoped by the Compose project; no host database or application-source bind mounts are used.

PostgreSQL becomes healthy before API startup. The API runs `alembic upgrade head` before Uvicorn and is checked at `/api/v1/health`; a migration failure prevents startup. The web service waits for API health and has its own HTTP health check. All three services must become healthy; the API must return `status: ok`, and the database revision must match the checked-out migration head. Verify the browser's network requests target the configured public API port (an API 401 without a login is an expected reachability response).

The historical demo-seeder incompatibility is corrected by retiring shared bypass accounts in favor of the audited, staff-only [bootstrap workflow](cloud_staging.md). The compatibility script delegates to bootstrap and refuses a nonempty database. Candidate enrolment and assignment gates remain unchanged. Seeding is not required for health/migration validation. Run it only against a newly created disposable deployment with privately injected `SERPS_BOOTSTRAP_*` variables; never point it at an existing research/evaluation database. Accounts and sessions are not copied from the native runtime. No demo control policy is enabled by these commands.

## Isolation and cleanup

`.dockerignore` allowlists image inputs and excludes environment files, the preserved backup, dependencies, `.next`, caches, databases, logs, Git metadata and dissertation/evaluation material. Both image contexts are the repository root; no files outside it are required. The frontend uses `npm ci` with the committed lockfile and builds inside Linux. Python dependencies and migrations are installed from committed source.

Stop only the selected validation project when finished:

```powershell
docker compose --env-file "$envFile" -p "$project" down
```

This preserves its database volume. Add `--volumes` only if you deliberately want to discard that disposable validation database. Never use global Docker cleanup/prune commands or a project name belonging to another deployment. Keep or securely remove the external environment file according to whether its volume is retained.

## Readiness evidence boundary

Report actual results per run: commit, Docker versions, image IDs/tags, project/service names, published ports, container health, HTTP results, migration revision and cleanup state. If the Docker engine cannot start, classification is **A: Docker-configured only**, regardless of native tests. Image build success alone is **B**; successful isolated stack startup is **C**; a fresh remote clone reproducing the documented deployment supports **D**. Physical camera, background/minimise, identity and governance acceptance remain separate.

## Historical isolated validation of baseline 9732228 (6 October 2026)

The results below describe the earlier Docker-only phase. See [the security/cloud report](security_cloud_readiness.md) for the current dependency and bootstrap validation.

Classification: **C ? Docker stack builds and runs successfully locally**. This is not an unrestricted production-readiness or physical acceptance claim. The application baseline was `d62da3d6380f2bb194f8e63b7c1a787d4a4f1bbf`, obtained from GitHub in an isolated checkout; only the deployment files in this change were added. Neither image relied on uncommitted native environment files. Successful images were not rebuilt merely to repeat validation. A fresh clone/replay of the final remote deployment commit was not performed, so classification D is not claimed.

Docker Engine 29.8.1 and Compose v5.5.1 were used. Project: `serps-readiness-d62da3d`. Configuration passed `config --quiet`; the API and web were built separately with `build api` and `build web`, and started with `up -d --no-build --wait --wait-timeout 180`. The earlier interrupted build failed during transfer (`context canceled`), before application compilation; the separate builds completed successfully.

| Service | Image | Published port | Result |
| --- | --- | --- | --- |
| api | `serps-api:readiness-d62da3d` | `127.0.0.1:33080` to 8000 | Healthy |
| web | `serps-web:readiness-d62da3d` | `127.0.0.1:33000` to 3000 | Healthy |
| db | `postgres:16-alpine` | None; internal 5432 | Healthy |

Image IDs recorded for this run:

- API: `sha256:9092d9bd8e02c1567c0bb5b81fcfc35a23f8e2562f09fc5673fd4cf56143ed4e`
- Web: `sha256:5a4b49a39653272fd78a0d26a9fd6212061cbd0bb535628e6795d9a7527a54e2`
- PostgreSQL: `sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea`
- Next.js build ID: `dtXVIFfGqYiVQ-FZTUlk8`

Validation results:

- `npm ci`, Next.js production compilation, build-time TypeScript checking and static-page generation passed inside Linux. Native application regression suites were not rerun for this packaging-only change.
- PostgreSQL initialized a new project-scoped volume. All migrations ran through `0009_exam_management_courses`; `alembic current` matched `alembic heads`. Schema inspection before seeding found all 29 application model tables and no missing model columns.
- Frontend `/` and `/login` returned HTTP 200; `/api/v1/health` returned `status: ok`. OpenAPI, configured-origin CORS, internal web-to-API DNS/HTTP, and the compiled browser URL `http://localhost:33080` passed.
- Read-only, non-interactive container checks found no local `.env` inputs, `.env.local.pre8765`, Git metadata or dissertation directory in the application image paths. The API/web containers had no bind mounts; only PostgreSQL used the new project volume.
- The stock demo seeder failed at its enrolled-only assignment gate. Its transaction did not persist users. This is an application/bootstrap blocker, not a Docker migration failure, and was left unchanged.
- Separate, explicitly synthetic non-biometric fixtures in the disposable database verified administrator/candidate login, authenticated identity retrieval, assignment creation and candidate assignment retrieval. These fixtures do not prove real biometric enrolment or physical acceptance and are not a production provisioning workaround. Examination-session count remained zero; no trial was executed.
- `npm ci` reported **15 audit findings: 4 moderate, 10 high, 1 critical**. No dependency updates or automatic audit fixes were applied. Production reachability and exploitability of those findings were not assessed; a separate dependency security review is required before public deployment.

The documented clone/configure/build/start procedure is available, but final-remote-commit replay and a working real account/bootstrap workflow remain unverified. HTTPS and physical camera/identity/governance acceptance remain separate requirements. Validation cleanup uses only this project's `down` command; its disposable volume and private external credentials are retained together, with no global pruning or changes to native services, existing projects or evaluation data.
