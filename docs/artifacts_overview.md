# Artifacts Overview

This document gives a short engineering overview of the current project artifacts.

## Application Metadata

- `docs/final_app_models.md` describes the final local model package for future backend/API usage: final tasks, model types, feature sets, local model paths, thresholds, post-processing, and final test metrics.
- `configs/final_app_models.json` stores machine-readable backend metadata for final model paths, feature-set names, thresholds, reconciliation priority order, and exact-score clipping range.
- `src/api/` contains the FastAPI backend for the Android mobile application, including auth endpoints, match browsing, prediction, persisted prediction details, and user prediction history.
- `src/api/admin/` contains the SQLAdmin administration panel mounted at `/admin`, including session-based admin authentication, dashboard, model views, and localized template overrides.
- `src/api/database/` contains the SQLAlchemy physical database layer for backend persistence. PostgreSQL 16 through Docker Compose is the primary production-like mode; SQLite is retained as a local fallback when `DATABASE_URL` is not set.
- `Dockerfile` builds the FastAPI backend container and starts it with `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`.
- `.dockerignore` keeps local datasets, model binaries, backups, Android build inputs, and other runtime artifacts out of the backend image context.
- `docker-compose.yml` defines the production-like local stack with PostgreSQL 16 and the FastAPI backend service. The backend service connects to PostgreSQL through the internal Docker network using the `postgres` hostname.
- The deployed VPS backend is served at `https://prediction-football.ru/` through Nginx reverse proxy and Let's Encrypt TLS. Nginx redirects HTTP port 80 to HTTPS port 443 and proxies requests to the Dockerized backend on `http://127.0.0.1:8000`.
- `docs/vps_deployment.md` documents the production deployment flow, ignored runtime artifacts, Certbot renewal check, and status policy.
- `docs/sqladmin_audit.md` documents the current SQLAdmin model-field audit.
- `docs/assets/qr_prediction_football.png` is a QR code that opens the production landing page at `https://prediction-football.ru/`.
- API-FOOTBALL / API-SPORTS is the selected single external source for future fixtures, results, match statistics, and odds. Its API key is a local `.env` value and must not be committed.
- `android_app/` contains the Android tablet MVP client. It is a Kotlin + Jetpack Compose thin client that calls FastAPI through Retrofit and does not run ML models, calculate ML features, or access any database directly.
- `requirements.txt` pins the Python runtime dependencies used by the backend, model loading, and auth flow.

## Python Scripts

- `src/data/analyze_data.py` reads `Matches.csv` and `EloRatings.csv`, builds table schemas, missing-value reports, league/season coverage reports, and confirms the selected top-5 league slice for 2018/19-2024/25.
- `src/data/clean_data.py` filters top-5 leagues, removes rows with critical missing values, checks duplicates, teams, and ELO coverage, and synchronizes ELO by the latest available rating date `<= MatchDate`.
- `src/features/feature_registry.py` stores centralized feature lists: base features, ELO features, odds features, rolling v1/v2 features, outcome feature-set configurations, target columns, and leakage columns.
- `src/features/build_features.py` builds `matches_features_v1.csv` and `matches_features_v2.csv`: ELO/odds features, rolling goals/form features, controlled V2 rolling features, and target columns. Rolling features use historical context before 2018/19, while the final dataset remains limited to 2018/19-2024/25.
- `src/analysis/target_threshold_analysis.py` runs a research-layer class-balance analysis for candidate betting thresholds in goals, corners, yellow cards, and red cards.
- `src/models/evaluate_models.py` contains shared classification evaluation helpers: metrics, classification reports, confusion matrices, and confusion matrix figures.
- `src/models/train_outcome.py` trains the outcome prediction pipeline with a time-based split and controlled feature-set experiments: V1 only, V1 plus BTTS/Over features, V1 plus corners/yellow features, and full V2.
- `src/models/tune_outcome_logistic.py` runs the final controlled LogisticRegression optimization block: compact `C` and class-weight tuning plus validation-only draw threshold experiments.
- `src/models/train_btts.py` trains the BTTS prediction pipeline with the same time-based split and controlled feature sets: V1 only and V1 plus BTTS-related rolling features.
- `src/models/tune_btts_logistic.py` runs the final controlled BTTS LogisticRegression optimization block: compact `C` and class-weight tuning plus validation-only threshold experiments.
- `src/models/train_over25.py` trains the Over2.5 prediction pipeline with the same time-based split and controlled feature sets: V1 only and V1 plus Over2.5-related rolling features.
- `src/models/tune_over25_logistic.py` runs the final controlled Over2.5 LogisticRegression optimization block: compact `C` and class-weight tuning plus validation-only threshold experiments.
- `src/models/train_corners.py` trains the Corners Over9.5 prediction pipeline with the same time-based split and controlled feature sets: V1 only and V1 plus corners-related rolling features.
- `src/models/tune_corners_logistic.py` runs the final controlled Corners LogisticRegression optimization block: compact `C` and class-weight tuning plus validation-only threshold experiments.
- `src/models/train_yellow_cards.py` trains the Yellow Cards Over3.5 prediction pipeline with the same time-based split and controlled feature sets: V1 only and V1 plus yellow-card-related rolling features.
- `src/models/tune_yellow_cards_logistic.py` runs the final controlled Yellow Cards LogisticRegression optimization block: compact `C` and class-weight tuning plus validation-only threshold experiments.
- `src/models/train_exact_score.py` trains the Exact Score regression pipeline with separate home-goals and away-goals regressors, then rounds and clips predictions to build exact scores.
- `src/postprocessing/consistency_layer.py` builds consistency reports and applies the final priority-based rule reconciliation layer for user-facing predictions.
- `src/deployment/prepare_final_app_models.py` rebuilds the local final app model package from already selected trained artifacts and refreshes `configs/final_app_models.json` without retraining.
- `src/api/main.py` creates the FastAPI app and exposes health, model metadata, match browsing, match-based prediction, and persisted prediction endpoints.
- `src/api/admin/setup.py` attaches SQLAdmin to the FastAPI app at `/admin`, registers the dashboard and model views, and points SQLAdmin to the project-local admin templates.
- `src/api/admin/auth.py` implements SQLAdmin session-based authentication using the existing `authenticate_user()` helper while requiring the `admin` role.
- `src/api/admin/dashboard.py` implements the localized dashboard with user, match, prediction, and user-history counters plus lightweight CSS charts.
- `src/api/admin/views.py` defines SQLAdmin `ModelView` classes for Users, football data, predictions, models, metrics, and reference tables. Users allow role editing only; password hashes are hidden; dangerous create/edit/delete operations are disabled for predictions, history, matches, and reference data; admin role edits are protected against self-demotion and removal of the last administrator.
- `src/api/admin/templates/` contains localized SQLAdmin template overrides for login, layout, list, details, edit, and dashboard pages. These overrides translate user-facing admin UI text and keep SQLAdmin core files unchanged.
- `src/api/config.py` stores backend paths and API metadata.
- `src/api/schemas.py` stores Pydantic request and response schemas, including auth validation rules for username, email, and password.
- `src/api/services/auth_service.py` contains password hashing, JWT token creation/validation, current-user dependencies, registration, and login helpers.
- `src/api/services/model_registry.py` reads `configs/final_app_models.json` and loads final local model binaries from `models/final_app/`.
- `src/api/services/prediction_service.py` contains model inference, exact-score clipping, reconciliation, prediction persistence, model-aware prediction reuse by `match_id` plus deployed outcome `model_id`, and unread-history count/mark-viewed helpers.
- `src/api/database/clear_runtime_data.py` is a development-only cleanup script for runtime/demo data. It clears `user_query_history`, `prediction_characteristic_values`, `predictions`, and `users`, resets runtime identity/autoincrement counters for PostgreSQL and SQLite, and preserves football domain data, odds, teams, model metadata, metrics, and ELO ratings.
- `src/api/database/migrate_user_history_view_state.py` adds or verifies `users.last_history_viewed_at` for PostgreSQL and SQLite so existing local databases can support unread-history state.
- `src/api/database/session.py` configures the SQLAlchemy engine, session factory, and declarative base from `DATABASE_URL`; the engine uses connection pre-ping so the backend can recover cleanly after PostgreSQL connection restarts.
- `src/api/database/models.py` stores SQLAlchemy ORM models for the physical database schema.
- `src/api/database/init_db.py` creates all database tables for the configured SQL database.
- `src/api/database/migrate_external_sources.py` is an idempotent schema migration helper for the API-FOOTBALL external source table and nullable external identity fields on `matches`.
- `src/api/database/sync_api_football.py` is the manual CLI entry point for API-FOOTBALL fixtures sync. It supports dry-run mode, mock fixture payloads, real API requests, and upsert by external fixture identity.
- `src/api/database/sync_api_football_odds.py` is the manual CLI entry point for API-FOOTBALL odds sync. It supports dry-run mode, mock odds payloads, real API requests, and upsert into the existing `odds` table.
- `src/api/database/sync_api_football_results.py` is the manual CLI entry point for API-FOOTBALL results/statistics sync. It supports dry-run mode, mock payloads, real API requests, and result upsert when full score plus statistics are available.
- `src/api/database/seed_db.py` inserts minimal reference data for statuses, match sources, user roles, model types, metrics, prediction characteristics, and bookmakers.
- `src/api/database/seed_final_models.py` inserts final deployed model metadata and main final test metrics into the configured SQL database.
- `src/api/database/load_football_data.py` loads cleaned domain football data from `data/interim/matches_top5_2018_2025_clean.csv` into the configured SQL database.
- `src/api/database/load_elo_ratings.py` loads ELO rating history from `data/raw/EloRatings.csv` for teams already present in the configured SQL database, with root CSV fallback for local compatibility.
- `src/api/database/seed_demo_upcoming_matches.py` creates development demo upcoming matches as regular `matches` rows with `source=demo`, `Market Average` odds, and no match result.
- `src/api/database/backup_postgres.py` creates ignored local PostgreSQL plain SQL backups under `backups/` with `pg_dump`.
- `src/api/database/restore_postgres.py` previews or executes PostgreSQL restore from a selected plain SQL backup with `psql`; restore is dry-run by default unless `--execute` is passed.
- `src/analysis/prediction_quality_analysis.py` computes historical prediction-quality reports without storing prediction rows in the application database.
- `src/api/services/feature_service.py` builds runtime model feature vectors from SQL database data using training-compatible feature names, ordering, ELO logic, odds transforms, and rolling-history calculations.
- `src/api/services/match_service.py` contains SQLAlchemy query helpers for match listing, match details, upcoming matches, recent matches, sampled recent matches, and showcase examples.
- `src/api/services/api_football_client.py` contains a small API-FOOTBALL HTTP client with fixture, statistics, and odds request methods. It does not write to the database.
- `src/api/services/external_match_sync_service.py` contains the conservative API-FOOTBALL fixture matching and upsert logic. It uses exact team matching plus in-code aliases and does not create new teams or leagues automatically.
- `src/api/services/external_odds_sync_service.py` contains API-FOOTBALL odds parsing and upsert logic for complete 1X2 plus Over/Under 2.5 payloads. API odds are averaged across complete bookmaker sets and saved under the existing `Market Average` bookmaker; API bookmaker rows are not created.
- `src/api/services/external_result_sync_service.py` contains API-FOOTBALL result and match-statistics parsing. It writes `match_results` only when score, total corners, and total yellow cards are all available.
- `src/api/services/scheduler_service.py` registers daily APScheduler jobs inside the FastAPI backend for fixtures, odds, and results/statistics sync.

## Android App

- `android_app/` contains the Android tablet MVP application.
- The app is a thin client over FastAPI: it does not generate ML features, does not access the database directly, does not run trained models locally, and does not implement reconciliation locally.
- Implemented screens: splash, login, registration, match list, match details, prediction result, profile, and prediction history.
- The app stores JWT tokens in `SharedPreferences`, attaches them as bearer tokens through OkHttp, validates them on splash with `GET /auth/me`, and clears them on logout or `401`/`403`. Logout navigation resets to Login through a known start destination with `launchSingleTop`.
- The match list supports league and season filters. The prediction history screen displays the latest user query per `prediction_id`, compares completed-match predictions with factual results, hides internal database IDs from users, loads before first render to avoid visible row insertion, scrolls to the top on open, and highlights newly viewed prediction rows for 5 seconds by `prediction_id`.
- The UI uses Russian user-facing labels through display mapping helpers while keeping team names, league names, and country names unchanged.
- The app remains tablet-first, with basic phone support improved for the MVP. Login and Register preserve non-password input in `AuthViewModel`, keep password values local to the Compose screen, are scrollable, and use keyboard-safe IME padding. Match Details, Prediction Result, and Profile are scrollable. Prediction Result uses one column on narrow screens and two columns on wider tablet screens. Match List tabs and filters are horizontally scrollable on narrow screens.
- The Android UI redesign is completed for the current MVP. It uses a dark sports analytics theme with near-black backgrounds, dark cards, and lime accents. Login/Register use floating in-app notifications and show/hide password controls. Match List opens on Upcoming, caches loaded tabs in `MatchListViewModel`, refreshes stale cached tabs in the background after the client-side TTL expires, shows the active tab's last successful update time, and visually separates actual upcoming matches from seeded demo matches. Match Details uses a compact tablet layout; Prediction Result and History use dark analytics cards; Profile uses a centered dashboard-style user card with a smooth unread-history badge and a fallback card for non-auth profile loading problems.
- Full `WindowSizeClass` handling, tablet master-detail navigation, and landscape-specific layouts are not implemented yet.
- Email verification, password reset, push notifications, team/league logos, standings, H2H, calendar, and news screens are not implemented.
- Backend `prediction.created_at` values are stored as UTC and displayed by Android in the local timezone of the emulator or tablet.
- Android Emulator should use `http://10.0.2.2:8000/`; a physical tablet should use `http://<LAN_IP>:8000/`.
- Override the backend URL for a physical device with `-PapiBaseUrl=http://<LAN_IP>:8000/`.

## CSV Datasets

- `data/raw/Matches.csv` is the source match table: leagues, dates, teams, ELO, form, odds, results, and post-match statistics.
- `data/raw/EloRatings.csv` is the source ELO table: rating date, club, country, and rating.
- `data/interim/matches_top5_2018_2025_clean.csv` is the cleaned working slice for top-5 leagues in 2018/19-2024/25 with verified ELO coverage.
- `data/interim/matches_features_v1.csv` is the v1 feature dataset for future model training. Post-match leakage columns are not included as features.
- `data/interim/matches_features_v2.csv` is the controlled v2 feature dataset with additional rolling BTTS, Over2.5, venue-form, corners, and yellow-card features.

Files under `data/` are not committed because they are local or potentially large generated artifacts.

Data directory roles:

- `data/raw/` stores canonical source CSV files such as `Matches.csv` and `EloRatings.csv`.
- `data/interim/` stores cleaned and feature-engineered intermediate CSV files.
- `data/processed/` is reserved for processed export artifacts.
- `data/app/` stores the local SQLite fallback application database.

## Reports

- `reports/tables/matches_schema.csv` contains the `Matches.csv` schema: types, missing values, and unique counts.
- `reports/tables/elo_schema.csv` contains the `EloRatings.csv` schema.
- `reports/tables/matches_missing_values.csv` contains missing values by column for the full `Matches.csv`.
- `reports/tables/elo_missing_values.csv` contains missing values by column for the full `EloRatings.csv`.
- `reports/tables/division_season_coverage.csv` contains league and season coverage.
- `reports/tables/top5_2018_2025_scope_summary.csv` summarizes the selected working slice.
- `reports/tables/top5_2018_2025_missing_values.csv` contains missing values for key columns in the selected slice.
- `reports/tables/cleaning_quality_report.csv` records cleaning quality checks: rows, duplicates, dates, teams, and ELO coverage.
- `reports/tables/features_v1_report.csv` records final feature dataset checks: rows, columns, missing values, and historical context size for rolling features.
- `reports/tables/features_v2_report.csv` records the same checks for the V2 feature dataset.
- `reports/tables/target_threshold_analysis.csv` stores class distributions for candidate goals, corners, and yellow-card thresholds.
- `reports/tables/red_cards_distribution.csv` stores red-card target distributions by split and confirms red-card rarity.
- `reports/figures/threshold_distributions/` stores class-balance charts for goals, corners, yellow cards, and red cards.
- `reports/tables/outcome/outcome_time_split.csv` records the train/validation/test split by season.
- `reports/tables/outcome/outcome_model_metrics.csv` compares outcome models and feature sets by accuracy, balanced accuracy, macro F1, and class recall.
- `reports/tables/outcome/outcome_classification_reports.csv` stores per-class precision, recall, and F1 for each outcome model.
- `reports/tables/outcome/outcome_confusion_matrices.csv` stores confusion matrix counts for each model and split.
- `reports/tables/outcome/*_feature_importance.csv` stores feature importance tables for models that expose coefficients or feature importances.
- `reports/tables/outcome/outcome_v2_high_correlations.csv` stores highly correlated V2 feature pairs from the train split when their absolute correlation is at least 0.85.
- `reports/tables/outcome/outcome_logistic_tuning_metrics.csv` stores compact LogisticRegression tuning metrics.
- `reports/tables/outcome/outcome_logistic_threshold_validation.csv` stores validation-only draw threshold tuning results.
- `reports/tables/outcome/outcome_logistic_selected_threshold_metrics.csv` stores metrics for the selected threshold-tuned LogisticRegression candidate.
- `reports/tables/outcome/outcome_final_controlled_comparison.csv` compares the final selected LogisticRegression configuration against previous outcome references.
- `reports/figures/outcome/*_test_confusion_matrix.png` stores test confusion matrix figures.
- `reports/tables/btts/btts_time_split.csv` records the BTTS train/validation/test split by season.
- `reports/tables/btts/btts_feature_sets.csv` lists BTTS feature-set definitions.
- `reports/tables/btts/btts_model_metrics.csv` compares BTTS models by accuracy, balanced accuracy, F1, precision, and recall.
- `reports/tables/btts/btts_classification_reports.csv` stores per-class BTTS precision, recall, and F1.
- `reports/tables/btts/btts_confusion_matrices.csv` stores BTTS confusion matrix counts.
- `reports/tables/btts/btts_logistic_tuning_metrics.csv` stores compact BTTS LogisticRegression tuning metrics.
- `reports/tables/btts/btts_logistic_threshold_validation.csv` stores validation-only BTTS threshold tuning results.
- `reports/tables/btts/btts_logistic_selected_threshold_metrics.csv` stores metrics for the selected threshold-tuned BTTS candidate.
- `reports/tables/btts/btts_final_controlled_comparison.csv` compares the final selected BTTS configuration against references.
- `reports/tables/btts/*_feature_importance.csv` stores BTTS feature importance tables for models that expose coefficients or feature importances.
- `reports/figures/btts/*_test_confusion_matrix.png` stores BTTS test confusion matrix figures.
- `reports/tables/over25/over25_time_split.csv` records the Over2.5 train/validation/test split by season.
- `reports/tables/over25/over25_feature_sets.csv` lists Over2.5 feature-set definitions.
- `reports/tables/over25/over25_model_metrics.csv` compares Over2.5 models by accuracy, balanced accuracy, F1, precision, and recall.
- `reports/tables/over25/over25_classification_reports.csv` stores per-class Over2.5 precision, recall, and F1.
- `reports/tables/over25/over25_confusion_matrices.csv` stores Over2.5 confusion matrix counts.
- `reports/tables/over25/over25_logistic_tuning_metrics.csv` stores compact Over2.5 LogisticRegression tuning metrics.
- `reports/tables/over25/over25_logistic_threshold_validation.csv` stores validation-only Over2.5 threshold tuning results.
- `reports/tables/over25/over25_logistic_selected_threshold_metrics.csv` stores metrics for the selected threshold-tuned Over2.5 candidate.
- `reports/tables/over25/over25_final_controlled_comparison.csv` compares the final selected Over2.5 configuration against references.
- `reports/tables/over25/*_feature_importance.csv` stores Over2.5 feature importance tables for models that expose coefficients or feature importances.
- `reports/figures/over25/*_test_confusion_matrix.png` stores Over2.5 test confusion matrix figures.
- `reports/tables/corners/corners_time_split.csv` records the Corners train/validation/test split by season.
- `reports/tables/corners/corners_feature_sets.csv` lists Corners feature-set definitions.
- `reports/tables/corners/corners_model_metrics.csv` compares Corners models by accuracy, balanced accuracy, F1, precision, and recall.
- `reports/tables/corners/corners_classification_reports.csv` stores per-class Corners precision, recall, and F1.
- `reports/tables/corners/corners_confusion_matrices.csv` stores Corners confusion matrix counts.
- `reports/tables/corners/corners_logistic_tuning_metrics.csv` stores compact Corners LogisticRegression tuning metrics.
- `reports/tables/corners/corners_logistic_threshold_validation.csv` stores validation-only Corners threshold tuning results.
- `reports/tables/corners/corners_logistic_selected_threshold_metrics.csv` stores metrics for the selected threshold-tuned Corners candidate.
- `reports/tables/corners/corners_final_controlled_comparison.csv` compares the final selected Corners configuration against references.
- `reports/tables/corners/*_feature_importance.csv` stores Corners feature importance tables for models that expose coefficients or feature importances.
- `reports/figures/corners/*_test_confusion_matrix.png` stores Corners test confusion matrix figures.
- `reports/tables/yellow_cards/yellow_cards_time_split.csv` records the Yellow Cards train/validation/test split by season.
- `reports/tables/yellow_cards/yellow_cards_feature_sets.csv` lists Yellow Cards feature-set definitions.
- `reports/tables/yellow_cards/yellow_cards_model_metrics.csv` compares Yellow Cards models by accuracy, balanced accuracy, F1, precision, and recall.
- `reports/tables/yellow_cards/yellow_cards_classification_reports.csv` stores per-class Yellow Cards precision, recall, and F1.
- `reports/tables/yellow_cards/yellow_cards_confusion_matrices.csv` stores Yellow Cards confusion matrix counts.
- `reports/tables/yellow_cards/yellow_cards_logistic_tuning_metrics.csv` stores compact Yellow Cards LogisticRegression tuning metrics.
- `reports/tables/yellow_cards/yellow_cards_logistic_threshold_validation.csv` stores validation-only Yellow Cards threshold tuning results.
- `reports/tables/yellow_cards/yellow_cards_logistic_selected_threshold_metrics.csv` stores metrics for the selected threshold-tuned Yellow Cards candidate.
- `reports/tables/yellow_cards/yellow_cards_final_controlled_comparison.csv` compares the final selected Yellow Cards configuration against references.
- `reports/tables/yellow_cards/*_feature_importance.csv` stores Yellow Cards feature importance tables for models that expose coefficients or feature importances.
- `reports/figures/yellow_cards/*_test_confusion_matrix.png` stores Yellow Cards test confusion matrix figures.
- `reports/tables/exact_score/exact_score_time_split.csv` records the Exact Score train/validation/test split by season.
- `reports/tables/exact_score/exact_score_feature_sets.csv` lists Exact Score feature-set definitions.
- `reports/tables/exact_score/exact_score_target_metrics.csv` stores home-goals and away-goals MAE/RMSE.
- `reports/tables/exact_score/exact_score_model_metrics.csv` stores exact-score accuracy and score-derived outcome, BTTS, and Over2.5 accuracy.
- `reports/tables/exact_score/exact_score_score_distribution.csv` stores actual and predicted score distributions.
- `reports/tables/exact_score/exact_score_common_scores.csv` stores the most common actual and predicted scores.
- `reports/tables/exact_score/exact_score_final_controlled_comparison.csv` compares selected and reference Exact Score configurations.
- `reports/tables/exact_score/exact_score_final_predictions.csv` stores final Exact Score predictions used by the consistency layer.
- `reports/figures/exact_score/*` stores score-distribution and total-goals-error figures for the selected Exact Score model.
- `reports/tables/consistency/consistency_summary.csv` stores before-reconciliation consistency rates by split.
- `reports/tables/consistency/conflict_counts_by_task.csv` stores conflict counts for outcome, BTTS, and Over2.5.
- `reports/tables/consistency/inconsistency_patterns.csv` stores common logical inconsistency patterns.
- `reports/tables/consistency/conflict_examples.csv` stores example conflicting predictions.
- `reports/tables/consistency/reconciled_predictions.csv` stores final user-facing reconciled predictions.
- `reports/tables/consistency/reconciliation_summary.csv` stores before/after consistency metrics and correction counts.
- `reports/tables/consistency/reconciliation_examples.csv` stores examples of score and Over2.5 corrections.
- `reports/tables/consistency/score_correction_patterns.csv` stores common exact-score correction patterns.
- `reports/tables/consistency/over25_correction_patterns.csv` stores common Over2.5 correction patterns.
- `reports/figures/consistency/*` stores consistency and reconciliation figures.

## Model Artifacts

- `models/outcome/` stores local trained outcome models. This directory is ignored by Git because trained model files can become large.
- `models/btts/` stores local trained BTTS models. This directory is ignored by Git because trained model files can become large.
- `models/over25/` stores local trained Over2.5 models. This directory is ignored by Git because trained model files can become large.
- `models/corners/` stores local trained Corners Over9.5 models. This directory is ignored by Git because trained model files can become large.
- `models/yellow_cards/` stores local trained Yellow Cards Over3.5 models. This directory is ignored by Git because trained model files can become large.
- `models/exact_score/` stores local trained Exact Score regression models. This directory is ignored by Git because trained model files can become large.
- `models/final_app/` stores local copies of final trained models prepared for backend/API loading. This directory is ignored by Git; only metadata and documentation are tracked.

## Final App Model Package

The final app model package is a deployment-oriented local artifact layer for the future backend/API. It does not change final ML configurations and does not retrain models.

Rebuild command:

```bash
python src/deployment/prepare_final_app_models.py
```

Included final models:

- outcome final model;
- BTTS final model;
- Over2.5 final model;
- Corners Over9.5 final model;
- Yellow Cards Over3.5 final model;
- Exact Score home-goals regressor;
- Exact Score away-goals regressor.

Backend/API code should load model binaries from `models/final_app/`, read lightweight metadata from `configs/final_app_models.json`, and apply the priority-based reconciliation flow before returning user-facing predictions.

## Backend API Skeleton

The current backend is intentionally lightweight and uses SQL database-backed runtime feature generation for match-based prediction.

Run command:

```bash
uvicorn src.api.main:app --reload
```

PostgreSQL 16 through Docker Compose is the primary production-like database mode:

```bash
cp .env.example .env
docker compose up -d postgres
python src/api/database/init_db.py
python src/api/database/seed_db.py
python src/api/database/seed_final_models.py
python src/api/database/load_football_data.py
python src/api/database/load_elo_ratings.py
python src/api/database/seed_demo_upcoming_matches.py
```

The repository also includes a backend Docker service for VPS deployment preparation:

```bash
docker compose up -d --build
```

The backend container uses `Dockerfile`, starts with `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`, mounts local `models/`, `data/`, `reports/`, and `backups/`, and receives a Docker-network `DATABASE_URL` that points to the `postgres` service.

The `.env` file is local and must not be committed. SQLite remains available as a fallback when `DATABASE_URL` is not set.

The production VPS deployment uses the same Docker Compose backend and PostgreSQL services with ignored runtime artifacts copied manually to the server:

- `.env` with production secrets and API credentials;
- `models/final_app/` model binaries;
- historical data CSV files under `data/raw/` and `data/interim/`, or a PostgreSQL backup under `backups/`;
- optional report artifacts for showcase examples.

Public traffic is handled by Nginx:

```text
https://prediction-football.ru/ -> Nginx :443 -> http://127.0.0.1:8000
http://prediction-football.ru/  -> HTTPS redirect
```

Let's Encrypt certificates are managed by Certbot with the Nginx plugin. Renewal is checked with:

```bash
certbot renew --dry-run --no-random-sleep-on-renew
```

After the VPS directory is configured as a Git worktree with a read-only deploy key, the standard deployment flow is:

```bash
cd /root/Prediction_Football
git status
git pull
docker compose up -d --build
docker compose ps
```

PostgreSQL backup and restore helpers are available:

```bash
python src/api/database/backup_postgres.py
python src/api/database/restore_postgres.py backups/football_backup_YYYYMMDD_HHMMSS.sql
python src/api/database/restore_postgres.py backups/football_backup_YYYYMMDD_HHMMSS.sql --execute
```

Backup files are written to ignored local `backups/`. The scripts use `pg_dump` and `psql`; if host PostgreSQL client tools are not available, they use the Docker Compose `postgres` service, so PostgreSQL must be running.

API-FOOTBALL is prepared as the single external sports data provider. External API identity is stored through `external_sources` plus nullable `matches.external_source_id`, `matches.external_match_id`, and `matches.last_synced_at` fields. The unique API identity is `(external_source_id, external_match_id)`, while historical and demo matches can keep these fields as `NULL`. Manual fixtures sync is implemented with `python src/api/database/sync_api_football.py`; manual odds sync is implemented with `python src/api/database/sync_api_football_odds.py`; manual results/statistics sync is implemented with `python src/api/database/sync_api_football_results.py`. The fixtures sync uses conservative alias-based team matching and does not create new teams automatically. The odds sync writes only complete 1X2 and Over/Under 2.5 odds sets under `Market Average`, averages complete bookmaker sets, does not create API bookmaker rows, and never creates fake odds. The results/statistics sync writes `match_results` only when score, total corners, and total yellow cards are all available. Daily scheduled sync is implemented inside the FastAPI backend through APScheduler: fixtures at `03:00` for `today -> today + 14 days`, odds at `06:00` for up to 25 fixtures in `today -> today + 7 days`, and results/statistics at `23:30` for up to 25 fixtures in `today - 2 days -> today` by default, all configurable through `.env`. These windows are intentionally small to reduce API usage and keep worst-case daily usage near 80 requests. `API_FOOTBALL_SEASON=2026` is the target app season, but API-FOOTBALL free plans may not expose that season yet; local API checks may need an available season. Scheduler health is available at `GET /scheduler/health`. Admin sync endpoints, sync logs, and monthly retraining automation are not implemented yet.

## SQLAdmin Administration Panel

The FastAPI backend mounts a SQLAdmin administration panel at `/admin`. It is intended for browser-based operational administration and is not used by the Android client. Android continues to authenticate through JWT bearer tokens, while `/admin` uses a separate signed session cookie through SQLAdmin's `AuthenticationBackend`.

The admin package is structured as follows:

- `src/api/admin/auth.py`: session login/logout/authentication for `/admin`, reusing the existing `authenticate_user()` helper and requiring the `admin` role.
- `src/api/admin/setup.py`: SQLAdmin registration, `/admin` mount configuration, dashboard registration, and view registration.
- `src/api/admin/dashboard.py`: operational dashboard with total users, users in the last 7 days, total matches, upcoming matches, total predictions, predictions in the last 7 days, latest predictions, and latest user query history.
- `src/api/admin/views.py`: SQLAdmin model views, Russian labels, safe list/detail/filter/export configuration, foreign-key display helpers, read-only rules, hidden password hashes, and admin role protection.
- `src/api/admin/templates/`: localized template overrides for login, layout, list, detail, edit, and dashboard pages. The overrides translate user-facing UI strings while leaving SQLAdmin core unchanged.

The enabled views cover Users, UserRoles, Matches, MatchResults, Odds, Predictions, PredictionCharacteristicValues, UserQueryHistory, Models, ModelMetrics, Countries, Leagues, Seasons, Teams, TeamEloRatings, Metrics, ModelTypes, MatchSources, ExternalSources, Bookmakers, PredictionCharacteristics, and MatchStatuses.

The first administrator is created by promoting an existing trusted user in the database or through a controlled admin process; public registration creates regular users only. In the local development database, `Vova777` was promoted to `admin` for verification.

Safety constraints:

- `password_hash` is not displayed in the Users view.
- Users can be viewed, searched, filtered, and have only their role edited.
- User deletion is disabled.
- Matches, predictions, user query history, model metadata, metrics, odds, and reference tables are read-only in the first admin-panel stage.
- Administrators cannot demote their own role.
- The last remaining administrator cannot be demoted.

Known limitation: when a protected role update is rejected, SQLAdmin displays the Russian error message in the edit form and does not change the database, but SQLAdmin's internal edit handler still logs the caught exception traceback in backend logs.

Endpoints:

- `GET /` returns the Russian production landing page with labeled navigation links to `/`, `/health`, `/docs`, and `/admin/login`.
- `GET /health` returns service status.
- `GET /db/health` checks configured database connectivity and should report `database=postgresql` in PostgreSQL mode.
- `GET /scheduler/health` returns scheduler enabled/running state and next run times without changing existing health schemas.
- `GET /models` returns final model metadata for each configured task.
- `POST /auth/register` creates a user with a bcrypt password hash.
- `POST /auth/login` returns a JWT bearer token.
- `GET /auth/me` validates and returns the current user.
- `GET /users/me/history` returns authenticated prediction query history.
- `GET /users/me/history/unread-count` returns the number of distinct history prediction IDs newer than `users.last_history_viewed_at`.
- `POST /users/me/history/mark-viewed` updates `users.last_history_viewed_at` to the latest history query timestamp, or current UTC time when the user has no history rows.
- `POST /predict` returns a unified prediction response for sample/manual JSON input.
- `GET /matches` returns paginated real matches from the configured SQL database with optional league, season, and date filters.
- `GET /matches/{match_id}` returns match details with teams, result, and odds.
- `GET /matches/upcoming` returns matches without result.
- `GET /matches/recent` returns recent finished matches.
- `GET /matches/recent/sampled` returns a balanced recent sample across league-season pairs for the Android filters.
- `GET /matches/showcase` returns historical demonstration examples selected from prediction-quality reports. These examples show strong historical matches for the MVP demo and do not replace aggregate model metrics.
- `POST /predict/{match_id}` builds runtime features from SQL database data, runs final models, reconciles outputs, stores prediction rows, and returns the final prediction.
- `GET /predictions/{prediction_id}` returns a persisted prediction with characteristic values.

Unknown FastAPI routes use browser-aware error handling: browser requests with `Accept: text/html` receive a Russian HTML 404 page with links back to `/`, `/docs`, and `/admin/login`, while API clients continue to receive the JSON response `{"detail":"Not Found"}`. Unknown SQLAdmin routes remain handled by SQLAdmin/Starlette to avoid customizing SQLAdmin internals.

Swagger UI remains available at `/docs`. Its technical endpoint list is not translated, but the page includes a simple link back to `/` for production navigation during demonstration.

## Database Layer

The primary local database mode is PostgreSQL 16 through Docker Compose. The local SQLite fallback database is stored at:

```text
data/app/football.db
```

Create the physical schema:

```bash
docker compose up -d postgres
python src/api/database/init_db.py
python src/api/database/seed_db.py
python src/api/database/seed_final_models.py
python src/api/database/load_football_data.py
python src/api/database/load_elo_ratings.py
python src/api/database/seed_demo_upcoming_matches.py
```

The football loader uses `data/interim/matches_top5_2018_2025_clean.csv` as the source for domain data. It fills countries, leagues, seasons, teams, matches, match results, bookmakers, and odds. Odds rows store 1X2 odds plus Over/Under 2.5 goal-total odds so runtime odds features match the training feature sets. The configured SQL database also stores ELO rating history, final deployed model metadata, and main final test metrics. `POST /predict/{match_id}` generates runtime features from SQL database rows instead of training feature CSV files, persists predictions and prediction characteristic values, and reuses an existing prediction for the same `match_id` and deployed outcome `model_id`. A future retrained/deployed outcome model with a different `model_id` can create a new prediction for the same match. Authenticated requests add rows to `user_query_history`; this table stores user actions and can contain several rows for the same `prediction_id`. `users.last_history_viewed_at` stores the user's latest viewed-history marker for unread-count calculations, and `mark-viewed` advances it after the history screen has loaded.

Development-only cleanup:

```bash
python src/api/database/clear_runtime_data.py
```

This script clears only runtime tables in dependency-safe order: `user_query_history`, `prediction_characteristic_values`, `predictions`, and `users`. It preserves football domain tables and reference/model data, including `matches`, `odds`, `teams`, `models`, `model_metrics`, and `team_elo_ratings`.

Runtime IDs are reset after cleanup. PostgreSQL uses `TRUNCATE ... RESTART IDENTITY` for the runtime tables. SQLite deletes runtime rows and clears `sqlite_sequence` entries for the runtime tables that own autoincrement IDs: `user_query_history`, `predictions`, and `users`. `prediction_characteristic_values` has a composite primary key and no standalone autoincrement ID. A quick manual check is to run the script, register a new user, and confirm that the new `users.id` starts from `1`; then create a new prediction and confirm that the new `predictions.id` starts from `1`.

## Outcome Feature Sets

- `v1_only` uses ELO, odds, implied probabilities, and simple rolling goals/form features.
- `v1_btts_over` adds rolling BTTS and Over2.5 rates to V1.
- `v1_corners_yellow` adds rolling corners and yellow-card averages to V1.
- `full_v2` combines all V1 and V2 rolling features.

V2 feature sets were tested but were not selected as the final outcome configuration because they did not provide stable test improvement.

## Target Threshold Analysis

The threshold analysis checks standard football betting lines before modeling secondary over/under tasks. It is a research/documentation artifact, not a prediction pipeline.

Checked thresholds:

- goals: `Over1.5`, `Over2.5`, `Over3.5`, `Over4.5`;
- corners: `Over8.5`, `Over9.5`, `Over10.5`, `Over11.5`;
- yellow cards: `Over2.5`, `Over3.5`, `Over4.5`, `Over5.5`;
- red cards: `Over0.5`, `Over1.5`.

Selected thresholds:

- `Over2.5` goals was selected because it is much more balanced than `Over1.5` and much less rare than `Over4.5`, while remaining a standard and practical football betting line.
- `Over9.5` corners was selected because it is almost perfectly balanced in the current dataset and is a standard corners betting line.
- `Over3.5` yellow cards was selected because it gives the best compromise between class balance and practical interpretation.

Red cards were analyzed separately and rejected as a main ML task because red-card targets are extremely imbalanced: any red card appears in a small minority of matches, and higher red-card thresholds are too rare for a stable primary target.

## Final Outcome Configuration

The selected outcome model is:

```text
features: v1_only
model: LogisticRegression
C: 0.05
class_weight: {"H": 1.0, "D": 1.6, "A": 1.0}
decision rule: default argmax
```

This configuration was selected because it slightly improved accuracy and Macro F1 over the original V1 LogisticRegression baseline while improving draw recall. Threshold tuning was tested but not selected because the test trade-off was worse.

## BTTS Feature Sets

- `v1_only` uses the same V1 feature space as the outcome pipeline.
- `v1_btts_related` adds rolling BTTS-rate and Over2.5-rate features to V1.

BTTS-related rolling features were tested but were not selected as final because they did not improve the selected BTTS baseline.

## Final BTTS Configuration

The selected BTTS model is:

```text
features: v1_only
model: LogisticRegression
C: 1.0
class_weight: None
threshold: 0.50
```

BTTS uses balanced accuracy as the main practical metric because positive-class F1 can be misleading: an always-`Yes` dummy model gets high F1 but has zero recall for `No`. Threshold tuning and custom class weights were tested but not selected because they improved one side of the class balance while hurting the other side too much.

## Over2.5 Feature Sets

- `v1_only` uses the same V1 feature space as the outcome pipeline.
- `v1_over25_related` adds rolling Over2.5-rate and BTTS-rate features to V1.

Over2.5-related rolling features were tested but were not selected as final because they did not improve the selected Over2.5 baseline.

## Final Over2.5 Configuration

The selected Over2.5 model is:

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

CatBoost became the final model for Over2.5 because it had the strongest validation balanced accuracy and the strongest practical test metrics among stable candidates. LogisticRegression tuning was still performed as a standardized controlled baseline optimization step across tasks, but the tuned LogisticRegression remained weaker than CatBoost. Threshold tuning did not improve over the default threshold.

## Corners Feature Sets

- `v1_only` uses the same V1 feature space as the outcome pipeline.
- `v1_corners_related` adds compact rolling corners features to V1: corners for, corners against, total corners, Corners Over9.5 rate, and short-term corner-form indicators.

Corners-related rolling features are built only from previous matches with `shift(1)`. Current-match corners are used only for `Target_Corners_Over95`, not as model features. Historical context is used in the same way as the existing feature pipeline: earlier top-5 league matches provide rolling history, while the final modeling dataset remains limited to 2018/19-2024/25.

Corners-related rolling features were tested but were not selected as final because they did not provide stable validation or test improvement over `v1_only`.

## Final Corners Configuration

The selected Corners Over9.5 model is:

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

CatBoost became the final Corners model because it had the strongest validation balanced accuracy and the strongest stable test performance among practical candidates. LogisticRegression tuning improved the LogisticRegression baseline, but the tuned LogisticRegression remained weaker than CatBoost. RandomForest was kept as a reference architecture and showed clear overfitting. Threshold tuning was tested on validation only and was not selected because it did not improve over the default `0.50` threshold.

## Yellow Cards Feature Sets

- `v1_only` uses the same V1 feature space as the outcome pipeline.
- `v1_yellow_related` adds compact rolling yellow-card features to V1: yellow cards for, yellow cards against, total yellow cards, Yellow Cards Over3.5 rate, and short-term yellow-card form indicators.

Yellow-card-related rolling features are built only from previous matches with `shift(1)`. Current-match yellow cards are used only for `Target_YellowCards_Over35`, not as model features. Historical context is used in the same way as the existing feature pipeline: earlier top-5 league matches provide rolling history, while the final modeling dataset remains limited to 2018/19-2024/25.

Yellow-related rolling features were selected because they improved validation and test behavior over `v1_only`, especially for the LogisticRegression baseline.

## Final Yellow Cards Configuration

The selected Yellow Cards Over3.5 model is:

```text
features: v1_yellow_related
model: LogisticRegression
C: 0.05
class_weight: balanced
threshold: 0.50
```

LogisticRegression became the final Yellow Cards model because the tuned configuration produced the most stable explainable balance between `Yes` and `No` recall on the test split. RandomForest had the strongest validation balanced accuracy, but it was rejected as final because it strongly overfit. CatBoost was rejected because it shifted too much toward the `Yes` class and had weak `No` recall on test. Threshold tuning was tested on validation only, but the selected validation threshold did not improve the final test result, so the default `0.50` threshold was kept.

## Exact Score Configuration

Exact Score is implemented as a simple regression pipeline rather than a large multiclass score classifier. The pipeline trains separate models for:

- `Target_HomeGoals`;
- `Target_AwayGoals`.

Predicted goals are rounded to integers and clipped to the range `0-6`, then combined into an exact score. The selected controlled baseline is:

```text
features: v1_score_related
model: Ridge regression
post-processing: round and clip to 0-6
```

Exact score accuracy is expected to be low for football. This pipeline is used as a detail layer and as an input to post-processing reconciliation, not as the main prediction source.

## Consistency And Reconciliation Layer

The consistency layer is a deterministic rule-based post-processing block. It does not retrain models and does not change final model configurations.

Final prediction priority:

1. Outcome prediction.
2. BTTS prediction.
3. Over2.5 prediction.
4. Exact score prediction.

Outcome is the main anchor because it is the primary diploma task. BTTS is second because it constrains score structure. Over2.5 is third and can be corrected only when it conflicts with the higher-priority `Outcome + BTTS` structure. Exact score is the lowest-priority detail layer and is corrected to the nearest score that satisfies the final higher-level predictions.

Before reconciliation, exact-score-derived predictions often conflict with direct outcome, BTTS, and Over2.5 predictions. After final priority-based reconciliation, all splits are fully consistent:

```text
split       before consistency  after consistency  remaining conflicts
train       0.4001              1.0000             0
validation  0.3773              1.0000             0
test        0.3659              1.0000             0
```

On the test split, the layer corrected 1015 exact scores and 149 Over2.5 predictions while preserving outcome and BTTS predictions.

## Leakage Policy

v1 features do not include current-match results or statistics: `FTHome`, `FTAway`, `FTResult`, `HT*`, shots, fouls, corners, or cards. These fields are used only to create target columns and rolling features with `shift(1)`. Corners features follow the same policy: `HomeCorners` and `AwayCorners` are not used directly as features for the current match, and rolling corners features are shifted so each row only sees previous team history. Yellow Cards features also follow this policy: `HomeYellow` and `AwayYellow` are not used directly as current-match features, and rolling yellow-card features are shifted so each row only sees previous team history.
