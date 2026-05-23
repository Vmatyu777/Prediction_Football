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
- Yellow Cards Over3.5 prediction pipeline and controlled LogisticRegression tuning.

Not implemented yet:

- exact score model;
- exact score and other over/under models;
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
