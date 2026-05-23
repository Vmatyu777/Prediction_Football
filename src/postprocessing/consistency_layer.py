from __future__ import annotations

from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from catboost import CatBoostClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import V1_FEATURES  # noqa: E402
from src.models.train_outcome import build_time_split  # noqa: E402


FEATURE_DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_features_v2.csv"
EXACT_SCORE_PREDICTIONS_PATH = (
    PROJECT_ROOT / "reports" / "tables" / "exact_score" / "exact_score_final_predictions.csv"
)

OUTCOME_MODEL_PATH = PROJECT_ROOT / "models" / "outcome" / "logistic_regression_controlled_best.joblib"
BTTS_MODEL_PATH = PROJECT_ROOT / "models" / "btts" / "v1_only__logistic_regression.joblib"
OVER25_MODEL_PATH = PROJECT_ROOT / "models" / "over25" / "v1_only__catboost_classifier.cbm"

TABLES_DIR = PROJECT_ROOT / "reports" / "tables" / "consistency"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "consistency"

REQUIRED_INPUTS = [
    FEATURE_DATA_PATH,
    EXACT_SCORE_PREDICTIONS_PATH,
    OUTCOME_MODEL_PATH,
    BTTS_MODEL_PATH,
    OVER25_MODEL_PATH,
]


def check_required_inputs() -> None:
    missing = [str(path) for path in REQUIRED_INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required existing prediction/model artifacts: {missing}")


def normalize_binary_predictions(raw_pred) -> pd.Series:
    return pd.Series(raw_pred.reshape(-1) if hasattr(raw_pred, "reshape") else raw_pred).astype(int)


def outcome_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return pd.Series(
        ["H" if home > away else "A" if away > home else "D" for home, away in zip(home_goals, away_goals)]
    )


def btts_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return ((home_goals > 0) & (away_goals > 0)).astype(int)


def over25_from_scores(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    return ((home_goals + away_goals) > 2.5).astype(int)


def outcome_from_single_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if away_goals > home_goals:
        return "A"
    return "D"


def btts_from_single_score(home_goals: int, away_goals: int) -> int:
    return int(home_goals > 0 and away_goals > 0)


def over25_from_single_score(home_goals: int, away_goals: int) -> int:
    return int((home_goals + away_goals) > 2.5)


def score_satisfies_constraints(
    *,
    home_goals: int,
    away_goals: int,
    outcome: str,
    btts: int | None,
    over25: int | None,
) -> bool:
    if outcome_from_single_score(home_goals, away_goals) != outcome:
        return False
    if btts is not None and btts_from_single_score(home_goals, away_goals) != btts:
        return False
    if over25 is not None and over25_from_single_score(home_goals, away_goals) != over25:
        return False
    return True


def nearest_consistent_score(row: pd.Series) -> dict[str, int | str]:
    original_home = int(row["pred_home_goals"])
    original_away = int(row["pred_away_goals"])
    direct_outcome = str(row["direct_outcome"])
    direct_btts = int(row["direct_btts"])
    direct_over25 = int(row["direct_over25"])

    constraint_attempts = [
        ("outcome_btts_over25", direct_btts, direct_over25),
        ("outcome_btts", direct_btts, None),
    ]

    for applied_constraints, btts_constraint, over25_constraint in constraint_attempts:
        candidates = []
        for home_goals in range(7):
            for away_goals in range(7):
                if not score_satisfies_constraints(
                    home_goals=home_goals,
                    away_goals=away_goals,
                    outcome=direct_outcome,
                    btts=btts_constraint,
                    over25=over25_constraint,
                ):
                    continue
                candidates.append(
                    {
                        "home_goals": home_goals,
                        "away_goals": away_goals,
                        "distance": abs(home_goals - original_home) + abs(away_goals - original_away),
                        "total_distance": abs(
                            (home_goals + away_goals) - (original_home + original_away)
                        ),
                        "score_sum": home_goals + away_goals,
                    }
                )

        if candidates:
            selected = sorted(
                candidates,
                key=lambda candidate: (
                    candidate["distance"],
                    candidate["total_distance"],
                    candidate["score_sum"],
                    candidate["home_goals"],
                    candidate["away_goals"],
                ),
            )[0]
            relaxed_constraints = {
                "outcome_btts_over25": "none",
                "outcome_btts": "over25",
                "outcome_only": "btts_over25",
            }[applied_constraints]
            return {
                "final_home_goals": selected["home_goals"],
                "final_away_goals": selected["away_goals"],
                "final_score_derived_over25": over25_from_single_score(
                    selected["home_goals"],
                    selected["away_goals"],
                ),
                "score_correction_distance": selected["distance"],
                "applied_constraints": applied_constraints,
                "relaxed_constraints": relaxed_constraints,
            }

    raise ValueError(f"Could not find score satisfying outcome and BTTS constraints: {row.to_dict()}")


def build_direct_predictions() -> pd.DataFrame:
    data = pd.read_csv(FEATURE_DATA_PATH, parse_dates=["MatchDateParsed"])
    data = data.sort_values("MatchDateParsed").reset_index(drop=True)
    splits = build_time_split(data)

    outcome_model = joblib.load(OUTCOME_MODEL_PATH)
    btts_model = joblib.load(BTTS_MODEL_PATH)
    over25_model = CatBoostClassifier()
    over25_model.load_model(OVER25_MODEL_PATH)

    rows = []
    for split_name, split_data in splits.items():
        X_split = split_data[V1_FEATURES]
        outcome_pred = pd.Series(outcome_model.predict(X_split)).astype(str)
        btts_pred = normalize_binary_predictions(btts_model.predict(X_split))
        over25_raw_pred = over25_model.predict(X_split)
        over25_pred = normalize_binary_predictions(over25_raw_pred)

        split_predictions = pd.DataFrame(
            {
                "split": split_name,
                "row_id": range(len(split_data)),
                "direct_outcome": outcome_pred,
                "direct_btts": btts_pred,
                "direct_over25": over25_pred,
                "true_outcome": split_data["Target_Outcome"].reset_index(drop=True),
                "true_btts": split_data["Target_BTTS"].reset_index(drop=True),
                "true_over25": split_data["Target_Over25"].reset_index(drop=True),
            }
        )
        rows.append(split_predictions)

    return pd.concat(rows, ignore_index=True)


def build_exact_score_predictions() -> pd.DataFrame:
    exact_predictions = pd.read_csv(EXACT_SCORE_PREDICTIONS_PATH)
    exact_predictions["row_id"] = exact_predictions.groupby("split").cumcount()

    derived_home = exact_predictions["pred_home_goals"].astype(int)
    derived_away = exact_predictions["pred_away_goals"].astype(int)
    exact_predictions["derived_outcome"] = outcome_from_scores(derived_home, derived_away)
    exact_predictions["derived_btts"] = btts_from_scores(derived_home, derived_away)
    exact_predictions["derived_over25"] = over25_from_scores(derived_home, derived_away)

    return exact_predictions[
        [
            "split",
            "row_id",
            "pred_score",
            "pred_home_goals",
            "pred_away_goals",
            "derived_outcome",
            "derived_btts",
            "derived_over25",
            "true_score",
        ]
    ].copy()


def build_consistency_frame() -> pd.DataFrame:
    direct = build_direct_predictions()
    exact = build_exact_score_predictions()
    consistency = direct.merge(exact, on=["split", "row_id"], how="inner")

    consistency["outcome_conflict"] = consistency["direct_outcome"] != consistency["derived_outcome"]
    consistency["btts_conflict"] = consistency["direct_btts"] != consistency["derived_btts"]
    consistency["over25_conflict"] = consistency["direct_over25"] != consistency["derived_over25"]
    consistency["any_conflict"] = (
        consistency["outcome_conflict"]
        | consistency["btts_conflict"]
        | consistency["over25_conflict"]
    )
    consistency["conflict_pattern"] = consistency.apply(build_conflict_pattern, axis=1)
    return consistency


def build_conflict_pattern(row: pd.Series) -> str:
    conflicts = []
    if row["outcome_conflict"]:
        conflicts.append(f"outcome:{row['direct_outcome']}!={row['derived_outcome']}")
    if row["btts_conflict"]:
        conflicts.append(f"btts:{row['direct_btts']}!={row['derived_btts']}")
    if row["over25_conflict"]:
        conflicts.append(f"over25:{row['direct_over25']}!={row['derived_over25']}")
    return "|".join(conflicts) if conflicts else "consistent"


def save_summary(consistency: pd.DataFrame) -> None:
    summary_rows = []
    for split_name, split_data in consistency.groupby("split"):
        total = len(split_data)
        conflict_count = int(split_data["any_conflict"].sum())
        summary_rows.append(
            {
                "split": split_name,
                "rows": total,
                "consistent_rows": total - conflict_count,
                "conflicting_rows": conflict_count,
                "consistency_rate": 1 - conflict_count / total,
                "conflict_rate": conflict_count / total,
                "outcome_conflict_rate": split_data["outcome_conflict"].mean(),
                "btts_conflict_rate": split_data["btts_conflict"].mean(),
                "over25_conflict_rate": split_data["over25_conflict"].mean(),
            }
        )
    pd.DataFrame(summary_rows).to_csv(TABLES_DIR / "consistency_summary.csv", index=False)


def save_conflict_counts(consistency: pd.DataFrame) -> None:
    rows = []
    for split_name, split_data in consistency.groupby("split"):
        for task_name, column in [
            ("outcome", "outcome_conflict"),
            ("btts", "btts_conflict"),
            ("over25", "over25_conflict"),
        ]:
            rows.append(
                {
                    "split": split_name,
                    "task": task_name,
                    "conflict_count": int(split_data[column].sum()),
                    "conflict_rate": split_data[column].mean(),
                }
            )
    pd.DataFrame(rows).to_csv(TABLES_DIR / "conflict_counts_by_task.csv", index=False)


def save_patterns(consistency: pd.DataFrame) -> None:
    pattern_counts = (
        consistency[consistency["any_conflict"]]
        .groupby(["split", "conflict_pattern"])
        .size()
        .reset_index(name="count")
        .sort_values(["split", "count"], ascending=[True, False])
    )
    pattern_counts.to_csv(TABLES_DIR / "inconsistency_patterns.csv", index=False)

    examples = consistency[consistency["any_conflict"]].copy()
    examples = examples[
        [
            "split",
            "row_id",
            "true_score",
            "pred_score",
            "direct_outcome",
            "derived_outcome",
            "direct_btts",
            "derived_btts",
            "direct_over25",
            "derived_over25",
            "conflict_pattern",
        ]
    ].head(100)
    examples.to_csv(TABLES_DIR / "conflict_examples.csv", index=False)


def build_reconciled_predictions(consistency: pd.DataFrame) -> pd.DataFrame:
    reconciled = consistency.copy()

    corrections = reconciled.apply(nearest_consistent_score, axis=1, result_type="expand")
    reconciled = pd.concat([reconciled, corrections], axis=1)

    reconciled["final_score"] = (
        reconciled["final_home_goals"].astype(str) + ":" + reconciled["final_away_goals"].astype(str)
    )
    reconciled["final_derived_outcome"] = outcome_from_scores(
        reconciled["final_home_goals"],
        reconciled["final_away_goals"],
    )
    reconciled["final_derived_btts"] = btts_from_scores(
        reconciled["final_home_goals"],
        reconciled["final_away_goals"],
    )
    reconciled["final_derived_over25"] = over25_from_scores(
        reconciled["final_home_goals"],
        reconciled["final_away_goals"],
    )

    reconciled["final_outcome"] = reconciled["direct_outcome"]
    reconciled["final_btts"] = reconciled["direct_btts"]
    reconciled["final_over25"] = reconciled["direct_over25"].where(
        reconciled["relaxed_constraints"] != "over25",
        reconciled["final_score_derived_over25"],
    )

    reconciled["score_corrected"] = reconciled["pred_score"] != reconciled["final_score"]
    reconciled["outcome_corrected"] = False
    reconciled["btts_corrected"] = False
    reconciled["over25_corrected"] = reconciled["direct_over25"] != reconciled["final_over25"]

    reconciled["final_outcome_conflict"] = (
        reconciled["final_outcome"] != reconciled["final_derived_outcome"]
    )
    reconciled["final_btts_conflict"] = reconciled["final_btts"] != reconciled["final_derived_btts"]
    reconciled["final_over25_conflict"] = (
        reconciled["final_over25"] != reconciled["final_derived_over25"]
    )
    reconciled["final_any_conflict"] = (
        reconciled["final_outcome_conflict"]
        | reconciled["final_btts_conflict"]
        | reconciled["final_over25_conflict"]
    )
    return reconciled


def save_reconciliation_outputs(reconciled: pd.DataFrame) -> None:
    reconciled.to_csv(TABLES_DIR / "reconciled_predictions.csv", index=False)

    rows = []
    for split_name, split_data in reconciled.groupby("split"):
        total = len(split_data)
        before_conflicts = int(split_data["any_conflict"].sum())
        after_conflicts = int(split_data["final_any_conflict"].sum())
        rows.append(
            {
                "split": split_name,
                "rows": total,
                "before_consistency_rate": 1 - before_conflicts / total,
                "after_consistency_rate": 1 - after_conflicts / total,
                "before_conflicting_rows": before_conflicts,
                "after_conflicting_rows": after_conflicts,
                "corrected_rows": int(
                    split_data["score_corrected"].sum()
                ),
                "score_corrections": int(split_data["score_corrected"].sum()),
                "outcome_corrections": 0,
                "btts_corrections": 0,
                "over25_corrections": int(split_data["over25_corrected"].sum()),
                "remaining_outcome_conflicts": int(split_data["final_outcome_conflict"].sum()),
                "remaining_btts_conflicts": int(split_data["final_btts_conflict"].sum()),
                "remaining_over25_conflicts": int(split_data["final_over25_conflict"].sum()),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES_DIR / "reconciliation_summary.csv", index=False)

    corrected_examples = reconciled[reconciled["score_corrected"]].copy()
    corrected_examples = corrected_examples[
        [
            "split",
            "row_id",
            "true_score",
            "pred_score",
            "final_score",
            "direct_outcome",
            "final_outcome",
            "direct_btts",
            "final_btts",
            "direct_over25",
            "final_over25",
            "over25_corrected",
            "score_correction_distance",
            "applied_constraints",
            "relaxed_constraints",
            "conflict_pattern",
        ]
    ].head(100)
    corrected_examples.to_csv(TABLES_DIR / "reconciliation_examples.csv", index=False)

    score_corrections = (
        reconciled[reconciled["score_corrected"]]
        .groupby(["split", "pred_score", "final_score", "applied_constraints", "relaxed_constraints"])
        .size()
        .reset_index(name="count")
        .sort_values(["split", "count"], ascending=[True, False])
    )
    score_corrections.to_csv(TABLES_DIR / "score_correction_patterns.csv", index=False)

    over25_corrections = (
        reconciled[reconciled["over25_corrected"]]
        .groupby(["split", "direct_over25", "final_over25", "pred_score", "final_score"])
        .size()
        .reset_index(name="count")
        .sort_values(["split", "count"], ascending=[True, False])
    )
    over25_corrections.to_csv(TABLES_DIR / "over25_correction_patterns.csv", index=False)


def save_figures() -> None:
    summary = pd.read_csv(TABLES_DIR / "consistency_summary.csv")
    counts = pd.read_csv(TABLES_DIR / "conflict_counts_by_task.csv")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(summary["split"], summary["consistency_rate"], color="#4c78a8")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Consistency rate")
    ax.set_title("Prediction consistency by split")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "consistency_rate_by_split.png", dpi=160)
    plt.close(fig)

    pivot = counts.pivot(index="split", columns="task", values="conflict_count")
    ax = pivot.plot(kind="bar", figsize=(8, 4.5))
    ax.set_xlabel("Split")
    ax.set_ylabel("Conflict count")
    ax.set_title("Conflict counts by task")
    ax.legend(loc="upper right")
    ax.figure.tight_layout()
    ax.figure.savefig(FIGURES_DIR / "conflict_counts_by_task.png", dpi=160)
    plt.close(ax.figure)

    reconciliation = pd.read_csv(TABLES_DIR / "reconciliation_summary.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    positions = range(len(reconciliation))
    width = 0.36
    ax.bar(
        [position - width / 2 for position in positions],
        reconciliation["before_consistency_rate"],
        width=width,
        label="Before",
        color="#e45756",
    )
    ax.bar(
        [position + width / 2 for position in positions],
        reconciliation["after_consistency_rate"],
        width=width,
        label="After",
        color="#54a24b",
    )
    ax.set_xticks(list(positions), reconciliation["split"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Consistency rate")
    ax.set_title("Consistency before and after reconciliation")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "reconciliation_before_after.png", dpi=160)
    plt.close(fig)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    check_required_inputs()
    consistency = build_consistency_frame()
    consistency.to_csv(TABLES_DIR / "consistency_predictions.csv", index=False)
    save_summary(consistency)
    save_conflict_counts(consistency)
    save_patterns(consistency)
    reconciled = build_reconciled_predictions(consistency)
    save_reconciliation_outputs(reconciled)
    save_figures()

    print("Consistency layer analysis completed.")
    print("Summary:")
    print(pd.read_csv(TABLES_DIR / "consistency_summary.csv").to_string(index=False))
    print("Conflict counts:")
    print(pd.read_csv(TABLES_DIR / "conflict_counts_by_task.csv").to_string(index=False))
    print("Most common inconsistency patterns:")
    print(pd.read_csv(TABLES_DIR / "inconsistency_patterns.csv").head(20).to_string(index=False))
    print("Reconciliation summary:")
    print(pd.read_csv(TABLES_DIR / "reconciliation_summary.csv").to_string(index=False))
    print("Most common score corrections:")
    print(pd.read_csv(TABLES_DIR / "score_correction_patterns.csv").head(20).to_string(index=False))


if __name__ == "__main__":
    main()
