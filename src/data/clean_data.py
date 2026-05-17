from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports" / "tables"

MATCHES_PATH = RAW_DIR / "Matches.csv"
ELO_PATH = RAW_DIR / "EloRatings.csv"
CLEAN_OUTPUT_PATH = INTERIM_DIR / "matches_top5_2018_2025_clean.csv"
QUALITY_REPORT_PATH = REPORTS_DIR / "cleaning_quality_report.csv"

TOP5_DIVISIONS = ["E0", "D1", "SP1", "I1", "F1"]
START_DATE = pd.Timestamp("2018-08-01")
END_DATE = pd.Timestamp("2025-07-01")

REQUIRED_COLUMNS = [
    "Division",
    "MatchDate",
    "HomeTeam",
    "AwayTeam",
    "HomeElo",
    "AwayElo",
    "FTHome",
    "FTAway",
    "FTResult",
    "HomeCorners",
    "AwayCorners",
    "HomeYellow",
    "AwayYellow",
    "OddHome",
    "OddDraw",
    "OddAway",
    "Over25",
    "Under25",
]


def add_synced_elo(matches: pd.DataFrame, elo: pd.DataFrame) -> pd.DataFrame:
    elo = elo.copy()
    elo["EloDate"] = pd.to_datetime(elo["date"], errors="coerce")
    elo["elo"] = pd.to_numeric(elo["elo"], errors="coerce")
    elo = elo.dropna(subset=["EloDate", "club", "elo"]).sort_values(["club", "EloDate"])

    result = matches.copy().reset_index(drop=True)
    result["MatchRowId"] = result.index

    def merge_for_side(side: str) -> pd.DataFrame:
        team_column = f"{side}Team"
        side_frame = result[["MatchRowId", "MatchDateParsed", team_column]].rename(
            columns={team_column: "club"}
        )
        side_frame = side_frame.sort_values(["club", "MatchDateParsed"])
        merged_parts = []

        for club, team_matches in side_frame.groupby("club", sort=False):
            club_elo = elo[elo["club"] == club][["EloDate", "elo"]].sort_values("EloDate")
            if club_elo.empty:
                team_matches = team_matches.copy()
                team_matches[f"{side}EloSynced"] = pd.NA
                merged_parts.append(team_matches[["MatchRowId", f"{side}EloSynced"]])
                continue

            merged = pd.merge_asof(
                team_matches.sort_values("MatchDateParsed"),
                club_elo,
                left_on="MatchDateParsed",
                right_on="EloDate",
                direction="backward",
            )
            merged = merged.rename(columns={"elo": f"{side}EloSynced"})
            merged_parts.append(merged[["MatchRowId", f"{side}EloSynced"]])

        return pd.concat(merged_parts, ignore_index=True)

    for side in ["Home", "Away"]:
        result = result.merge(merge_for_side(side), on="MatchRowId", how="left")

    result = result.drop(columns=["MatchRowId"])
    return result


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    matches = pd.read_csv(MATCHES_PATH, low_memory=False)
    elo = pd.read_csv(ELO_PATH)

    missing_required = sorted(set(REQUIRED_COLUMNS) - set(matches.columns))
    if missing_required:
        raise ValueError(f"Missing required columns in Matches.csv: {missing_required}")

    matches["MatchDateParsed"] = pd.to_datetime(matches["MatchDate"], errors="coerce")
    filtered = matches[
        matches["Division"].isin(TOP5_DIVISIONS)
        & (matches["MatchDateParsed"] >= START_DATE)
        & (matches["MatchDateParsed"] < END_DATE)
    ].copy()

    before_required_drop = len(filtered)
    filtered = filtered.dropna(subset=REQUIRED_COLUMNS + ["MatchDateParsed"]).copy()
    after_required_drop = len(filtered)

    duplicate_full_rows = int(filtered.duplicated().sum())
    duplicate_match_keys = int(
        filtered.duplicated(
            subset=["Division", "MatchDate", "HomeTeam", "AwayTeam"], keep=False
        ).sum()
    )
    filtered = filtered.drop_duplicates().copy()

    filtered = add_synced_elo(filtered, elo)
    filtered["HomeEloSourceDiff"] = filtered["HomeElo"] - filtered["HomeEloSynced"]
    filtered["AwayEloSourceDiff"] = filtered["AwayElo"] - filtered["AwayEloSynced"]

    match_teams = set(filtered["HomeTeam"].dropna()) | set(filtered["AwayTeam"].dropna())
    elo_teams = set(elo["club"].dropna())
    teams_missing_in_elo = sorted(match_teams - elo_teams)

    filtered = filtered.sort_values(["MatchDateParsed", "Division", "HomeTeam", "AwayTeam"]).reset_index(
        drop=True
    )
    filtered.to_csv(CLEAN_OUTPUT_PATH, index=False)

    report = pd.DataFrame(
        [
            {"metric": "rows_after_scope_filter", "value": before_required_drop},
            {"metric": "rows_after_required_drop", "value": after_required_drop},
            {"metric": "full_duplicate_rows_before_drop", "value": duplicate_full_rows},
            {"metric": "duplicate_match_keys", "value": duplicate_match_keys},
            {"metric": "date_parse_missing_after_filter", "value": int(filtered["MatchDateParsed"].isna().sum())},
            {"metric": "unique_teams", "value": len(match_teams)},
            {"metric": "teams_missing_in_elo", "value": len(teams_missing_in_elo)},
            {"metric": "home_synced_elo_missing", "value": int(filtered["HomeEloSynced"].isna().sum())},
            {"metric": "away_synced_elo_missing", "value": int(filtered["AwayEloSynced"].isna().sum())},
            {"metric": "output_rows", "value": len(filtered)},
        ]
    )
    report.to_csv(QUALITY_REPORT_PATH, index=False)

    if teams_missing_in_elo:
        pd.Series(teams_missing_in_elo, name="team").to_csv(
            REPORTS_DIR / "teams_missing_in_elo_top5_2018_2025.csv", index=False
        )

    print(f"Clean data saved to: {CLEAN_OUTPUT_PATH}")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
