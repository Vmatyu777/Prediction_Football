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
- Additional tasks such as exact score, other over/under targets, corners, and yellow cards are secondary and should not be expanded unless explicitly requested.
- Current data scope: top-5 European first divisions (`E0`, `D1`, `SP1`, `I1`, `F1`) for seasons 2018/19-2024/25.

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

## Git Hygiene

- Large data and trained models must stay ignored by Git.
- Keep `data/` and root CSV files out of commits.
- Keep `models/` out of commits.
