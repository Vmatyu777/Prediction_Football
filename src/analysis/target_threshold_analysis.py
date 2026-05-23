from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "interim" / "matches_top5_2018_2025_clean.csv"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "threshold_distributions"

THRESHOLD_ANALYSIS_PATH = TABLES_DIR / "target_threshold_analysis.csv"
RED_CARDS_DISTRIBUTION_PATH = TABLES_DIR / "red_cards_distribution.csv"

GOALS_THRESHOLDS = [1.5, 2.5, 3.5, 4.5]
CORNERS_THRESHOLDS = [8.5, 9.5, 10.5, 11.5]
YELLOW_CARDS_THRESHOLDS = [2.5, 3.5, 4.5, 5.5]
RED_CARDS_THRESHOLDS = [0.5, 1.5]


def add_season_start_year(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["SeasonStartYear"] = result["MatchDateParsed"].apply(
        lambda value: value.year if value.month >= 7 else value.year - 1
    )
    return result


def summarize_thresholds(
    *,
    data: pd.DataFrame,
    market: str,
    total_column: str,
    thresholds: list[float],
) -> pd.DataFrame:
    rows = []
    total_rows = len(data)
    for threshold in thresholds:
        yes_count = int((data[total_column] > threshold).sum())
        no_count = total_rows - yes_count
        rows.append(
            {
                "market": market,
                "threshold": threshold,
                "target": f"Over{threshold}",
                "total_matches": total_rows,
                "yes_count": yes_count,
                "no_count": no_count,
                "yes_rate": yes_count / total_rows,
                "no_rate": no_count / total_rows,
            }
        )
    return pd.DataFrame(rows)


def build_split_summary(data: pd.DataFrame, total_column: str, threshold: float) -> pd.DataFrame:
    splits = {
        "full": data,
        "train": data[data["SeasonStartYear"].between(2018, 2022)],
        "validation": data[data["SeasonStartYear"] == 2023],
        "test": data[data["SeasonStartYear"] == 2024],
    }
    rows = []
    for split_name, split_data in splits.items():
        total_rows = len(split_data)
        yes_count = int((split_data[total_column] > threshold).sum())
        no_count = total_rows - yes_count
        rows.append(
            {
                "split": split_name,
                "threshold": threshold,
                "target": f"Over{threshold}",
                "total_matches": total_rows,
                "yes_count": yes_count,
                "no_count": no_count,
                "yes_rate": yes_count / total_rows if total_rows else 0.0,
                "no_rate": no_count / total_rows if total_rows else 0.0,
            }
        )
    return pd.DataFrame(rows)


def save_threshold_figure(summary: pd.DataFrame, market: str, output_path: Path) -> None:
    market_summary = summary[summary["market"] == market].copy()
    labels = market_summary["target"].tolist()
    yes_rates = market_summary["yes_rate"].tolist()
    no_rates = market_summary["no_rate"].tolist()
    positions = range(len(labels))

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(positions, yes_rates, label="Yes rate", color="#4c78a8")
    ax.bar(positions, no_rates, bottom=yes_rates, label="No rate", color="#f58518")
    ax.axhline(0.5, color="#333333", linewidth=1, linestyle="--", alpha=0.6)
    ax.set_xticks(list(positions), labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Class rate")
    ax.set_title(f"{market} threshold class balance")
    ax.legend(loc="upper right")

    for index, yes_rate in enumerate(yes_rates):
        ax.text(index, yes_rate / 2, f"{yes_rate:.2f}", ha="center", va="center", color="white")
        ax.text(
            index,
            yes_rate + no_rates[index] / 2,
            f"{no_rates[index]:.2f}",
            ha="center",
            va="center",
            color="black",
        )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_red_cards_figure(red_summary: pd.DataFrame, output_path: Path) -> None:
    full_summary = red_summary[red_summary["split"] == "full"].copy()
    labels = full_summary["target"].tolist()
    yes_rates = full_summary["yes_rate"].tolist()
    no_rates = full_summary["no_rate"].tolist()
    positions = range(len(labels))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(positions, yes_rates, label="Yes rate", color="#e45756")
    ax.bar(positions, no_rates, bottom=yes_rates, label="No rate", color="#72b7b2")
    ax.set_xticks(list(positions), labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Class rate")
    ax.set_title("Red cards target rarity")
    ax.legend(loc="upper right")

    for index, yes_rate in enumerate(yes_rates):
        ax.text(index, yes_rate + 0.03, f"{yes_rate:.3f}", ha="center", va="bottom")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_PATH, parse_dates=["MatchDateParsed"])
    data = add_season_start_year(data)

    data["TotalGoals"] = data["FTHome"] + data["FTAway"]
    data["TotalCorners"] = data["HomeCorners"] + data["AwayCorners"]
    data["TotalYellowCards"] = data["HomeYellow"] + data["AwayYellow"]

    threshold_summary = pd.concat(
        [
            summarize_thresholds(
                data=data,
                market="goals",
                total_column="TotalGoals",
                thresholds=GOALS_THRESHOLDS,
            ),
            summarize_thresholds(
                data=data,
                market="corners",
                total_column="TotalCorners",
                thresholds=CORNERS_THRESHOLDS,
            ),
            summarize_thresholds(
                data=data,
                market="yellow_cards",
                total_column="TotalYellowCards",
                thresholds=YELLOW_CARDS_THRESHOLDS,
            ),
        ],
        ignore_index=True,
    )
    threshold_summary.to_csv(THRESHOLD_ANALYSIS_PATH, index=False)

    for market in ["goals", "corners", "yellow_cards"]:
        save_threshold_figure(
            threshold_summary,
            market,
            FIGURES_DIR / f"{market}_threshold_class_balance.png",
        )

    red_columns = {"HomeRed", "AwayRed"}
    if red_columns.issubset(data.columns):
        data["TotalRedCards"] = data["HomeRed"] + data["AwayRed"]
        red_summary = pd.concat(
            [
                build_split_summary(data, "TotalRedCards", threshold)
                for threshold in RED_CARDS_THRESHOLDS
            ],
            ignore_index=True,
        )
        red_summary["market"] = "red_cards"
        red_summary = red_summary[
            [
                "market",
                "split",
                "threshold",
                "target",
                "total_matches",
                "yes_count",
                "no_count",
                "yes_rate",
                "no_rate",
            ]
        ]
    else:
        red_summary = pd.DataFrame(
            [
                {
                    "market": "red_cards",
                    "split": "full",
                    "threshold": pd.NA,
                    "target": "red_card_columns_missing",
                    "total_matches": len(data),
                    "yes_count": pd.NA,
                    "no_count": pd.NA,
                    "yes_rate": pd.NA,
                    "no_rate": pd.NA,
                }
            ]
        )

    red_summary.to_csv(RED_CARDS_DISTRIBUTION_PATH, index=False)
    if red_columns.issubset(data.columns):
        save_red_cards_figure(red_summary, FIGURES_DIR / "red_cards_class_balance.png")

    print("Target threshold analysis saved to:")
    print(THRESHOLD_ANALYSIS_PATH)
    print(RED_CARDS_DISTRIBUTION_PATH)
    print("Threshold summary:")
    print(threshold_summary.to_string(index=False))
    print("Red cards summary:")
    print(red_summary.to_string(index=False))


if __name__ == "__main__":
    main()
