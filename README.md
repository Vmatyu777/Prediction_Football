# Prediction Football

Diploma project: a machine learning information system for football match prediction with a mobile application.

## Current Status

Implemented:

- data analysis and cleaning pipeline;
- V1 and controlled V2 feature engineering;
- outcome prediction pipeline for `Home Win / Draw / Away Win`;
- controlled LogisticRegression tuning for the final outcome baseline;
- BTTS prediction pipeline and controlled LogisticRegression tuning;
- Over2.5 prediction pipeline and controlled LogisticRegression tuning;
- Corners Over9.5 prediction pipeline and controlled LogisticRegression tuning;
- Yellow Cards Over3.5 prediction pipeline and controlled LogisticRegression tuning;
- exact score regression pipeline;
- priority-based consistency and reconciliation layer;
- final app model package metadata for future backend/API;
- FastAPI backend with PostgreSQL runtime persistence for Android/mobile usage, plus SQLite legacy fallback;
- Android tablet MVP client under `android_app/`;
- mobile authentication flow with registration, login, JWT token storage, profile, and prediction history.

Not implemented yet:

- other over/under models beyond the finalized diploma scope;
- advanced account features such as OAuth, refresh tokens, password reset, or email confirmation.

## Data Scope

The current dataset scope is intentionally compact and explainable:

- leagues: top-5 European first divisions (`E0`, `D1`, `SP1`, `I1`, `F1`);
- seasons: 2018/19-2024/25;
- split strategy: time-based split only, no random split.

Large source and generated datasets are ignored by Git. Locally, source CSV files should be placed at:

```text
data/raw/Matches.csv
data/raw/EloRatings.csv
```

Local data directory roles:

- `data/raw/`: canonical source CSV files.
- `data/interim/`: cleaned and feature-engineered intermediate CSV files.
- `data/processed/`: reserved for processed export artifacts.
- `data/app/`: local SQLite fallback database for legacy/development runs without `DATABASE_URL`.

## Data And Feature Pipeline

Run the preparation pipeline:

```bash
python src/data/analyze_data.py
python src/data/clean_data.py
python src/features/build_features.py
```

The pipeline creates local files under `data/interim/` and reports under `reports/tables/`.

Feature engineering:

- `V1_FEATURES`: ELO, odds, implied probabilities, simple rolling goals/form features;
- `V2_FEATURES`: controlled additional rolling BTTS, Over2.5, venue-form, corners, and yellow-card features.

V2 features were tested for outcome prediction but were not selected as final because they did not provide stable test improvement.

## Target Threshold Analysis

Before finalizing secondary over/under targets, the project includes a separate class-balance analysis for standard football betting lines. The thresholds were not selected arbitrarily: they were checked against target distributions to avoid extreme imbalance while keeping practical betting interpretation.

Analyzed markets:

- goals;
- corners;
- yellow cards;
- red cards.

Key findings:

- Goals: `Over1.5` is too frequent, while `Over4.5` is too rare. `Over2.5` gives the best balance between class distribution and practical usefulness.
- Corners: `Over9.5` is almost perfectly balanced and is the most reasonable corners threshold among the tested lines.
- Yellow Cards: `Over3.5` gives the best compromise between class balance and practical interpretation.
- Red Cards: red-card targets are too imbalanced, so red cards were not selected as a main prediction task.

The selected betting lines are therefore:

```text
goals:        Over2.5
corners:      Over9.5
yellow cards: Over3.5
```

## Outcome Prediction

Run the outcome experiments:

```bash
python src/models/train_outcome.py
python src/models/tune_outcome_logistic.py
```

Main metric:

- Macro F1.

Additional metrics:

- accuracy;
- balanced accuracy;
- draw recall.

Final outcome configuration:

```text
features: v1_only
model: LogisticRegression
C: 0.05
class_weight: {"H": 1.0, "D": 1.6, "A": 1.0}
decision rule: default argmax
```

Final test metrics:

```text
accuracy:          0.5111
macro F1:          0.4867
balanced accuracy: 0.4861
draw recall:       0.3836
```

Threshold tuning was tested but was not selected as final because it improved draw recall while reducing test accuracy and Macro F1.

## BTTS Prediction

BTTS means `Both Teams To Score`.

Target:

- `Yes`: both teams scored at least one goal;
- `No`: at least one team did not score.

The BTTS pipeline uses the same time-based split as the outcome pipeline:

- train: seasons 2018-2022;
- validation: season 2023;
- test: season 2024.

Controlled feature sets:

- `v1_only`;
- `v1_btts_related`.

Models:

- `DummyClassifier`;
- `LogisticRegression`;
- `RandomForestClassifier` as reference;
- `CatBoostClassifier` as reference.

BTTS has an important metric issue: positive-class F1 can be misleading because `BTTS Yes` is slightly more frequent. A `DummyClassifier` that always predicts `Yes` gets high F1, but completely ignores the `No` class. For this reason, BTTS evaluation focuses on balanced accuracy and recall balance, while still reporting F1, precision, and recall.

Final BTTS configuration:

```text
features: v1_only
model: LogisticRegression
C: 1.0
class_weight: None
threshold: 0.50
```

Final test metrics:

```text
accuracy:          0.5437
balanced accuracy: 0.5335
F1:                0.6042
Yes recall:        0.6291
No recall:         0.4379
```

BTTS-related rolling features were tested but were not selected as final. Threshold tuning and custom class weights were also tested but were not selected because they created unstable trade-offs between `Yes` and `No` recall.

## Over2.5 Prediction

Over2.5 predicts whether the total number of goals in a match is greater than 2.5.

Target:

- `Yes`: total goals > 2.5;
- `No`: total goals <= 2.5.

The Over2.5 pipeline uses the same time-based split as the outcome and BTTS pipelines:

- train: seasons 2018-2022;
- validation: season 2023;
- test: season 2024.

Controlled feature sets:

- `v1_only`;
- `v1_over25_related`.

Models:

- `DummyClassifier`;
- `LogisticRegression`;
- `RandomForestClassifier` as reference;
- `CatBoostClassifier` as reference.

Balanced accuracy is important for Over2.5 because a dummy always-`Yes` model can get a misleadingly high positive-class F1 while completely ignoring `No`.

Final Over2.5 configuration:

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

Final test metrics:

```text
accuracy:          0.5958
balanced accuracy: 0.5875
F1:                0.6516
Yes recall:        0.7070
No recall:         0.4681
```

Over2.5-related rolling features were tested but were not selected as final. LogisticRegression tuning improved metrics slightly, but final CatBoost remained stronger. Threshold tuning did not improve over the default `0.50` threshold.

## Corners Over9.5 Prediction

Corners Over9.5 predicts whether the total number of corners in a match is greater than 9.5.

Target:

- `Yes`: total corners > 9.5;
- `No`: total corners <= 9.5.

The Corners pipeline uses the same time-based split as the other finalized pipelines:

- train: seasons 2018-2022;
- validation: season 2023;
- test: season 2024.

The target classes are close to balanced across the dataset, near a 50/50 split between `Yes` and `No`.

Controlled feature sets:

- `v1_only`;
- `v1_corners_related`.

Models:

- `DummyClassifier`;
- `LogisticRegression`;
- `RandomForestClassifier` as reference;
- `CatBoostClassifier` as reference.

Balanced accuracy is the main practical metric for Corners Over9.5 because a `DummyClassifier` can get a misleadingly high positive-class F1 by always predicting `Yes`, while completely missing the `No` class.

Final Corners configuration:

```text
features: v1_only
model: CatBoostClassifier
threshold: 0.50
```

Final test metrics:

```text
accuracy:          0.5563
balanced accuracy: 0.5560
F1:                0.5150
Yes recall:        0.4730
No recall:         0.6390
```

Corners-related rolling features were tested but did not provide stable improvement over `v1_only`. LogisticRegression tuning improved the baseline LogisticRegression, but final CatBoost was more stable and stronger by validation balanced accuracy. RandomForest showed clear overfitting. Threshold tuning did not improve over the default `0.50` threshold.

## Yellow Cards Over3.5 Prediction

Yellow Cards Over3.5 predicts whether the total number of yellow cards in a match is greater than 3.5.

Target:

- `Yes`: total yellow cards > 3.5;
- `No`: total yellow cards <= 3.5.

The Yellow Cards pipeline uses the same time-based split as the other finalized pipelines:

- train: seasons 2018-2022;
- validation: season 2023;
- test: season 2024.

The target is moderately imbalanced: `Yes` is about 58% of the full dataset, while `No` is about 42%.

Controlled feature sets:

- `v1_only`;
- `v1_yellow_related`.

Models:

- `DummyClassifier`;
- `LogisticRegression`;
- `RandomForestClassifier` as reference;
- `CatBoostClassifier` as reference.

Balanced accuracy is the main practical metric for Yellow Cards Over3.5 because a `DummyClassifier` can get misleading accuracy and positive-class F1 by always predicting `Yes`, while completely missing the `No` class.

Final Yellow Cards configuration:

```text
features: v1_yellow_related
model: LogisticRegression
C: 0.05
class_weight: balanced
threshold: 0.50
```

Final test metrics:

```text
accuracy:          0.5512
balanced accuracy: 0.5559
F1:                0.5731
Yes recall:        0.5244
No recall:         0.5874
```

Yellow-related rolling features provided stable improvement over `v1_only`. LogisticRegression tuning improved the baseline and produced the most stable explainable final model. Threshold tuning improved validation balanced accuracy but did not improve the final test result, so the default `0.50` threshold was selected. RandomForest was rejected as final because it strongly overfit, while CatBoost shifted too much toward the `Yes` class.

## Consistency And Reconciliation Layer

The project includes a separate rule-based post-processing layer for user-facing predictions. It does not retrain models and does not change the final ML configurations. Its role is to make predictions logically consistent before they are shown together.

Final priority hierarchy:

1. Outcome prediction.
2. BTTS prediction.
3. Over2.5 prediction.
4. Exact score prediction.

Outcome is the main anchor because match outcome prediction is the primary diploma task and the most important decision layer. BTTS is second because it directly constrains whether both teams can score. Over2.5 is third and can be corrected only when it conflicts with the higher-priority `Outcome + BTTS` structure. Exact score is the lowest-priority detail layer because it is the noisiest and least stable prediction task.

Final reconciliation logic:

- keep the final outcome prediction unchanged;
- keep the final BTTS prediction unchanged when at least one score can satisfy `Outcome + BTTS`;
- keep Over2.5 if it is compatible with `Outcome + BTTS`;
- correct Over2.5 only when no score can satisfy all three higher-level predictions;
- correct exact score to the nearest score that satisfies final `Outcome + BTTS + Over2.5`.

Exact score no longer controls the system. Instead, exact score is adjusted to match the more stable predictions.

Final consistency metrics:

```text
split       before consistency  after consistency  remaining conflicts
train       0.4001              1.0000             0
validation  0.3773              1.0000             0
test        0.3659              1.0000             0
```

On the test split, the reconciliation layer corrected 1015 exact scores and 149 Over2.5 predictions while leaving outcome and BTTS predictions unchanged.

## Final App Model Package

The ML research layer is finalized for the current diploma scope. A local model package is prepared for the future backend/API under:

```text
models/final_app/
```

The package can be rebuilt from the selected final local model artifacts with:

```bash
python src/deployment/prepare_final_app_models.py
```

This directory contains local copies of the final trained model artifacts for:

- outcome;
- BTTS;
- Over2.5;
- Corners Over9.5;
- Yellow Cards Over3.5;
- Exact Score home-goals regression;
- Exact Score away-goals regression.

Model binaries remain ignored by Git because `models/` is a local artifact directory. The tracked metadata lives in:

```text
docs/final_app_models.md
configs/final_app_models.json
```

The future backend/API should load models from `models/final_app/`, use the tracked metadata for task names and paths, and pass final user-facing predictions through the priority-based reconciliation layer.

## Backend API Skeleton

The FastAPI backend lives under:

```text
src/api/
```

Available endpoints:

- `GET /health`;
- `GET /db/health`;
- `GET /models`;
- `POST /auth/register`;
- `POST /auth/login`;
- `GET /auth/me`;
- `GET /users/me/history`;
- `GET /matches`;
- `GET /matches/{match_id}`;
- `GET /matches/upcoming`;
- `GET /matches/recent`;
- `GET /matches/recent/sampled`;
- `GET /matches/showcase`;
- `POST /predict`.
- `POST /predict/{match_id}`;
- `GET /predictions/{prediction_id}`.

Run the backend locally:

```bash
uvicorn src.api.main:app --reload
```

For Android emulator or physical tablet testing, bind the backend to all interfaces:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Install Python runtime dependencies with:

```bash
pip install -r requirements.txt
```

The pinned backend/auth stack includes FastAPI, Uvicorn, Pydantic, SQLAlchemy, `psycopg[binary]`, `python-dotenv`, pandas, NumPy, scikit-learn, CatBoost, PyJWT, `passlib[bcrypt]`, and `bcrypt==4.0.1`.

PostgreSQL 16 through Docker Compose is the primary production-like database mode. Copy `.env.example` to `.env`, keep `.env` local and uncommitted, then start PostgreSQL:

```bash
docker compose up -d postgres
```

SQLite is preserved as a legacy/local fallback when `DATABASE_URL` is not set. In the PostgreSQL mode, `GET /db/health` should return `database=postgresql`.

API-FOOTBALL / API-SPORTS is the selected single external source for future fixtures, match results, match statistics, and odds. The API key must be stored only in local `.env` as `API_FOOTBALL_API_KEY`; `.env.example` contains only an empty template value. External API identity is stored through `external_sources` and nullable external fields on `matches` so API-loaded matches can be upserted without duplicates while historical and demo matches can keep `NULL` external ids.

API-FOOTBALL fixtures sync is implemented as a manual CLI script:

```bash
python src/api/database/sync_api_football.py --league "Premier League" --season 2026 --next 10 --dry-run
```

The fixtures sync stores only scheduled, postponed, and cancelled API fixtures. Finished fixtures are skipped until the separate result/statistics sync is implemented. Team matching is intentionally conservative: the sync first tries exact `(country, team name)` matching, then an in-code alias mapping for known API-FOOTBALL versus historical-data naming differences. New teams and leagues are not created automatically because duplicate teams would break runtime ML feature history.

API-FOOTBALL odds sync is implemented as a manual CLI script using the existing `odds` table:

```bash
python src/api/database/sync_api_football_odds.py --fixture-id 123456 --dry-run
```

Odds sync stores only complete 1X2 and Over/Under 2.5 odds sets. It does not create fake odds and skips incomplete bookmaker payloads with warnings. Result/statistics update is not implemented yet. Scheduled automation is future work. Recommended future sync frequency is: upcoming fixtures daily; odds daily for matches in the next 1-7 days; results/statistics 1-2 times daily after result sync is implemented. Admin-triggered retraining or monthly retraining is also future work and is not automated by the current backend.

The `/predict` endpoint remains available for sample/manual JSON input. The match-based `/predict/{match_id}` flow loads final models from `models/final_app/`, reads metadata from `configs/final_app_models.json`, generates runtime features from the configured SQL database, applies the priority-based reconciliation layer, and stores prediction outputs.

Repeated `POST /predict/{match_id}` calls reuse an existing prediction when the same `match_id` and the same deployed outcome `model_id` are already stored. If the deployed outcome model changes after future retraining and receives a different `model_id`, the backend can create a new prediction for the same match. This avoids duplicate `prediction_characteristic_values` for repeated requests while preserving old predictions.

Match rows include a `match_sources` reference (`historical`, `demo`, or `api`). Historical CSV-loaded matches use `historical`; development demo upcoming matches use `demo`; `api` is reserved for a future external loader. Match summary and detail responses expose the source so Android can show a user-facing source label.

The match list separates recent matches from demonstration examples. `GET /matches/recent/sampled` returns the latest finished matches balanced across league-season pairs. `GET /matches/showcase` returns historical matches selected from `reports/tables/prediction_quality/prediction_quality_match_scores.csv` to demonstrate cases where the existing model predictions matched factual results well. Showcase examples do not replace model metrics and are not a general quality estimate.

Authentication uses short-lived MVP JWT bearer tokens:

- `POST /auth/register` creates a user with a bcrypt password hash.
- `POST /auth/login` returns an access token.
- Android stores the token in `SharedPreferences` and sends `Authorization: Bearer <token>` through an OkHttp interceptor.
- `GET /auth/me` validates the current token for Splash/profile startup.
- `GET /users/me/history` returns the authenticated user's prediction query history.

Credential validation rules:

- username: only Latin letters, digits, `_`, and `-`;
- email: ASCII email format, no Cyrillic characters;
- password: at least 8 printable ASCII characters, at least one Latin letter, and at least one digit; special characters are allowed.

## Android Tablet MVP

The Android MVP lives under:

```text
android_app/
```

It is a thin Kotlin + Jetpack Compose client for the FastAPI backend:

- it does not calculate ML features;
- it does not access PostgreSQL, SQLite, or any backend database directly;
- it does not run trained models locally;
- it calls FastAPI endpoints through Retrofit.

The Android app remains tablet-first, with basic phone support improved for the MVP. Login and registration forms preserve input across configuration changes, are vertically scrollable, and use IME padding for keyboard-safe interaction. Match Details, Prediction Result, and Profile are vertically scrollable. Prediction Result uses one column for prediction metric cards on narrow screens and two columns on wider tablet screens. Match List tabs and filters are horizontally scrollable on narrow screens. Full `WindowSizeClass` support, tablet master-detail navigation, and landscape-specific layouts are not implemented yet.

Implemented screens:

- splash screen with token validation;
- login;
- registration;
- match list with Recent, Upcoming, and Examples tabs;
- match details;
- prediction result;
- profile;
- prediction history.

The match list includes league and season filters with an `All` option. The history screen shows unique predictions without visual duplicates: rows are sorted by `query_date` descending and then grouped by `prediction_id`, so the latest user action is shown for each stored prediction. For completed matches, Android compares prediction characteristics with the factual result.

The Android UI maps technical backend values such as `H / D / A`, `Yes / No`, match statuses, and bookmaker/source names to Russian user-facing labels. Match outcome probabilities are shown with full labels (`Home win`, `Draw`, `Away win` equivalents in Russian), not short betting notation. Historical match sources are not shown in the UI; demo and API sources are shown as user-facing labels. Team names, league names, and country names are kept as returned by the backend.

Prediction timestamps are stored by the backend as UTC `created_at` values. Android treats backend `created_at` as UTC and displays it in the local timezone of the emulator or physical tablet. The device timezone affects display only.

Backend URL defaults:

- Android Emulator: `http://10.0.2.2:8000/`;
- physical tablet: `http://<LAN_IP>:8000/`.

The debug build reads `BuildConfig.API_BASE_URL`. The default is the emulator URL. For a physical Android tablet on the same LAN, build with:

```bash
cd android_app
./gradlew :app:assembleDebug -PapiBaseUrl=http://<LAN_IP>:8000/
```

`10.0.2.2` works only in Android Emulator. A physical tablet must use the laptop's LAN IP address and the backend must listen on `0.0.0.0:8000`.

## Database Layer

The SQLAlchemy database layer lives under:

```text
src/api/database/
```

Primary database mode:

```text
PostgreSQL 16 through Docker Compose
```

Local SQLite fallback path:

```text
data/app/football.db
```

Create tables and load the local PostgreSQL database:

```bash
docker compose up -d postgres
python src/api/database/init_db.py
python src/api/database/seed_db.py
python src/api/database/seed_final_models.py
python src/api/database/load_football_data.py
python src/api/database/load_elo_ratings.py
python src/api/database/seed_demo_upcoming_matches.py
```

The loader uses:

```text
data/interim/matches_top5_2018_2025_clean.csv
```

The ELO loader uses `data/raw/EloRatings.csv` as its primary source and keeps the root `EloRatings.csv` path only as a local fallback.

It fills countries, leagues, seasons, teams, matches, match results, bookmakers, and odds. Odds rows store 1X2 market odds and Over/Under 2.5 goal-total odds so runtime features can match the deployed training feature sets. The configured SQL database also stores ELO rating history and lightweight metadata for the final deployed ML models and their main test metrics.

External source identity for API-loaded matches is prepared through:

```text
external_sources
matches.external_source_id
matches.external_match_id
matches.last_synced_at
```

The unique external identity is `(external_source_id, external_match_id)`. `external_match_id` is not globally unique by itself, and `NULL` remains allowed for historical and demo matches.

`POST /predict/{match_id}` builds model feature vectors from SQL match, odds, ELO, and rolling match history, calls the existing final models, applies the reconciliation layer, stores the prediction, and returns the final user-facing JSON. Repeated calls for the same match and deployed outcome model reuse the stored prediction instead of creating duplicates.

When the request includes a valid bearer token, the backend stores a `user_query_history` row. This table is an action log: repeated user requests can create multiple history rows for the same `prediction_id`, while Android displays only the latest row per prediction to avoid visual duplicates.

Development-only runtime cleanup:

```bash
python src/api/database/clear_runtime_data.py
```

This script clears only runtime/demo tables: `users`, `user_query_history`, `predictions`, and `prediction_characteristic_values`. It does not delete football domain data, odds, teams, leagues, seasons, model metadata, model metrics, or ELO ratings.

Runtime feature generation for `POST /predict/{match_id}` lives in `src/api/services/feature_service.py`. It uses the configured SQL database as the runtime source and builds the same deployed feature sets used by the final models: `v1_only`, `v1_score_related`, and `v1_yellow_related`. The service follows the training feature names and ordering from `src/features/feature_registry.py`, reuses the same ELO, odds transform, and rolling-history formulas, computes implied 1X2 and Over/Under 2.5 probabilities from stored odds, and reports debug checks for feature count, missing values, NaN values, and ordering.
