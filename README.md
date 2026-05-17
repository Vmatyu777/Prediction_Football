# Prediction Football

Diploma project: a machine learning information system for football match prediction with a mobile application.

## Current Status

Implemented:

- data analysis and cleaning pipeline;
- V1 and controlled V2 feature engineering;
- outcome prediction pipeline for `Home Win / Draw / Away Win`;
- controlled LogisticRegression tuning for the final outcome baseline.

Not implemented yet:

- BTTS model;
- exact score model;
- over/under models;
- API;
- mobile application.

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
