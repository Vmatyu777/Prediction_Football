from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy.orm import joinedload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.api.database.models import Match, MatchResult, Season  # noqa: E402
from src.api.database.session import SessionLocal  # noqa: E402
from src.api.services.feature_service import build_runtime_feature_bundle  # noqa: E402
from src.api.services.model_registry import load_models  # noqa: E402
from src.api.services.prediction_service import (  # noqa: E402
    BINARY_LABELS,
    predict_binary_from_features,
    predict_exact_score_from_features,
    predict_multiclass_from_features,
    reconcile_prediction,
)


REPORT_DIR = PROJECT_ROOT / "reports" / "tables" / "prediction_quality"
INT_TO_OUTCOME = {0: "A", 1: "D", 2: "H"}


def build_prediction_from_loaded_models(models: dict[str, object], feature_bundle) -> dict[str, str]:
    outcome_result = predict_multiclass_from_features(
        models["outcome"],
        feature_bundle.frames["v1_only"],
    )
    btts_result = predict_binary_from_features(
        "btts",
        models["btts"],
        feature_bundle.frames["v1_only"],
    )
    over25_result = predict_binary_from_features(
        "over25",
        models["over25"],
        feature_bundle.frames["v1_only"],
    )
    corners_result = predict_binary_from_features(
        "corners_over95",
        models["corners_over95"],
        feature_bundle.frames["v1_only"],
    )
    yellow_result = predict_binary_from_features(
        "yellow_cards_over35",
        models["yellow_cards_over35"],
        feature_bundle.frames["v1_yellow_related"],
    )
    raw_home_goals, raw_away_goals = predict_exact_score_from_features(
        models,
        feature_bundle.frames["v1_score_related"],
    )
    reconciled = reconcile_prediction(
        outcome=outcome_result["prediction"],
        btts=btts_result["prediction"],
        over25=over25_result["prediction"],
        home_goals=raw_home_goals,
        away_goals=raw_away_goals,
    )

    return {
        "predicted_outcome": outcome_result["prediction"],
        "predicted_btts": BINARY_LABELS[reconciled["btts"]],
        "predicted_over25": BINARY_LABELS[reconciled["over25"]],
        "predicted_corners_over95": BINARY_LABELS[corners_result["prediction"]],
        "predicted_yellow_cards_over35": BINARY_LABELS[yellow_result["prediction"]],
        "predicted_exact_score": f"{reconciled['home_goals']}:{reconciled['away_goals']}",
        "raw_exact_score": f"{raw_home_goals}:{raw_away_goals}",
    }


def score_prediction(match: Match, prediction: dict[str, str]) -> dict[str, int | str]:
    result = match.result
    if result is None:
        raise ValueError(f"Match has no result: {match.id}")

    actual_outcome = INT_TO_OUTCOME[result.actual_outcome]
    actual_btts = "Yes" if result.home_goals > 0 and result.away_goals > 0 else "No"
    actual_over25 = "Yes" if (result.home_goals + result.away_goals) > 2.5 else "No"
    actual_corners_over95 = "Yes" if result.total_corners > 9.5 else "No"
    actual_yellow_cards_over35 = "Yes" if result.total_yellow_cards > 3.5 else "No"
    actual_exact_score = f"{result.home_goals}:{result.away_goals}"

    outcome_hit = int(prediction["predicted_outcome"] == actual_outcome)
    btts_hit = int(prediction["predicted_btts"] == actual_btts)
    over25_hit = int(prediction["predicted_over25"] == actual_over25)
    corners_hit = int(prediction["predicted_corners_over95"] == actual_corners_over95)
    yellow_hit = int(prediction["predicted_yellow_cards_over35"] == actual_yellow_cards_over35)
    exact_hit = int(prediction["predicted_exact_score"] == actual_exact_score)
    total_hits_without_exact = outcome_hit + btts_hit + over25_hit + corners_hit + yellow_hit

    return {
        "actual_outcome": actual_outcome,
        "actual_btts": actual_btts,
        "actual_over25": actual_over25,
        "actual_corners_over95": actual_corners_over95,
        "actual_yellow_cards_over35": actual_yellow_cards_over35,
        "actual_exact_score": actual_exact_score,
        "outcome_hit": outcome_hit,
        "btts_hit": btts_hit,
        "over25_hit": over25_hit,
        "corners_over95_hit": corners_hit,
        "yellow_cards_over35_hit": yellow_hit,
        "exact_score_hit": exact_hit,
        "total_hits_without_exact_5": total_hits_without_exact,
        "total_hits_6": total_hits_without_exact + exact_hit,
    }


def build_match_scores() -> pd.DataFrame:
    models = load_models()
    rows = []

    with SessionLocal() as db:
        matches = (
            db.query(Match)
            .options(
                joinedload(Match.result),
                joinedload(Match.season).joinedload(Season.league),
                joinedload(Match.home_team),
                joinedload(Match.away_team),
                joinedload(Match.odds),
            )
            .join(MatchResult)
            .order_by(Match.match_date.asc(), Match.id.asc())
            .all()
        )
        total = len(matches)

        for index, match in enumerate(matches, start=1):
            feature_bundle = build_runtime_feature_bundle(db, match)
            prediction = build_prediction_from_loaded_models(models, feature_bundle)
            score = score_prediction(match, prediction)
            rows.append(
                {
                    "match_id": match.id,
                    "match_date": match.match_date,
                    "league": match.season.league.name,
                    "season": match.season.name,
                    "home_team": match.home_team.name,
                    "away_team": match.away_team.name,
                    **prediction,
                    **score,
                }
            )
            if index % 1000 == 0 or index == total:
                print(f"Processed {index}/{total} matches")

    return pd.DataFrame(rows)


def distribution_frame(scores: pd.DataFrame, column: str, output_name: str) -> pd.DataFrame:
    counts = Counter(scores[column])
    return pd.DataFrame(
        {
            output_name: sorted(counts),
            "match_count": [counts[value] for value in sorted(counts)],
        }
    )


def build_summary(scores: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metric": "total_historical_matches", "value": len(scores)},
            {"metric": "average_total_hits_6", "value": scores["total_hits_6"].mean()},
            {
                "metric": "average_total_hits_without_exact_5",
                "value": scores["total_hits_without_exact_5"].mean(),
            },
            {"metric": "exact_score_hits", "value": int(scores["exact_score_hit"].sum())},
            {"metric": "matches_with_4plus_without_exact_5", "value": int((scores["total_hits_without_exact_5"] >= 4).sum())},
            {"metric": "matches_with_5of5_without_exact", "value": int((scores["total_hits_without_exact_5"] == 5).sum())},
        ]
    )


def grouped_quality(scores: pd.DataFrame, group_column: str) -> pd.DataFrame:
    return (
        scores.groupby(group_column)
        .agg(
            match_count=("match_id", "count"),
            average_total_hits_6=("total_hits_6", "mean"),
            average_total_hits_without_exact_5=("total_hits_without_exact_5", "mean"),
            exact_score_hits=("exact_score_hit", "sum"),
            matches_with_4plus_without_exact_5=("total_hits_without_exact_5", lambda values: int((values >= 4).sum())),
            matches_with_5of5_without_exact=("total_hits_without_exact_5", lambda values: int((values == 5).sum())),
        )
        .reset_index()
    )


def save_reports(scores: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    scores.to_csv(REPORT_DIR / "prediction_quality_match_scores.csv", index=False)
    build_summary(scores).to_csv(REPORT_DIR / "prediction_quality_summary.csv", index=False)
    distribution_frame(scores, "total_hits_6", "total_hits_6").to_csv(
        REPORT_DIR / "prediction_quality_distribution_6.csv",
        index=False,
    )
    distribution_frame(scores, "total_hits_without_exact_5", "total_hits_without_exact_5").to_csv(
        REPORT_DIR / "prediction_quality_distribution_5.csv",
        index=False,
    )
    grouped_quality(scores, "league").to_csv(REPORT_DIR / "prediction_quality_by_league.csv", index=False)
    grouped_quality(scores, "season").to_csv(REPORT_DIR / "prediction_quality_by_season.csv", index=False)


def main() -> None:
    scores = build_match_scores()
    save_reports(scores)

    print("Prediction quality analysis completed.")
    print(build_summary(scores).to_string(index=False))
    print("Distribution 0..6:")
    print(distribution_frame(scores, "total_hits_6", "total_hits_6").to_string(index=False))
    print("Distribution 0..5 without exact:")
    print(distribution_frame(scores, "total_hits_without_exact_5", "total_hits_without_exact_5").to_string(index=False))


if __name__ == "__main__":
    main()
