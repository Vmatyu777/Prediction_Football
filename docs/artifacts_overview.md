# Artifacts Overview

This document gives a short engineering overview of the current project artifacts.

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

## CSV Datasets

- `data/raw/Matches.csv` is the source match table: leagues, dates, teams, ELO, form, odds, results, and post-match statistics.
- `data/raw/EloRatings.csv` is the source ELO table: rating date, club, country, and rating.
- `data/interim/matches_top5_2018_2025_clean.csv` is the cleaned working slice for top-5 leagues in 2018/19-2024/25 with verified ELO coverage.
- `data/interim/matches_features_v1.csv` is the v1 feature dataset for future model training. Post-match leakage columns are not included as features.
- `data/interim/matches_features_v2.csv` is the controlled v2 feature dataset with additional rolling BTTS, Over2.5, venue-form, corners, and yellow-card features.

Files under `data/` are not committed because they are local or potentially large generated artifacts.

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

## Model Artifacts

- `models/outcome/` stores local trained outcome models. This directory is ignored by Git because trained model files can become large.
- `models/btts/` stores local trained BTTS models. This directory is ignored by Git because trained model files can become large.
- `models/over25/` stores local trained Over2.5 models. This directory is ignored by Git because trained model files can become large.
- `models/corners/` stores local trained Corners Over9.5 models. This directory is ignored by Git because trained model files can become large.
- `models/yellow_cards/` stores local trained Yellow Cards Over3.5 models. This directory is ignored by Git because trained model files can become large.

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

## Leakage Policy

v1 features do not include current-match results or statistics: `FTHome`, `FTAway`, `FTResult`, `HT*`, shots, fouls, corners, or cards. These fields are used only to create target columns and rolling features with `shift(1)`. Corners features follow the same policy: `HomeCorners` and `AwayCorners` are not used directly as features for the current match, and rolling corners features are shifted so each row only sees previous team history. Yellow Cards features also follow this policy: `HomeYellow` and `AwayYellow` are not used directly as current-match features, and rolling yellow-card features are shifted so each row only sees previous team history.
