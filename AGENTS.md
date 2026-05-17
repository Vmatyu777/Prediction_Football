# Project Context For AI Agents

## Communication

- User-facing replies must be in Russian.
- Code, documentation, README, commit messages, filenames, variables, and GitHub repository structure must remain in English.

## Project Goal

Build a diploma project: a machine learning information system for football match prediction with a future mobile application.

## Current ML Scope

- Main ML task: match outcome prediction (`Home Win / Draw / Away Win`).
- Additional tasks such as BTTS, exact score, over/under, corners, and yellow cards are secondary and should not be expanded unless explicitly requested.
- Current data scope: top-5 European first divisions (`E0`, `D1`, `SP1`, `I1`, `F1`) for seasons 2018/19-2024/25.

## Modeling Rules

- Use only time-based train/validation/test splits.
- Avoid leakage: do not use current-match results or post-match statistics as features.
- Main metric: Macro F1.
- Always track accuracy, balanced accuracy, and draw recall.
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

## Git Hygiene

- Large data and trained models must stay ignored by Git.
- Keep `data/` and root CSV files out of commits.
- Keep `models/` out of commits.
