from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.features.feature_registry import (  # noqa: E402
    CORNERS_RELATED_ROLLING_FEATURES,
    TARGET_COLUMNS,
    V1_FEATURES,
    V2_FEATURES,
    YELLOW_CARDS_RELATED_ROLLING_FEATURES,
)


RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports" / "tables"

RAW_MATCHES_PATH = RAW_DIR / "Matches.csv"
CLEAN_INPUT_PATH = INTERIM_DIR / "matches_top5_2018_2025_clean.csv"
FEATURE_V1_OUTPUT_PATH = INTERIM_DIR / "matches_features_v1.csv"
FEATURE_V2_OUTPUT_PATH = INTERIM_DIR / "matches_features_v2.csv"
FEATURE_V1_REPORT_PATH = REPORTS_DIR / "features_v1_report.csv"
FEATURE_V2_REPORT_PATH = REPORTS_DIR / "features_v2_report.csv"

CORNERS_OVER_THRESHOLD = 9.5
YELLOW_CARDS_OVER_THRESHOLD = 3.5
TOP5_DIVISIONS = ["E0", "D1", "SP1", "I1", "F1"]


def safe_inverse(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return 1 / numeric.where(numeric > 0)


def make_match_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["Division"].astype(str)
        + "|"
        + df["MatchDate"].astype(str)
        + "|"
        + df["HomeTeam"].astype(str)
        + "|"
        + df["AwayTeam"].astype(str)
    )


def add_rolling_features(matches: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    base = matches.reset_index(drop=True).copy()
    base["MatchKey"] = make_match_key(base)

    history = history.copy().reset_index(drop=True)
    history["HistoryRowId"] = history.index
    history["MatchKey"] = make_match_key(history)

    home_records = pd.DataFrame(
        {
            "HistoryRowId": history["HistoryRowId"],
            "MatchKey": history["MatchKey"],
            "MatchSide": "Home",
            "MatchDateParsed": history["MatchDateParsed"],
            "Team": history["HomeTeam"],
            "GoalsFor": history["FTHome"],
            "GoalsAgainst": history["FTAway"],
            "Points": history["FTResult"].map({"H": 3, "D": 1, "A": 0}),
            "IsBTTS": ((history["FTHome"] > 0) & (history["FTAway"] > 0)).astype(int),
            "IsOver25": ((history["FTHome"] + history["FTAway"]) > 2.5).astype(int),
            "IsCornersOver95": (
                (history["HomeCorners"] + history["AwayCorners"]) > CORNERS_OVER_THRESHOLD
            ).astype(int),
            "CornersFor": history["HomeCorners"],
            "CornersAgainst": history["AwayCorners"],
            "TotalCorners": history["HomeCorners"] + history["AwayCorners"],
            "IsYellowCardsOver35": (
                (history["HomeYellow"] + history["AwayYellow"]) > YELLOW_CARDS_OVER_THRESHOLD
            ).astype(int),
            "YellowCardsFor": history["HomeYellow"],
            "YellowCardsAgainst": history["AwayYellow"],
            "TotalYellowCards": history["HomeYellow"] + history["AwayYellow"],
        }
    )
    away_records = pd.DataFrame(
        {
            "HistoryRowId": history["HistoryRowId"],
            "MatchKey": history["MatchKey"],
            "MatchSide": "Away",
            "MatchDateParsed": history["MatchDateParsed"],
            "Team": history["AwayTeam"],
            "GoalsFor": history["FTAway"],
            "GoalsAgainst": history["FTHome"],
            "Points": history["FTResult"].map({"H": 0, "D": 1, "A": 3}),
            "IsBTTS": ((history["FTHome"] > 0) & (history["FTAway"] > 0)).astype(int),
            "IsOver25": ((history["FTHome"] + history["FTAway"]) > 2.5).astype(int),
            "IsCornersOver95": (
                (history["HomeCorners"] + history["AwayCorners"]) > CORNERS_OVER_THRESHOLD
            ).astype(int),
            "CornersFor": history["AwayCorners"],
            "CornersAgainst": history["HomeCorners"],
            "TotalCorners": history["HomeCorners"] + history["AwayCorners"],
            "IsYellowCardsOver35": (
                (history["HomeYellow"] + history["AwayYellow"]) > YELLOW_CARDS_OVER_THRESHOLD
            ).astype(int),
            "YellowCardsFor": history["AwayYellow"],
            "YellowCardsAgainst": history["HomeYellow"],
            "TotalYellowCards": history["HomeYellow"] + history["AwayYellow"],
        }
    )

    team_history = pd.concat([home_records, away_records], ignore_index=True)
    team_history = team_history.sort_values(
        ["Team", "MatchDateParsed", "HistoryRowId", "MatchSide"]
    ).reset_index(drop=True)

    grouped = team_history.groupby("Team", group_keys=False)
    team_history["MatchesPlayedBefore"] = grouped.cumcount()
    for column in [
        "GoalsFor",
        "GoalsAgainst",
        "Points",
        "IsBTTS",
        "IsOver25",
        "IsCornersOver95",
        "CornersFor",
        "CornersAgainst",
        "TotalCorners",
        "IsYellowCardsOver35",
        "YellowCardsFor",
        "YellowCardsAgainst",
        "TotalYellowCards",
    ]:
        shifted = grouped[column].shift(1)
        team_history[f"Rolling{column}3"] = shifted.groupby(team_history["Team"]).rolling(
            3, min_periods=1
        ).mean().reset_index(level=0, drop=True)
        team_history[f"Rolling{column}5"] = shifted.groupby(team_history["Team"]).rolling(
            5, min_periods=1
        ).mean().reset_index(level=0, drop=True)

    venue_grouped = team_history.groupby(["Team", "MatchSide"], group_keys=False)
    for column in ["GoalsFor", "GoalsAgainst", "Points"]:
        shifted = venue_grouped[column].shift(1)
        team_history[f"VenueRolling{column}5"] = shifted.groupby(
            [team_history["Team"], team_history["MatchSide"]]
        ).rolling(5, min_periods=1).mean().reset_index(level=[0, 1], drop=True)

    rolling_columns = [
        "MatchKey",
        "MatchSide",
        "MatchesPlayedBefore",
        "RollingGoalsFor5",
        "RollingGoalsAgainst5",
        "RollingPoints3",
        "RollingPoints5",
        "RollingIsBTTS5",
        "RollingIsOver255",
        "RollingIsCornersOver955",
        "RollingCornersFor5",
        "RollingCornersAgainst5",
        "RollingTotalCorners5",
        "RollingCornersFor3",
        "RollingCornersAgainst3",
        "RollingIsYellowCardsOver355",
        "RollingYellowCardsFor5",
        "RollingYellowCardsAgainst5",
        "RollingTotalYellowCards5",
        "RollingYellowCardsFor3",
        "RollingYellowCardsAgainst3",
        "VenueRollingGoalsFor5",
        "VenueRollingGoalsAgainst5",
        "VenueRollingPoints5",
    ]
    home_rolling = team_history.loc[team_history["MatchSide"] == "Home", rolling_columns].rename(
        columns={
            "MatchesPlayedBefore": "HomeMatchesPlayedBefore",
            "RollingGoalsFor5": "HomeRollingGoalsFor5",
            "RollingGoalsAgainst5": "HomeRollingGoalsAgainst5",
            "RollingPoints3": "HomeRollingPoints3",
            "RollingPoints5": "HomeRollingPoints5",
            "RollingIsBTTS5": "HomeRollingBTTSRate5",
            "RollingIsOver255": "HomeRollingOver25Rate5",
            "RollingIsCornersOver955": "HomeRollingCornersOver95Rate5",
            "RollingCornersFor5": "HomeRollingCornersFor5",
            "RollingCornersAgainst5": "HomeRollingCornersAgainst5",
            "RollingTotalCorners5": "HomeRollingTotalCorners5",
            "RollingCornersFor3": "HomeRollingCornersFor3",
            "RollingCornersAgainst3": "HomeRollingCornersAgainst3",
            "RollingIsYellowCardsOver355": "HomeRollingYellowCardsOver35Rate5",
            "RollingYellowCardsFor5": "HomeRollingYellowCardsFor5",
            "RollingYellowCardsAgainst5": "HomeRollingYellowCardsAgainst5",
            "RollingTotalYellowCards5": "HomeRollingTotalYellowCards5",
            "RollingYellowCardsFor3": "HomeRollingYellowCardsFor3",
            "RollingYellowCardsAgainst3": "HomeRollingYellowCardsAgainst3",
            "VenueRollingGoalsFor5": "HomeOnlyRollingGoalsFor5",
            "VenueRollingGoalsAgainst5": "HomeOnlyRollingGoalsAgainst5",
            "VenueRollingPoints5": "HomeOnlyRollingPoints5",
        }
    )
    away_rolling = team_history.loc[team_history["MatchSide"] == "Away", rolling_columns].rename(
        columns={
            "MatchesPlayedBefore": "AwayMatchesPlayedBefore",
            "RollingGoalsFor5": "AwayRollingGoalsFor5",
            "RollingGoalsAgainst5": "AwayRollingGoalsAgainst5",
            "RollingPoints3": "AwayRollingPoints3",
            "RollingPoints5": "AwayRollingPoints5",
            "RollingIsBTTS5": "AwayRollingBTTSRate5",
            "RollingIsOver255": "AwayRollingOver25Rate5",
            "RollingIsCornersOver955": "AwayRollingCornersOver95Rate5",
            "RollingCornersFor5": "AwayRollingCornersFor5",
            "RollingCornersAgainst5": "AwayRollingCornersAgainst5",
            "RollingTotalCorners5": "AwayRollingTotalCorners5",
            "RollingCornersFor3": "AwayRollingCornersFor3",
            "RollingCornersAgainst3": "AwayRollingCornersAgainst3",
            "RollingIsYellowCardsOver355": "AwayRollingYellowCardsOver35Rate5",
            "RollingYellowCardsFor5": "AwayRollingYellowCardsFor5",
            "RollingYellowCardsAgainst5": "AwayRollingYellowCardsAgainst5",
            "RollingTotalYellowCards5": "AwayRollingTotalYellowCards5",
            "RollingYellowCardsFor3": "AwayRollingYellowCardsFor3",
            "RollingYellowCardsAgainst3": "AwayRollingYellowCardsAgainst3",
            "VenueRollingGoalsFor5": "AwayOnlyRollingGoalsFor5",
            "VenueRollingGoalsAgainst5": "AwayOnlyRollingGoalsAgainst5",
            "VenueRollingPoints5": "AwayOnlyRollingPoints5",
        }
    )
    home_rolling = home_rolling.drop(columns=["MatchSide"])
    away_rolling = away_rolling.drop(columns=["MatchSide"])

    base = base.merge(home_rolling, on="MatchKey", how="left")
    base = base.merge(away_rolling, on="MatchKey", how="left")
    base = base.drop(columns=["MatchKey"])

    rolling_fill_columns = [
        "HomeRollingGoalsFor5",
        "HomeRollingGoalsAgainst5",
        "AwayRollingGoalsFor5",
        "AwayRollingGoalsAgainst5",
        "HomeRollingPoints3",
        "HomeRollingPoints5",
        "AwayRollingPoints3",
        "AwayRollingPoints5",
        "HomeRollingBTTSRate5",
        "AwayRollingBTTSRate5",
        "HomeRollingOver25Rate5",
        "AwayRollingOver25Rate5",
        "HomeRollingCornersOver95Rate5",
        "AwayRollingCornersOver95Rate5",
        "HomeRollingCornersFor5",
        "HomeRollingCornersAgainst5",
        "AwayRollingCornersFor5",
        "AwayRollingCornersAgainst5",
        "HomeRollingTotalCorners5",
        "AwayRollingTotalCorners5",
        "HomeRollingCornersFor3",
        "HomeRollingCornersAgainst3",
        "AwayRollingCornersFor3",
        "AwayRollingCornersAgainst3",
        "HomeRollingYellowCardsFor5",
        "HomeRollingYellowCardsAgainst5",
        "AwayRollingYellowCardsFor5",
        "AwayRollingYellowCardsAgainst5",
        "HomeRollingYellowCardsOver35Rate5",
        "AwayRollingYellowCardsOver35Rate5",
        "HomeRollingTotalYellowCards5",
        "AwayRollingTotalYellowCards5",
        "HomeRollingYellowCardsFor3",
        "HomeRollingYellowCardsAgainst3",
        "AwayRollingYellowCardsFor3",
        "AwayRollingYellowCardsAgainst3",
        "HomeOnlyRollingPoints5",
        "HomeOnlyRollingGoalsFor5",
        "HomeOnlyRollingGoalsAgainst5",
        "AwayOnlyRollingPoints5",
        "AwayOnlyRollingGoalsFor5",
        "AwayOnlyRollingGoalsAgainst5",
    ]
    base[rolling_fill_columns] = base[rolling_fill_columns].fillna(0)

    base["RollingGoalsForDiff5"] = base["HomeRollingGoalsFor5"] - base["AwayRollingGoalsFor5"]
    base["RollingGoalsAgainstDiff5"] = (
        base["HomeRollingGoalsAgainst5"] - base["AwayRollingGoalsAgainst5"]
    )
    base["RollingPointsDiff3"] = base["HomeRollingPoints3"] - base["AwayRollingPoints3"]
    base["RollingPointsDiff5"] = base["HomeRollingPoints5"] - base["AwayRollingPoints5"]
    base["RollingBTTSRateDiff5"] = base["HomeRollingBTTSRate5"] - base["AwayRollingBTTSRate5"]
    base["RollingOver25RateDiff5"] = base["HomeRollingOver25Rate5"] - base["AwayRollingOver25Rate5"]
    base["RollingCornersOver95RateDiff5"] = (
        base["HomeRollingCornersOver95Rate5"] - base["AwayRollingCornersOver95Rate5"]
    )
    base["RollingCornersForDiff5"] = base["HomeRollingCornersFor5"] - base["AwayRollingCornersFor5"]
    base["RollingCornersAgainstDiff5"] = (
        base["HomeRollingCornersAgainst5"] - base["AwayRollingCornersAgainst5"]
    )
    base["RollingTotalCornersDiff5"] = (
        base["HomeRollingTotalCorners5"] - base["AwayRollingTotalCorners5"]
    )
    base["RollingCornersForDiff3"] = base["HomeRollingCornersFor3"] - base["AwayRollingCornersFor3"]
    base["RollingCornersAgainstDiff3"] = (
        base["HomeRollingCornersAgainst3"] - base["AwayRollingCornersAgainst3"]
    )
    base["RollingYellowCardsForDiff5"] = (
        base["HomeRollingYellowCardsFor5"] - base["AwayRollingYellowCardsFor5"]
    )
    base["RollingYellowCardsAgainstDiff5"] = (
        base["HomeRollingYellowCardsAgainst5"] - base["AwayRollingYellowCardsAgainst5"]
    )
    base["RollingYellowCardsOver35RateDiff5"] = (
        base["HomeRollingYellowCardsOver35Rate5"] - base["AwayRollingYellowCardsOver35Rate5"]
    )
    base["RollingTotalYellowCardsDiff5"] = (
        base["HomeRollingTotalYellowCards5"] - base["AwayRollingTotalYellowCards5"]
    )
    base["RollingYellowCardsForDiff3"] = (
        base["HomeRollingYellowCardsFor3"] - base["AwayRollingYellowCardsFor3"]
    )
    base["RollingYellowCardsAgainstDiff3"] = (
        base["HomeRollingYellowCardsAgainst3"] - base["AwayRollingYellowCardsAgainst3"]
    )
    base["VenueRollingPointsDiff5"] = base["HomeOnlyRollingPoints5"] - base["AwayOnlyRollingPoints5"]
    base["VenueRollingGoalsForDiff5"] = (
        base["HomeOnlyRollingGoalsFor5"] - base["AwayOnlyRollingGoalsFor5"]
    )
    base["VenueRollingGoalsAgainstDiff5"] = (
        base["HomeOnlyRollingGoalsAgainst5"] - base["AwayOnlyRollingGoalsAgainst5"]
    )
    return base


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    matches = pd.read_csv(CLEAN_INPUT_PATH, low_memory=False)
    matches["MatchDateParsed"] = pd.to_datetime(matches["MatchDateParsed"], errors="coerce")

    raw_matches = pd.read_csv(RAW_MATCHES_PATH, low_memory=False)
    raw_matches["MatchDateParsed"] = pd.to_datetime(raw_matches["MatchDate"], errors="coerce")
    history = raw_matches[
        raw_matches["Division"].isin(TOP5_DIVISIONS)
        & (raw_matches["MatchDateParsed"] <= matches["MatchDateParsed"].max())
    ].dropna(
        subset=[
            "Division",
            "MatchDate",
            "HomeTeam",
            "AwayTeam",
            "FTHome",
            "FTAway",
            "FTResult",
            "MatchDateParsed",
        ]
    )

    features = add_rolling_features(matches, history)

    features["SeasonStartYear"] = features["MatchDateParsed"].apply(
        lambda value: value.year if value.month >= 7 else value.year - 1
    )
    features["MatchMonth"] = features["MatchDateParsed"].dt.month

    features["EloDiff"] = features["HomeElo"] - features["AwayElo"]
    features["EloMean"] = (features["HomeElo"] + features["AwayElo"]) / 2

    features["ImpliedHomeWin"] = safe_inverse(features["OddHome"])
    features["ImpliedDraw"] = safe_inverse(features["OddDraw"])
    features["ImpliedAwayWin"] = safe_inverse(features["OddAway"])
    features["ImpliedOver25"] = safe_inverse(features["Over25"])
    features["ImpliedUnder25"] = safe_inverse(features["Under25"])
    features["BookmakerMargin1X2"] = (
        features["ImpliedHomeWin"] + features["ImpliedDraw"] + features["ImpliedAwayWin"]
    )

    total_goals = features["FTHome"] + features["FTAway"]
    total_corners = features["HomeCorners"] + features["AwayCorners"]
    total_yellow_cards = features["HomeYellow"] + features["AwayYellow"]

    features["Target_Outcome"] = features["FTResult"]
    features["Target_BTTS"] = ((features["FTHome"] > 0) & (features["FTAway"] > 0)).astype(int)
    features["Target_Over25"] = (total_goals > 2.5).astype(int)
    features["Target_Corners_Over95"] = (total_corners > CORNERS_OVER_THRESHOLD).astype(int)
    features["Target_YellowCards_Over35"] = (total_yellow_cards > YELLOW_CARDS_OVER_THRESHOLD).astype(
        int
    )
    features["Target_HomeGoals"] = features["FTHome"].astype(int)
    features["Target_AwayGoals"] = features["FTAway"].astype(int)

    base_columns = ["MatchDate", "MatchDateParsed"]
    v2_columns = V2_FEATURES + [
        feature for feature in CORNERS_RELATED_ROLLING_FEATURES if feature not in V2_FEATURES
    ] + [
        feature for feature in YELLOW_CARDS_RELATED_ROLLING_FEATURES if feature not in V2_FEATURES
    ]
    v1_output = features[base_columns + V1_FEATURES + TARGET_COLUMNS].copy()
    v2_output = features[base_columns + v2_columns + TARGET_COLUMNS].copy()
    v1_output.to_csv(FEATURE_V1_OUTPUT_PATH, index=False)
    v2_output.to_csv(FEATURE_V2_OUTPUT_PATH, index=False)

    v1_report = pd.DataFrame(
        [
            {"metric": "rows", "value": len(v1_output)},
            {"metric": "columns", "value": len(v1_output.columns)},
            {"metric": "feature_columns", "value": len(V1_FEATURES)},
            {"metric": "target_columns", "value": len(TARGET_COLUMNS)},
            {"metric": "missing_cells", "value": int(v1_output.isna().sum().sum())},
            {
                "metric": "rows_with_any_missing",
                "value": int(v1_output.isna().any(axis=1).sum()),
            },
            {"metric": "historical_rows_used_for_rolling", "value": len(history)},
            {
                "metric": "rows_with_home_no_history",
                "value": int((v1_output["HomeMatchesPlayedBefore"] == 0).sum()),
            },
            {
                "metric": "rows_with_away_no_history",
                "value": int((v1_output["AwayMatchesPlayedBefore"] == 0).sum()),
            },
        ]
    )
    v1_report.to_csv(FEATURE_V1_REPORT_PATH, index=False)

    v2_report = pd.DataFrame(
        [
            {"metric": "rows", "value": len(v2_output)},
            {"metric": "columns", "value": len(v2_output.columns)},
            {"metric": "feature_columns", "value": len(v2_columns)},
            {"metric": "target_columns", "value": len(TARGET_COLUMNS)},
            {"metric": "missing_cells", "value": int(v2_output.isna().sum().sum())},
            {
                "metric": "rows_with_any_missing",
                "value": int(v2_output.isna().any(axis=1).sum()),
            },
            {"metric": "historical_rows_used_for_rolling", "value": len(history)},
            {
                "metric": "rows_with_home_no_history",
                "value": int((v2_output["HomeMatchesPlayedBefore"] == 0).sum()),
            },
            {
                "metric": "rows_with_away_no_history",
                "value": int((v2_output["AwayMatchesPlayedBefore"] == 0).sum()),
            },
        ]
    )
    v2_report.to_csv(FEATURE_V2_REPORT_PATH, index=False)

    print(f"V1 feature data saved to: {FEATURE_V1_OUTPUT_PATH}")
    print(v1_report.to_string(index=False))
    print(f"V2 feature data saved to: {FEATURE_V2_OUTPUT_PATH}")
    print(v2_report.to_string(index=False))
    print("V2 feature columns:")
    print("\n".join(V2_FEATURES))
    print("Target columns:")
    print("\n".join(TARGET_COLUMNS))


if __name__ == "__main__":
    main()
