# VPS Deployment Notes

This document describes the current production deployment flow for the Prediction Football backend.

## Production Host

Production domain:

```text
https://prediction-football.ru/
```

VPS project path:

```text
/root/Prediction_Football
```

The backend runs in Docker Compose with PostgreSQL. Nginx is installed on the VPS and acts as the public reverse proxy:

```text
HTTPS :443 -> Nginx -> http://127.0.0.1:8000
HTTP  :80  -> HTTPS redirect
```

TLS certificates are managed by Let's Encrypt and Certbot with the Nginx plugin.

## Ignored Production Artifacts

These files and directories are required on the VPS but are intentionally not tracked by Git:

- `.env`
- `models/final_app/`
- `data/raw/EloRatings.csv`
- `data/raw/Matches.csv`
- `data/interim/matches_top5_2018_2025_clean.csv`
- `data/interim/matches_features_v1.csv`
- `data/interim/matches_features_v2.csv`
- optional PostgreSQL backups under `backups/`
- optional prediction-quality reports under `reports/`

Do not commit production secrets, model binaries, CSV datasets, database dumps, or local runtime databases.

## Standard Deploy

The VPS uses a read-only GitHub deploy key for repository access. Do not use GitHub passwords on the server and do not store GitHub personal access tokens in the project directory.

After the VPS is configured as a Git worktree with the deploy key, deploy manually with:

```bash
cd /root/Prediction_Football
git status
git pull
docker compose up -d --build
docker compose ps
```

Run production checks:

```bash
curl https://prediction-football.ru/
curl https://prediction-football.ru/health
curl https://prediction-football.ru/db/health
curl https://prediction-football.ru/models
curl https://prediction-football.ru/scheduler/health
```

SQLAdmin login:

```text
https://prediction-football.ru/admin/login
```

The SQLAdmin login page includes a passwordless defense demo mode when the production `.env` keeps:

```env
PREDICTION_FOOTBALL_ADMIN_DEMO_ENABLED=true
```

The demo session is read-only, uses the signed SQLAdmin session cookie, does not create a database user, and exposes only the main demonstration views. Disable it after the defense by setting:

```env
PREDICTION_FOOTBALL_ADMIN_DEMO_ENABLED=false
```

Then redeploy with:

```bash
cd /root/Prediction_Football
docker compose up -d --build
```

## Certificate Renewal

Check Certbot renewal with:

```bash
certbot renew --dry-run --no-random-sleep-on-renew
```

The production certificate is renewed by Certbot's system timer.

## Production UI And Error Handling

The root route `/` returns a small Russian HTML landing page for browser users. It provides labeled navigation links to:

- `/`
- `/health`
- `/docs`
- `/admin/login`

The QR code for defense/demo access is tracked at:

```text
docs/assets/qr_prediction_football.png
```

It opens:

```text
https://prediction-football.ru/
```

Unknown FastAPI routes use browser-aware 404 handling:

- browser requests with `Accept: text/html` receive a Russian HTML 404 page with links to `/`, `/docs`, and `/admin/login`;
- API clients continue to receive the JSON response `{"detail":"Not Found"}`.

SQLAdmin remains mounted at `/admin`. Unknown SQLAdmin routes are left to SQLAdmin/Starlette so the admin package is not customized beyond project-local templates and reverse proxy behavior.

Swagger UI remains available at `/docs`. The page includes a simple `← На главную` link for demo navigation, while endpoint names and technical schemas remain unchanged.

The SQLAdmin field audit is tracked at:

```text
docs/sqladmin_audit.md
```

## Status Policy

Dynamic backend status endpoints:

- `/health`
- `/db/health`
- `/scheduler/health`

Static production UI status:

- the landing page shows `Статус системы: работает`.

The static landing status is intentionally simple for the diploma deployment. The dynamic health endpoints remain the source of operational truth. Replacing the landing badge with live client-side health polling would add frontend logic without meaningful value before defense.

Android dynamic statuses:

- loading states for screens and requests;
- error states returned by ViewModels;
- prediction history statuses based on available factual results;
- match status labels mapped from backend values.

Android static statuses:

- short UI badges such as signed-in state and section labels.

These static Android labels should remain unchanged before defense because they are presentation labels, not operational health checks.
