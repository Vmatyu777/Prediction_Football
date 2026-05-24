# Final App Models

This document describes the local model package prepared for the future backend/API and mobile application.

## Package Policy

- Final model files are local artifacts under `models/final_app/`.
- Model binaries are ignored by Git through the existing `models/` ignore rule.
- Code, documentation, and lightweight metadata are tracked by Git.
- The backend should load model files from `models/final_app/` using the metadata in `configs/final_app_models.json`.

## Final Models

| Task | Model type | Feature set | Input features | Output | Threshold / post-processing | Local model path | Tracked |
|---|---|---|---:|---|---|---|---|
| Outcome | LogisticRegression | `v1_only` | 36 | `H / D / A` | default argmax | `models/final_app/outcome_model.joblib` | No |
| BTTS | LogisticRegression | `v1_only` | 36 | `Yes / No` | threshold `0.50` | `models/final_app/btts_model.joblib` | No |
| Over2.5 | CatBoostClassifier | `v1_only` | 36 | `Yes / No` | threshold `0.50` | `models/final_app/over25_model.cbm` | No |
| Corners Over9.5 | CatBoostClassifier | `v1_only` | 36 | `Yes / No` | threshold `0.50` | `models/final_app/corners_over95_model.cbm` | No |
| Yellow Cards Over3.5 | LogisticRegression | `v1_yellow_related` | 54 | `Yes / No` | threshold `0.50` | `models/final_app/yellow_cards_over35_model.joblib` | No |
| Exact Score Home Goals | Ridge regression | `v1_score_related` | 30 | home goals | round and clip to `0-6` | `models/final_app/exact_score_home_goals_model.joblib` | No |
| Exact Score Away Goals | Ridge regression | `v1_score_related` | 30 | away goals | round and clip to `0-6` | `models/final_app/exact_score_away_goals_model.joblib` | No |

## Final Test Metrics

| Task | Main test metrics |
|---|---|
| Outcome | accuracy `0.5111`, macro F1 `0.4867`, balanced accuracy `0.4861`, draw recall `0.3836` |
| BTTS | accuracy `0.5437`, balanced accuracy `0.5335`, F1 `0.6042`, Yes recall `0.6291`, No recall `0.4379` |
| Over2.5 | accuracy `0.5958`, balanced accuracy `0.5875`, F1 `0.6516`, Yes recall `0.7070`, No recall `0.4681` |
| Corners Over9.5 | accuracy `0.5563`, balanced accuracy `0.5560`, F1 `0.5150`, Yes recall `0.4730`, No recall `0.6390` |
| Yellow Cards Over3.5 | accuracy `0.5512`, balanced accuracy `0.5559`, F1 `0.5731`, Yes recall `0.5244`, No recall `0.5874` |
| Exact Score | exact score accuracy `0.1212`, home goals MAE `0.8948`, away goals MAE `0.8399`, total goals MAE `1.2899` |

## Final Prediction Flow

1. Load final models from `models/final_app/`.
2. Build the required feature set for each task.
3. Produce raw task predictions.
4. Build exact score from the two goal regressors by rounding and clipping predictions to `0-6`.
5. Apply priority-based reconciliation before displaying user-facing predictions.

Final reconciliation priority:

1. Outcome.
2. BTTS.
3. Over2.5.
4. Exact score.

Outcome and BTTS remain the highest-priority prediction layers. Over2.5 is corrected only when it conflicts with `Outcome + BTTS`. Exact score is corrected to the nearest score that satisfies the final higher-priority predictions.
