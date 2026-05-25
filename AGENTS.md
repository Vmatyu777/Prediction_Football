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
- Current endpoints: `GET /health`, `GET /db/health`, `GET /models`, `POST /predict`.
- Run locally with `uvicorn src.api.main:app --reload`.
- The backend must load tracked metadata from `configs/final_app_models.json` and local model binaries from `models/final_app/`.
- Current feature preparation is a placeholder for API integration; do not retrain models or change final ML configurations from the API layer.
- SQLite-backed feature preparation is not implemented yet.

## SQLite Database Layer

- SQLite backend database code lives under `src/api/database/`.
- Local database file path: `data/app/football.db`.
- The database file is ignored by Git and must not be committed.
- Create tables with `python src/api/database/init_db.py`.
- Seed minimal dictionaries with `python src/api/database/seed_db.py`.
- Seed final deployed model metadata and metrics with `python src/api/database/seed_final_models.py`.
- Load cleaned domain football data with `python src/api/database/load_football_data.py`.
- The loader source is `data/interim/matches_top5_2018_2025_clean.csv`, not the feature matrix CSV files.
- The loader fills countries, leagues, seasons, teams, matches, match results, bookmakers, and odds.
- SQLite stores lightweight metadata for final deployed ML models in `models` and `model_metrics`.
- Users, query history, predictions, and prediction characteristic values are not loaded by the football data loader.

## Git Hygiene

- Large data and trained models must stay ignored by Git.
- Keep `data/` and root CSV files out of commits.
- Keep `models/` out of commits.
