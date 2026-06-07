# Project Context For AI Agents

## Communication

- User-facing replies must be in Russian.
- Code, documentation, README, commit messages, filenames, variables, and GitHub repository structure must remain in English.

## Project Goal

Build a diploma project: a machine learning information system for football match prediction with a future mobile application.

## Current ML Scope

- Main ML task: match outcome prediction (`Home Win / Draw / Away Win`).
- BTTS prediction is implemented as a secondary finalized pipeline.
- Over2.5 prediction is implemented as a secondary finalized pipeline.
- Corners Over9.5 prediction is implemented as a secondary finalized pipeline.
- Yellow Cards Over3.5 prediction is implemented as a secondary finalized pipeline.
- Exact score prediction is implemented as a secondary finalized regression pipeline.
- A priority-based consistency and reconciliation layer is implemented as a final post-processing block.
- Final app model package metadata is prepared for future backend/API loading.
- Additional tasks such as other over/under targets, corners, and yellow cards are secondary and should not be expanded unless explicitly requested.
- Current data scope: top-5 European first divisions (`E0`, `D1`, `SP1`, `I1`, `F1`) for seasons 2018/19-2024/25.

## Target Threshold Context

- Threshold values were selected using class distribution analysis, not arbitrarily.
- Selected standard betting lines:
  - goals: `Over2.5`;
  - corners: `Over9.5`;
  - yellow cards: `Over3.5`.
- Red cards were analyzed separately and rejected as a main prediction task because of extreme class imbalance.

## Modeling Rules

- Use only time-based train/validation/test splits.
- Avoid leakage: do not use current-match results or post-match statistics as features.
- Main metric: Macro F1.
- Always track accuracy, balanced accuracy, and draw recall.
- For BTTS, balanced accuracy is important because positive-class F1 can be misleading when models collapse toward `BTTS Yes`.
- For Over2.5, balanced accuracy is important because positive-class F1 can be misleading when models collapse toward `Over2.5 Yes`.
- For Corners Over9.5, balanced accuracy is important because positive-class F1 can be misleading when models collapse toward `Corners Over9.5 Yes`.
- For Yellow Cards Over3.5, balanced accuracy is important because positive-class F1 can be misleading when models collapse toward `Yellow Cards Over3.5 Yes`.
- LogisticRegression remains the primary explainable baseline model across tasks.
- CatBoost and RandomForest are used as strong reference architectures.
- Compact LogisticRegression tuning is the standardized controlled optimization approach across tasks.
- Do not use Optuna, stacking, ensembles, or large feature engineering unless explicitly requested.

## Current Final Outcome Model

```text
features: v1_only
model: LogisticRegression
C: 0.05
class_weight: {"H": 1.0, "D": 1.6, "A": 1.0}
decision rule: default argmax
```

V2 features were tested but not selected as final. Threshold tuning was tested but not selected as final.

## Current Final BTTS Model

```text
features: v1_only
model: LogisticRegression
C: 1.0
class_weight: None
threshold: 0.50
```

BTTS-related rolling features were tested but not selected as final. BTTS threshold tuning and custom class weights were tested but not selected as final.

## Current Final Over2.5 Model

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

Over2.5-related rolling features were tested but not selected as final. LogisticRegression tuning improved metrics slightly but remained weaker than CatBoost. Threshold tuning did not improve over the default threshold.

## Current Final Corners Over9.5 Model

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

Corners-related rolling features were tested but not selected as final. LogisticRegression tuning improved the LogisticRegression baseline but remained weaker than CatBoost. Threshold tuning was tested but not selected over the default threshold.

## Current Final Yellow Cards Over3.5 Model

```text
features: v1_yellow_related
model: LogisticRegression
C: 0.05
class_weight: balanced
threshold: 0.50
```

Yellow-related rolling features improved results and were selected for the final configuration. Threshold tuning was tested but not selected over the default threshold. RandomForest and CatBoost remain reference architectures for this task.

## Final Consistency And Reconciliation Layer

The consistency layer is a rule-based post-processing block. It must not retrain models or change final ML configurations.

Final priority order:

1. Outcome prediction.
2. BTTS prediction.
3. Over2.5 prediction.
4. Exact score prediction.

Post-processing logic:

- Outcome is the highest-priority anchor and is not changed.
- BTTS is second priority and is not changed when a valid score can satisfy `Outcome + BTTS`.
- Over2.5 is third priority and is corrected only when it conflicts with `Outcome + BTTS`.
- Exact score is the lowest-priority detail layer and is corrected to the nearest score that satisfies final `Outcome + BTTS + Over2.5`.

Current design decision: exact score must not drive the final system because it is the noisiest prediction task. It is used as a detailed display layer after reconciliation, not as the main consistency anchor.

## Final App Model Package

- Local final model files are prepared under `models/final_app/`.
- The package can be rebuilt without retraining by running `python src/deployment/prepare_final_app_models.py`.
- `models/` remains ignored by Git, so model binaries must not be committed.
- Tracked metadata:
  - `docs/final_app_models.md`;
  - `configs/final_app_models.json`.
- Future backend/API code should load models from `models/final_app/`.
- Final user-facing predictions must pass through the priority-based reconciliation layer.

## Backend API Skeleton

- Initial FastAPI backend code lives under `src/api/`.
- Current endpoints: `GET /`, `GET /health`, `GET /db/health`, `GET /models`, `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /users/me/history`, `GET /users/me/history/unread-count`, `POST /users/me/history/mark-viewed`, `GET /matches`, `GET /matches/{match_id}`, `GET /matches/upcoming`, `GET /matches/recent`, `GET /matches/recent/sampled`, `GET /matches/showcase`, `POST /predict`, `POST /predict/{match_id}`, `GET /predictions/{prediction_id}`.
- `GET /` is a production landing page rendered with FastAPI `HTMLResponse`; unknown routes must continue to return 404.
- Run locally with `uvicorn src.api.main:app --reload`.
- Run for Android emulator/tablet testing with `uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`.
- Docker deployment preparation is available through `Dockerfile` and `docker-compose.yml`; run both PostgreSQL and FastAPI with `docker compose up -d --build`.
- The backend Docker service starts with `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` and connects to PostgreSQL through the Docker network using the `postgres` hostname.
- Production is served at `https://prediction-football.ru/` through Nginx reverse proxy and Let's Encrypt certificates. Public HTTP traffic on port 80 redirects to HTTPS on port 443, and Nginx proxies requests to the Dockerized backend on `http://127.0.0.1:8000`.
- VPS deployment notes are tracked in `docs/vps_deployment.md`. The intended deployment flow is `git pull` followed by `docker compose up -d --build` from `/root/Prediction_Football`.
- Before changing the VPS deployment directory, back up `.env`, `models/final_app/`, `data/raw/`, `data/interim/`, and optional `backups/` or `reports/` artifacts.
- The backend must load tracked metadata from `configs/final_app_models.json` and local model binaries from `models/final_app/`.
- Match-based prediction uses SQL database-backed runtime feature generation; do not retrain models or change final ML configurations from the API layer.
- PostgreSQL 16 through Docker Compose is the primary production-like backend database mode.
- SQLite remains a legacy/local fallback when `DATABASE_URL` is not set.
- Backend/auth Python dependencies are tracked in `requirements.txt`.
- User credential validation rules are: username must contain only Latin letters, digits, `_`, and `-`; email must be ASCII email format; password must be at least 8 printable ASCII characters with at least one Latin letter and one digit.
- API-FOOTBALL / API-SPORTS is the selected single external sports data source for future fixtures, match results, match statistics, and odds.
- API-FOOTBALL credentials must be stored only in local `.env` as `API_FOOTBALL_API_KEY`; `.env.example` must contain only an empty template value.
- API-FOOTBALL fixtures sync is implemented as a manual CLI script in `src/api/database/sync_api_football.py`.
- Fixtures sync stores only scheduled, postponed, and cancelled API fixtures. Finished fixtures are skipped until result/statistics sync is implemented.
- Team matching uses exact `(country, team name)` lookup plus in-code aliases for known API-FOOTBALL naming differences. New teams and leagues must not be created automatically by fixtures sync because duplicates would break runtime ML feature history.
- API-FOOTBALL odds sync is implemented as a manual CLI script in `src/api/database/sync_api_football_odds.py`.
- Odds sync writes only complete 1X2 and Over/Under 2.5 odds sets to the existing `odds` table under `Market Average`, averages complete bookmaker sets, never writes fake values, and must not create new bookmaker rows from API payloads.
- API-FOOTBALL results/statistics sync is implemented as a manual CLI script in `src/api/database/sync_api_football_results.py`.
- Results/statistics sync writes `match_results` only when score, total corner kicks, and total yellow cards are all available. It must not write fake zeros for missing statistics.
- Daily API-FOOTBALL sync is registered inside the FastAPI backend through APScheduler in `src/api/services/scheduler_service.py`.
- Scheduler defaults are configurable through `.env`: fixtures at `03:00` for `today -> today + 14 days`, odds at `06:00` for `today -> today + 7 days`, and results/statistics at `23:30` for `today - 2 days -> today`.
- Scheduler windows are intentionally small to reduce API usage and respect free-tier limits. `API_FOOTBALL_MAX_SYNC_FIXTURES` defaults to `25`, so worst-case daily usage is about 80 requests.
- `API_FOOTBALL_SEASON=2026` is the target app season, but API-FOOTBALL free plans may not expose that season yet; use an available season for local API checks if needed.
- Scheduler health is exposed through `GET /scheduler/health`; existing `/health` and `/db/health` schemas must remain unchanged.
- Unknown FastAPI routes use browser-aware error handling: browsers receive a Russian HTML 404 page, while API clients continue to receive JSON `{"detail":"Not Found"}` responses. SQLAdmin-specific unknown routes are left to SQLAdmin/Starlette.
- SQLAdmin administration panel is mounted at `/admin` through `src/api/admin/`. It uses separate session-based admin authentication and must not change or replace the Android JWT auth flow.
- Admin panel access is restricted to users with the `admin` role. Public registration must continue to create regular users only; the first admin is created by promoting an existing trusted user through a controlled database/admin process.
- SQLAdmin Users view must never display `password_hash`. Users may be viewed, searched, filtered, and have only their role edited.
- User deletion is not allowed in SQLAdmin.
- SQLAdmin must not allow dangerous CRUD for predictions, user query history, matches, football domain data, model metadata, metrics, odds, or reference tables unless explicitly requested and carefully reviewed.
- SQLAdmin must not allow an admin to demote their own role or remove the last remaining admin user.
- Admin-triggered sync, sync logs, and monthly retraining automation are future work.

## Database Layer

- Backend database code lives under `src/api/database/`.
- Primary local database mode is PostgreSQL 16 through Docker Compose.
- `.env.example` is the tracked environment template; `.env` is local, ignored by Git, and must not be committed.
- Start PostgreSQL with `docker compose up -d postgres`.
- Start the production-like local stack with `docker compose up -d --build`.
- SQLite fallback database path is `data/app/football.db`.
- SQLite database files are ignored by Git and must not be committed.
- `data/raw/` is the canonical source location for `Matches.csv` and `EloRatings.csv`.
- `data/interim/` stores cleaned and feature-engineered intermediate CSV files.
- `data/processed/` is reserved for processed export artifacts.
- `data/app/` stores the local SQLite fallback application database.
- Create tables with `python src/api/database/init_db.py`.
- Seed minimal dictionaries with `python src/api/database/seed_db.py`.
- Seed final deployed model metadata and metrics with `python src/api/database/seed_final_models.py`.
- Load cleaned domain football data with `python src/api/database/load_football_data.py`.
- Load ELO history with `python src/api/database/load_elo_ratings.py`.
- Seed demo upcoming matches with `python src/api/database/seed_demo_upcoming_matches.py`.
- Create PostgreSQL backups with `python src/api/database/backup_postgres.py`; backups are stored under ignored local `backups/` using the `football_backup_YYYYMMDD_HHMMSS.sql` naming template.
- Preview restore with `python src/api/database/restore_postgres.py backups/<file>.sql`; actual restore requires `--execute`.
- Backup and restore use `pg_dump`/`psql`; when host PostgreSQL client tools are unavailable, scripts use the Docker Compose `postgres` service.
- In PostgreSQL mode, `GET /db/health` must report `database=postgresql`.
- The loader source is `data/interim/matches_top5_2018_2025_clean.csv`, not the feature matrix CSV files.
- The ELO loader primary source is `data/raw/EloRatings.csv`; root CSV fallback is local compatibility only.
- The loader fills countries, leagues, seasons, teams, matches, match results, bookmakers, and odds. Odds rows include 1X2 odds plus Over/Under 2.5 goal-total odds for runtime feature parity.
- Match rows reference `match_sources`: CSV-loaded rows use `historical`, development demo upcoming rows use `demo`, and `api` is reserved for a future external loader.
- External API identity is represented by `external_sources` and nullable `matches.external_source_id`, `matches.external_match_id`, and `matches.last_synced_at` fields so API-loaded matches can be upserted without duplicates.
- `external_match_id` is not globally unique by itself; the unique identity is `(external_source_id, external_match_id)`.
- The configured SQL database stores lightweight metadata for final deployed ML models in `models` and `model_metrics`.
- `POST /predict/{match_id}` stores rows in `predictions` and `prediction_characteristic_values`.
- Authenticated `POST /predict/{match_id}` also stores user action rows in `user_query_history`.
- `users.last_history_viewed_at` stores the latest viewed-history marker for unread prediction history. `GET /users/me/history/unread-count` counts distinct prediction IDs newer than this marker, and `POST /users/me/history/mark-viewed` advances it after the user opens history.
- Runtime prediction features for match-based prediction are generated by `src/api/services/feature_service.py` from SQL database history, not from training feature CSV files.
- Runtime feature generation must preserve feature names and ordering from `src/features/feature_registry.py` for `v1_only`, `v1_score_related`, and `v1_yellow_related`; implied 1X2 and Over/Under 2.5 probabilities are computed from stored odds.
- Current prediction reuse is model-aware: repeated `POST /predict/{match_id}` calls return the existing row for the same `match_id` and same deployed outcome `model_id`; a different future outcome `model_id` may create a new prediction.
- `src/api/database/clear_runtime_data.py` is a development-only cleanup script. It clears only `user_query_history`, `prediction_characteristic_values`, `predictions`, and `users`; it must not delete football domain data, model metadata, metrics, odds, ELO ratings, or schema objects. PostgreSQL cleanup uses `TRUNCATE ... RESTART IDENTITY`; SQLite cleanup deletes runtime rows and clears `sqlite_sequence` for runtime autoincrement tables.
- `src/api/database/seed_demo_upcoming_matches.py` is a development seed script. It creates scheduled demo matches with `source=demo`, `Market Average` odds, and no `match_results`.
- Users and query history are not loaded by the football data loader.
- `user_query_history` is an action log and may contain multiple rows for the same `prediction_id`; Android should display only the latest row per prediction.
- `src/analysis/prediction_quality_analysis.py` computes historical prediction-quality reports without writing predictions to the application database. `GET /matches/showcase` uses those reports to return honest historical examples with high prediction-hit counts; it must not replace aggregate model metrics or `/matches/recent/sampled`.

## Android MVP Layer

- Android tablet MVP code lives under `android_app/` as part of this monorepo.
- The Android app is a thin Kotlin + Jetpack Compose client over FastAPI.
- Android must not calculate ML features, access PostgreSQL, SQLite, or any backend database directly, run models locally, or implement reconciliation locally.
- Implemented Android screens: splash, login, registration, match list, match details, prediction result, profile, and prediction history.
- Android UI redesign is completed for the MVP: the app uses a dark football analytics theme with near-black backgrounds, dark cards, and lime accents for CTAs, statuses, prediction highlights, and progress bars.
- Android registration/login uses FastAPI auth endpoints and stores JWT access tokens in `SharedPreferences`.
- Login and Register use floating in-app notifications for form/auth errors and include show/hide password controls.
- Android adds `Authorization: Bearer <token>` through the Retrofit/OkHttp API layer and clears the token on `401`/`403`.
- Splash validates a stored token through `GET /auth/me`; valid tokens continue to the match list, missing or invalid tokens go to login.
- Profile shows the authenticated user in a dashboard-style card, links to prediction history, shows a smooth unread-history badge when `newPredictionsCount > 0`, and has a stable fallback card only for non-auth profile loading problems. Logout clears the token and returns to login through a known start destination with `launchSingleTop`.
- Prediction history is sorted by `query_date` descending and then deduplicated by `prediction_id` for display. History loads before first render to avoid visible row insertion, scrolls to the top on open, highlights new prediction rows by `prediction_id` for 5 seconds, calls `mark-viewed` after successful load, and resets the unread badge.
- Match list supports Recent, Upcoming, and Examples tabs plus client-side filters by league and season with an `All` option. It opens on Upcoming by default, caches loaded tab data in `MatchListViewModel`, refreshes stale cached tabs in the background after the client-side TTL expires, and shows the active tab's last successful update time.
- Upcoming actual matches and seeded demo matches are visually separated in Android; demo matches keep a compact `Демо` badge.
- Android UI maps technical backend values to Russian user-facing labels through display mapping helpers.
- Android displays backend match sources through user-facing labels: `historical` is hidden, `demo` is shown as a demo match, and `api` is shown as an API match.
- Android prediction results display outcome labels with full user-facing names, not short betting notation.
- Team names, league names, and country names should remain as returned by the backend.
- Backend `prediction.created_at` is stored as UTC; Android displays it in the local timezone of the emulator/tablet.
- The Android UI remains tablet-first, with basic phone support improved for the MVP.
- Login and Register preserve non-password input through `AuthViewModel`, keep password values local to the Compose screen, are vertically scrollable, and use keyboard-safe IME padding.
- Match Details uses a compact tablet layout; Prediction Result uses a dark analytics dashboard layout; History uses readable market cards with Russian statuses.
- Match Details, Prediction Result, and Profile are vertically scrollable where needed.
- Prediction Result uses one column on narrow screens and two columns on wider tablet screens.
- Match List tabs and filters are horizontally scrollable on narrow screens.
- Full `WindowSizeClass` handling, tablet master-detail navigation, and landscape-specific layouts are not implemented yet.
- Email verification, password reset, push notifications, team/league logos, standings, H2H, calendar, and news screens are not implemented.
- Android Emulator backend URL: `http://10.0.2.2:8000/`.
- Physical tablet backend URL: `http://<LAN_IP>:8000/`.
- Android debug builds use `BuildConfig.API_BASE_URL`; override it with `-PapiBaseUrl=http://<LAN_IP>:8000/` for a physical tablet or `-PapiBaseUrl=https://prediction-football.ru/` for the deployed VPS backend.

## Git Hygiene

- Large data and trained models must stay ignored by Git.
- Keep `data/` and root CSV files out of commits.
- Keep `models/` out of commits.
- Keep `football.db`, `*.db`, Python caches, Android `.gradle/`, `.kotlin/`, `build/`, APK/AAB files, and other runtime/build artifacts out of commits.
