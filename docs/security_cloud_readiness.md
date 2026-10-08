# Security and Cloud Deployment Readiness Report

Baseline: `97322281c63929f21c96c3aa66ebdb06a4f8b730`. Validation work is isolated; no public deployment is authorized/performed. Final results are recorded below after validation.

## Audit investigation

The historical audit count was 15 (4 moderate, 10 high, 1 critical). The pre-remediation refreshed registry audit reported 16 package entries (4 moderate, 11 high, 1 critical), including a source-map-js advisory. These are aggregated dependency findings, not 16 independent exploitable application flaws. Six appear with `--omit=dev`; the others are tooling. Reachability below is source/configuration analysis, not penetration-test proof.

### @next/eslint-plugin-next

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next -> @next/eslint-plugin-next.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - Inherited from `fast-glob`.

### @vitest/mocker

- Severity: moderate; development/tooling tree.
- Path (baseline lock): web -> vitest -> @vitest/mocker.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - [Vitest: Path Traversal / Arbitrary File Read via @vitest/mocker Redirect Mock](https://github.com/advisories/GHSA-82fw-gwwq-j7x9); affected >=2.1.0 <4.1.11

### baseline-browser-mapping

- Severity: moderate; production dependency tree.
- Path (baseline lock): web -> next -> baseline-browser-mapping.
- Reachability: Invalid mapping query can terminate process; no user-controlled query route found. Used by framework/build target selection.
- Advisory/propagation:
  - [baseline-browser-mapping process termination on invalid input causes denial of service](https://github.com/advisories/GHSA-w5vr-8v7q-w6rv); affected >=2.0.0 <2.11.0

### brace-expansion

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint -> minimatch -> brace-expansion.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - [brace-expansion: Quadratic-time expansion of the `{a},b}` rewrite causes CPU denial of service](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr); affected <1.1.21
  - [brace-expansion: Quadratic-time expansion of the `{a},b}` rewrite causes CPU denial of service](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr); affected >=4.0.0 <5.0.12
  - [brace-expansion: DoS via uncontrolled recursion on nested brace groups causing stack exhaustion](https://github.com/advisories/GHSA-qhr7-859c-m2p7); affected <1.1.20
  - [brace-expansion: DoS via uncontrolled recursion on nested brace groups causing stack exhaustion](https://github.com/advisories/GHSA-qhr7-859c-m2p7); affected >=4.0.0 <5.0.11
  - [brace-expansion: DoS via uncontrolled recursion in parseCommaParts causing stack exhaustion](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p); affected <1.1.19
  - [brace-expansion: DoS via uncontrolled recursion in parseCommaParts causing stack exhaustion](https://github.com/advisories/GHSA-6j4f-fj2g-mc7p); affected >=4.0.0 <5.0.10

### braces

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next -> @next/eslint-plugin-next -> fast-glob -> micromatch -> braces.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - [braces vulnerable to stack-exhaustion denial of service through deeply nested patterns](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm); affected <=3.0.3

### browserslist

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next -> eslint-plugin-react-hooks -> @babel/core -> @babel/helper-compilation-targets -> browserslist.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - [Browserslist: Unbounded memory growth (no cache eviction) via distinct query results, leading to eventual OOM](https://github.com/advisories/GHSA-c83g-rgw3-j3cx); affected <=4.28.6
  - [Browserslist: Uncaught crash / prototype write via untrusted browserslist-stats.json custom stats (normalizeStats)](https://github.com/advisories/GHSA-73wf-gq98-2v4g); affected <=4.28.6

### eslint-config-next

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - Inherited from `@next/eslint-plugin-next`.

### fast-glob

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next -> @next/eslint-plugin-next -> fast-glob.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - Inherited from `micromatch`.

### js-yaml

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint -> @eslint/eslintrc -> js-yaml.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - [JS-YAML: Quadratic CPU consumption in !!omap resolution (3.x and 4.x) — CVE-2026-59870 fix not backported](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj); affected >=4.0.0 <4.3.1
  - [js-yaml: maxTotalMergeKeys does not limit CPU use for empty merge sources](https://github.com/advisories/GHSA-2883-xcg3-v3hh); affected >=4.0.0 <4.3.2

### micromatch

- Severity: high; development/tooling tree.
- Path (baseline lock): web -> eslint-config-next -> @next/eslint-plugin-next -> fast-glob -> micromatch.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - Inherited from `braces`.

### nanoid

- Severity: high; production dependency tree.
- Path (baseline lock): web -> postcss -> nanoid.
- Reachability: Advisory targets custom generators with size zero; no application custom generator/input path found. Transitive PostCSS helper, not SERPS identity/token generation.
- Advisory/propagation:
  - [nanoid: custom generators can loop indefinitely when size is zero](https://github.com/advisories/GHSA-2v37-7h3g-55p8); affected <3.3.18

### next

- Severity: critical; production dependency tree.
- Path (baseline lock): web -> next.
- Reachability: Windows-hosted RCE applies to the unpatched Windows server if reachable; Linux cloud/container avoids that OS prerequisite. AVIF image optimization and next/og have separate critical advisories. No next/og/ImageResponse routes or next/image imports found, nor untrusted image upload/remotePatterns configuration. Static analysis narrows exposure but does not prove optimizer endpoint safety. Patch before staging; native runtime is deliberately not restarted.
- Advisory/propagation:
  - [Next.js: Unauthenticated Remote Code Execution on windows-hosted servers](https://github.com/advisories/GHSA-p293-qw3h-jr36); affected >=16.0.0 <16.3.3
  - [Next.js: Unauthenticated Remote Code Execution in Image Optimization API when AVIF files are used](https://github.com/advisories/GHSA-2xp9-vwfh-vxw4); affected >=16.0.0 <16.3.3
  - [Next.js: Remote Code Execution in next/og ImageResponse](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j); affected >=16.2.0 <16.3.6
  - Inherited from `postcss`.
  - Inherited from `sharp`.

### postcss

- Severity: moderate; production dependency tree.
- Path (baseline lock): web -> postcss.
- Reachability: Untrusted CSS/sourceMappingURL prerequisite; SERPS uses committed CSS during build, with no user CSS processing endpoint found. Build supply-chain exposure remains relevant.
- Advisory/propagation:
  - [PostCSS: incomplete fix of GHSA-6g55-p6wh-862q — attacker-controlled sourceMappingURL reads arbitrary .map files when `from` is unset](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp); affected <=8.5.22

### sharp

- Severity: high; production dependency tree.
- Path (baseline lock): web -> next -> sharp.
- Reachability: Conditional server image-processing exposure through Next image optimization; no direct app invocation or user-supplied AVIF source found. Upgrade through supported Next dependency, not a forced incompatible sharp override.
- Advisory/propagation:
  - [sharp inherited vulnerabilities in libvips: CVE-2026-33327, CVE-2026-33328, CVE-2026-35590, CVE-2026-35591](https://github.com/advisories/GHSA-f88m-g3jw-g9cj); affected <0.35.0
  - [sharp: Vulnerabilities in libheif: GHSA-g89c-p67h-r497 and GHSA-2jg2-4ch7-h545](https://github.com/advisories/GHSA-rgj7-g3m4-5g8c); affected <0.35.4

### source-map-js

- Severity: high; production dependency tree.
- Path (baseline lock): web -> postcss -> source-map-js.
- Reachability: Malformed source-map section offsets required; maps are generated from repository build inputs, no submitted-source-map endpoint found. Build-time DoS risk for untrusted sources.
- Advisory/propagation:
  - [source-map-js allows event-loop denial of service through indexed source-map section offsets](https://github.com/advisories/GHSA-68fv-2mgg-jv7q); affected >=1.0.0 <1.2.2

### vitest

- Severity: moderate; development/tooling tree.
- Path (baseline lock): web -> vitest.
- Reachability: Lint/test tooling only; not an application import or production request handler. Malicious repository/config/test input or an exposed development server could exercise it. Production web runtime is pruned of development dependencies; do not expose dev/Vitest servers.
- Advisory/propagation:
  - Inherited from `@vitest/mocker`.
  - [Vitest: Path Traversal / Arbitrary File Read via @vitest/mocker Redirect Mock](https://github.com/advisories/GHSA-82fw-gwwq-j7x9); affected >=2.1.0 <4.1.11

## Remediation strategy

Use Next.js and matching ESLint config 16.3.8, PostCSS 8.5.29 and Vitest 4.1.11; retain existing direct major versions and pin previously floating `latest` entries. MediaPipe stays at the baseline version. Compatible transitive versions are resolved and locked. No `npm audit fix --force`, Next downgrade or Vitest 5 upgrade is used. npm 10 resolver attempts failed with `loadPeerSet/edgesOut`. npm 11.6.2 produced an incomplete lock rejected by clean installation. Fresh resolution with Node-compatible npm 11.21.0 completed normally, without force or legacy peer handling; prior locks remain preserved outside the checkout. Full clean-install/regression validation is required before accepting the replacement lock.

The enrolled-only assignment gate remains intact. The previous demo seeder created `demonstration_bypass`, which that gate correctly rejected. Shared bypass accounts are retired. The replacement is offline, explicit, empty-database-only staff provisioning with an audit entry and no candidates, assignments, examination sessions or biometric bypass. Repeat execution refuses without credential resets. An existing missing exception import in the rejected-login path is corrected and regression-tested.

## Deployment and rollback

See [the staging runbook](cloud_staging.md) for complete Vercel/Railway variable requirements, TLS/HTTPS/CORS, migration/startup settings, one-time bootstrap, controlled deployment, Render/Supabase portability, rollback and physical acceptance. Git-triggered Vercel deployment is disabled in configuration; CI has no cloud credentials or deployment job.

## Validation and decision

Backend validation completed: 16 focused tests and 116 full backend tests passed (preserved validated patch). Clean installation with npm 11.21.0, dependency-tree validation, TypeScript, ESLint, all 135 frontend tests across 19 files, webpack production build, and git diff whitespace checking passed. An initial test wrapper incorrectly supplied the build-only API URL to the default-URL test; removing that wrapper override yielded 135/135 passes without application changes. Disposable Docker validation passed; see the final decision and evidence below.

### Recovered-checkout validation checkpoint (8 October 2026)

The regenerated npm 11.21.0 lock audits with zero production findings and five high tooling findings: `braces`, `micromatch`, `fast-glob`, `@next/eslint-plugin-next`, and `eslint-config-next`. These are the lint dependency propagation chain; npm proposes a breaking Next ESLint configuration downgrade, which is not accepted. Treat untrusted lint inputs as a tooling risk and do not expose development servers. Clean installation and frontend checks passed. Disposable Docker integration passed under project `serps-security-41d80c40` on ports 34000/34080; the final decision below supersedes the earlier NO-GO checkpoint.

## Final local validation and staging decision (8 October 2026)

**GO for the next separately authorized, access-restricted staging deployment phase. No public deployment was performed or authorized here. NO-GO for production examinations or unrestricted public exposure until provider/security and physical acceptance below are complete.** This is local Docker readiness, not a claim that Vercel/Railway have been deployed or penetration-tested.

| Check | Result |
| --- | --- |
| Clean dependency resolution/install | npm 11.21.0, ordinary peer validation; passed. No force/legacy-peer-deps. |
| Production npm audit | 0 findings, previously 6. |
| Full npm audit | 5 high tooling findings remain, previously 16 total including 1 critical. |
| Dependency tree / TypeScript / ESLint | Passed. ESLint 9.39.5 also reports upstream end-of-support; a future supported-major migration needs separate compatibility validation. |
| Frontend regression | 135/135, 19 test files. |
| Production frontend build | Next 16.3.8 webpack build, TypeScript and 12 static pages passed. |
| Backend regressions | Preserved 16 focused / 116 full passing results; validated backend application patch unchanged after recovery. |
| Whitespace | git diff --check passed. |
| API Docker image | Built successfully; startup uses portable port/migration entry point. |
| Web Docker image | Built successfully, npm 11.21.0; production dependencies pruned, non-root runtime. |
| Disposable PostgreSQL | Fresh migration head and all model tables/columns verified. |
| Runtime | All three containers healthy; API readiness/liveness and frontend `/` and `/login` reachable. |
| Network/CORS | Allowed origin accepted, unapproved origin receives no CORS permission; container frontend reaches API. |
| Image content | Correct isolated public API URL compiled; local env files and ESLint/Vitest absent from checked runtime paths. |
| Bootstrap/authentication | Staff provisioning succeeds once; repeated provisioning refuses; administrator login and `/me` succeed; wrong password returns 401. |
| Governance boundaries | No candidates, exam sessions or demo-bypass profiles created; bootstrap audit exists. Enrolled-only assignment gate preserved. |
| Cleanup | Validation containers/network removed; synthetic volume/private validation material retained outside repository. Native/evaluation resources unchanged. |

Images: `serps-api:serps-security-41d80c40`, `serps-web:serps-security-41d80c40`; PostgreSQL `postgres:16-alpine`. Only loopback host ports 34080 (API) and 34000 (web) were exposed; database had no host port. Integration project: `serps-security-41d80c40`. Local evidence directory: `serps-cloud-check-h6yjuddi` (sanitized logs and results; private environment file must not be published).

The first API build succeeded but the Windows validation wrapper failed decoding UTF-8 with cp1252. The wrapper now explicitly decodes UTF-8. The successful API image was reused without application changes; its embedded validation helper predates that logging-only repair. A web attempt failed at Docker Hub token TLS handshake before any application stage; an unchanged retry succeeded. No TLS checks were disabled. Final source also includes documentation-only corrections after the build. Fresh CI uses the corrected helper and builds both images normally; `--reuse-api-image` is an explicit local recovery option only for verified matching application source.

Validated dependency versions: Next/config 16.3.8, PostCSS 8.5.29, Sharp 0.35.5, Nanoid 3.3.20, Source Map JS 1.2.2, Baseline Browser Mapping 2.11.27, Vitest 4.1.11; Vite 8.1.4 and MediaPipe 0.10.35 retained. Five remaining high entries are the braces 3.0.3 lint chain propagated through micromatch, fast-glob and Next ESLint packages, not five production endpoints. Do not run lint against untrusted repositories with credentials; CI has read-only repository permissions and no cloud secrets. No claim of zero overall security risk is made.

### Reproduction and deployment handoff

From a fresh checkout use `npx --yes --package=npm@11.21.0 npm ci`, then the documented TypeScript/lint/test/webpack build commands. Run `python scripts/deploy/validate_docker.py` with Docker available and ports 34000/34080 free; it creates unique isolated resources. The checked-in CI performs these checks but its remote run must still be reviewed after push; no remote CI success is claimed by local evidence.

Required provider variables, the complete staging sequence, TLS/CORS/secret controls, one-time bootstrap, migration ordering and rollback/restore procedure are in [cloud_staging.md](cloud_staging.md). Vercel must receive only the public HTTPS API origin; API database/JWT/bootstrap credentials remain provider secrets. Disable automatic deployments until separate staging authorization. Rollback must preserve schema compatibility; restore incompatible data into a new database, never overwrite native/evaluation data.

Remaining acceptance: actual provider HTTPS and DB certificate verification, restricted ingress/rate controls, backup restoration, persistence across provider restart, log redaction/retention, genuine candidate enrolment and assignment, authorization/tenant checks, and physical camera/background/minimise/sleep-resume/re-authentication/human-review flows. Local synthetic bootstrap tests do not prove biometric or real-examination acceptance. Do not use Trial 17 or frozen evaluation artifacts. Python/base-image supply-chain review and ongoing advisory monitoring remain operational responsibilities; this phase's dependency audit covers npm, not a comprehensive penetration test.

### Exact changed files

- `.dockerignore`
- `.env.example`
- `.github/workflows/ci.yml`
- `README.md`
- `apps/api/app/api/v1/routes/auth.py`
- `apps/api/app/api/v1/routes/health.py`
- `apps/web/next-env.d.ts`
- `apps/web/next.config.mjs`
- `apps/web/package.json`
- `apps/web/vercel.json`
- `docker/api.Dockerfile`
- `docker/web.Dockerfile`
- `docs/cloud_staging.md`
- `docs/docker_deployment.md`
- `docs/installation_guide.md`
- `docs/security_cloud_readiness.md`
- `package-lock.json`
- `package.json`
- `railway.json`
- `scripts/deploy/bootstrap.py`
- `scripts/deploy/start_api.py`
- `scripts/deploy/validate_docker.py`
- `scripts/dev/seed_demo_data.py`
- `src/serps_pop/config/settings.py`
- `src/serps_pop/operations/__init__.py`
- `src/serps_pop/operations/bootstrap.py`
- `tests/test_cloud_bootstrap.py`
