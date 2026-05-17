from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports" / "tables"

MATCHES_PATH = RAW_DIR / "Matches.csv"
ELO_PATH = RAW_DIR / "EloRatings.csv"

TOP5_DIVISIONS = ["E0", "D1", "SP1", "I1", "F1"]
START_DATE = pd.Timestamp("2018-08-01")
END_DATE = pd.Timestamp("2025-07-01")


def build_schema_report(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "missing_count": df.isna().sum().to_numpy(),
            "missing_percent": (df.isna().mean() * 100).round(2).to_numpy(),
            "unique_count": [df[column].nunique(dropna=True) for column in df.columns],
        }
    )


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    matches = pd.read_csv(MATCHES_PATH, low_memory=False)
    elo = pd.read_csv(ELO_PATH)

    matches["MatchDateParsed"] = pd.to_datetime(matches["MatchDate"], errors="coerce")
    elo["DateParsed"] = pd.to_datetime(elo["date"], errors="coerce")

    matches_schema = build_schema_report(matches.drop(columns=["MatchDateParsed"]))
    elo_schema = build_schema_report(elo.drop(columns=["DateParsed"]))
    matches_schema.to_csv(REPORTS_DIR / "matches_schema.csv", index=False)
    elo_schema.to_csv(REPORTS_DIR / "elo_schema.csv", index=False)

    missing_matches = matches_schema[["column", "missing_count", "missing_percent"]].sort_values(
        "missing_percent", ascending=False
    )
    missing_elo = elo_schema[["column", "missing_count", "missing_percent"]].sort_values(
        "missing_percent", ascending=False
    )
    missing_matches.to_csv(REPORTS_DIR / "matches_missing_values.csv", index=False)
    missing_elo.to_csv(REPORTS_DIR / "elo_missing_values.csv", index=False)

    matches["SeasonStartYear"] = matches["MatchDateParsed"].apply(
        lambda value: value.year if pd.notna(value) and value.month >= 7 else value.year - 1
        if pd.notna(value)
        else pd.NA
    )
    division_season = (
        matches.groupby(["Division", "SeasonStartYear"], dropna=False)
        .size()
        .reset_index(name="matches")
        .sort_values(["Division", "SeasonStartYear"])
    )
    division_season.to_csv(REPORTS_DIR / "division_season_coverage.csv", index=False)

    scope = matches[
        matches["Division"].isin(TOP5_DIVISIONS)
        & (matches["MatchDateParsed"] >= START_DATE)
        & (matches["MatchDateParsed"] < END_DATE)
    ].copy()

    selected_columns = [
        "FTHome",
        "FTAway",
        "FTResult",
        "HomeCorners",
        "AwayCorners",
        "HomeYellow",
        "AwayYellow",
        "HomeElo",
        "AwayElo",
        "OddHome",
        "OddDraw",
        "OddAway",
        "Over25",
        "Under25",
    ]
    scope_missing = (
        (scope[selected_columns].isna().mean() * 100).round(2).rename("missing_percent").reset_index()
    )
    scope_missing = scope_missing.rename(columns={"index": "column"})
    scope_missing.to_csv(REPORTS_DIR / "top5_2018_2025_missing_values.csv", index=False)

    scope_summary = pd.DataFrame(
        [
            {
                "rows": len(scope),
                "date_min": scope["MatchDateParsed"].min().date(),
                "date_max": scope["MatchDateParsed"].max().date(),
                "divisions": ",".join(TOP5_DIVISIONS),
                "unique_teams": pd.concat([scope["HomeTeam"], scope["AwayTeam"]]).nunique(),
                "duplicate_full_rows": int(scope.duplicated().sum()),
                "duplicate_match_keys": int(
                    scope.duplicated(
                        subset=["Division", "MatchDate", "HomeTeam", "AwayTeam"], keep=False
                    ).sum()
                ),
            }
        ]
    )
    scope_summary.to_csv(REPORTS_DIR / "top5_2018_2025_scope_summary.csv", index=False)

    print("Matches shape:", matches.shape)
    print("ELO shape:", elo.shape)
    print("Matches date range:", matches["MatchDateParsed"].min(), matches["MatchDateParsed"].max())
    print("ELO date range:", elo["DateParsed"].min(), elo["DateParsed"].max())
    print("Recommended scope rows:", len(scope))
    print("Recommended scope divisions:")
    print(scope["Division"].value_counts().sort_index().to_string())
    print("Recommended scope missing values:")
    print(scope_missing.to_string(index=False))
    print(f"Reports saved to: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
