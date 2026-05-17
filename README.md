# Prediction Football

Diploma project: a machine learning information system for football match prediction with a mobile application.

Current status: data preparation, cleaning, and v1 feature dataset are implemented. Model training is not implemented yet.

## Current ML Scope

- Main task: match outcome prediction, `Home Win / Draw / Away Win`.
- Additional tasks: BTTS, Over 2.5, corners over/under, yellow cards over/under, and exact score via separate home-goals and away-goals predictions.
- Working data slice: top-5 European first divisions (`E0`, `D1`, `SP1`, `I1`, `F1`) for seasons 2018/19-2024/25.

## Data

Large CSV files are not stored in Git. Locally, they should be placed at:

```text
data/raw/Matches.csv
data/raw/EloRatings.csv
```

Root-level copies of `Matches.csv` and `EloRatings.csv` are also ignored by Git.

## Data Preparation

```bash
python src/data/analyze_data.py
python src/data/clean_data.py
python src/features/build_features.py
```

Local outputs are created in `data/interim/` and `reports/tables/`.
