# SERPS RC1 Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| API cannot connect to database | PostgreSQL stopped, wrong host/password, or URL not encoded | Start database; check `SERPS_DATABASE_URL`; use host `db` inside Compose and `localhost` natively; URL-encode special characters. |
| `docker compose config` reports a required variable | Secrets are intentionally not embedded | Set `SERPS_POSTGRES_PASSWORD`, `SERPS_DATABASE_URL`, and `SERPS_JWT_SECRET` in the launching shell. |
| Docker command hangs or cannot access engine | Docker Desktop/engine unavailable or permission blocked | Start Docker Desktop, select Linux containers, verify `docker info`, then retry. If still unavailable, document PostgreSQL as unverified. |
| Migration head differs | Incomplete checkout or migration failure | Run `python -m alembic heads/history`; RC1 expects one head, `0005_sprint3d_dual_camera`; inspect errors before changing data. |
| Seeder refuses to run | `SERPS_DEMO_PASSWORD` absent/short | Set an explicit password of at least 12 characters. |
| Seed login password appears wrong | Existing users were seeded with an earlier password | Use the original password or recreate the disposable demo database; the idempotent seeder does not silently reset users. |
| Candidate sees no assignment | Wrong institution/candidate or seed not applied | Confirm MIVA seed, candidate link, published examination, and eligible assignment. |
| Start remains disabled | Missing consent, device pass, distinct camera selection, or permission | Read readiness failures, complete each prerequisite, and retry; backend enforcement cannot be bypassed. |
| Only one camera appears | Browser/OS sees one video input | Connect a second physical camera, grant OS/browser access, reload, and rediscover. Do not treat one camera as dual-ready. |
| Camera labels are blank | Browser hides labels before permission | Grant permission once, stop the temporary stream, and enumerate again. |
| Camera disconnects | Track ended, device removed, permission revoked, or another app owns it | Close competing apps, reconnect, restore permission, and retry; inspect generated evidence. |
| FaceDetector says unavailable | Browser lacks the experimental API | Continue camera/focus monitoring; use a supported browser only if face demonstration is essential. Do not claim face detection occurred. |
| Reviewer queue is empty | No reviewer-required latest policy result, resolved case, or wrong institution/filter | Clear filters, generate an elevated-risk evidence pattern, and confirm reviewer institution. |
| Reviewer decision rejected | Missing rationale, unsupported action, mismatched chain IDs, or duplicate submission | Reload detail, choose a supported action, supply rationale, and submit once. |
| Administrator cannot submit a decision | Deliberate separation of duties | Use a Reviewer/Proctor or System Administrator account where authorised. |
| Browser shows session expired | Access token expired or invalidated | Sign in again; do not copy tokens into logs or documentation. |
| Frontend cannot reach API | Wrong `NEXT_PUBLIC_API_BASE_URL`, CORS, or API down | Confirm health endpoint, rebuild if public URL changed, and set exact CORS origin. |
| Pytest cache warning | Restricted workspace prevents `.pytest_cache` write | Test results remain valid; run in a writable checkout to remove the warning. |
| `npm audit` reports PostCSS | Current Next.js dependency path has two moderate findings | Do not use the breaking forced downgrade; monitor and upgrade safely when a compatible release resolves it. |

When escalating a defect, capture the commit hash, command, status code, minimal error message, role/institution, database engine, and reproduction steps. Exclude passwords, JWTs, refresh tokens, personal data, and raw media.
