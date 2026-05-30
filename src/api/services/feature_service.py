from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.api.database.models import Match, MatchResult, Odds, TeamEloRating
from src.features.feature_registry import (
    EXACT_SCORE_FEATURE_SETS,
    OUTCOME_FEATURE_SETS,
    YELLOW_CARDS_FEATURE_SETS,
)


LEAGUE_DIVISIONS = {
    "Premier League": "E0",
    "Bundesliga": "D1",
    "La Liga": "SP1",
    "Serie A": "I1",
    "Ligue 1": "F1",
}

RUNTIME_FEATURE_SETS = {
    "v1_only": OUTCOME_FEATURE_SETS["v1_only"],
    "v1_score_related": EXACT_SCORE_FEATURE_SETS["v1_score_related"],
    "v1_yellow_related": YELLOW_CARDS_FEATURE_SETS["v1_yellow_related"],
}

@dataclass
class RuntimeFeatureBundle:
    frames: dict[str, pd.DataFrame]
    debug: dict[str, dict[str, int | bool | list[str]]]


def build_runtime_feature_bundle(db: Session, match: Match) -> RuntimeFeatureBundle:
    row = build_runtime_feature_row(db, match)
    frames = {}
    debug = {}

    for feature_set, feature_names in RUNTIME_FEATURE_SETS.items():
        frame = pd.DataFrame([{feature: row.get(feature, 0.0) for feature in feature_names}])
        missing_features = [feature for feature in feature_names if feature not in row]
        nan_features = frame.columns[frame.isna().any()].tolist()
        frames[feature_set] = frame
        debug[feature_set] = {
            "feature_count": len(feature_names),
            "frame_columns": len(frame.columns),
            "missing_features": missing_features,
            "nan_features": nan_features,
            "ordering_matches_registry": list(frame.columns) == feature_names,
        }

    return RuntimeFeatureBundle(frames=frames, debug=debug)


def build_runtime_feature_row(db: Session, match: Match) -> dict[str, float | int | str]:
    odds = latest_odds(match)
    home_elo = latest_elo(db, match.home_team_id, match.match_date)
    away_elo = latest_elo(db, match.away_team_id, match.match_date)
    home_history = team_history_records(db, match.home_team_id, match.match_date)
    away_history = team_history_records(db, match.away_team_id, match.match_date)
    home_stats = rolling_features(home_history)
    away_stats = rolling_features(away_history)

    odd_home = float(odds.home_win_odds)
    odd_draw = float(odds.draw_odds)
    odd_away = float(odds.away_win_odds)
    over25_odds = float(odds.over25_odds)
    under25_odds = float(odds.under25_odds)
    implied_home = safe_inverse(odd_home)
    implied_draw = safe_inverse(odd_draw)
    implied_away = safe_inverse(odd_away)
    implied_over25 = safe_inverse(over25_odds)
    implied_under25 = safe_inverse(under25_odds)

    row: dict[str, float | int | str] = {
        "Division": LEAGUE_DIVISIONS.get(match.season.league.name, match.season.league.name),
        "HomeTeam": match.home_team.name,
        "AwayTeam": match.away_team.name,
        "SeasonStartYear": match.season.start_date.year,
        "MatchMonth": match.match_date.month,
        "HomeElo": home_elo,
        "AwayElo": away_elo,
        "HomeEloSynced": home_elo,
        "AwayEloSynced": away_elo,
        "EloDiff": home_elo - away_elo,
        "EloMean": (home_elo + away_elo) / 2,
        "OddHome": odd_home,
        "OddDraw": odd_draw,
        "OddAway": odd_away,
        "Over25": over25_odds,
        "Under25": under25_odds,
        "ImpliedHomeWin": implied_home,
        "ImpliedDraw": implied_draw,
        "ImpliedAwayWin": implied_away,
        "ImpliedOver25": implied_over25,
        "ImpliedUnder25": implied_under25,
        "BookmakerMargin1X2": implied_home + implied_draw + implied_away,
    }

    add_side_features(row, "Home", home_stats)
    add_side_features(row, "Away", away_stats)
    add_diff_features(row)
    return row


def latest_odds(match: Match) -> Odds:
    if not match.odds:
        raise ValueError(f"Match has no odds: {match.id}")
    return sorted(match.odds, key=lambda item: item.collected_at, reverse=True)[0]


def latest_elo(db: Session, team_id: int, match_date) -> float:
    rating = (
        db.query(TeamEloRating)
        .filter(TeamEloRating.team_id == team_id, TeamEloRating.rating_date <= match_date.date())
        .order_by(TeamEloRating.rating_date.desc())
        .first()
    )
    return float(rating.elo_value) if rating else 0.0


def team_history_records(db: Session, team_id: int, match_date) -> list[dict[str, float | int]]:
    matches = (
        db.query(Match)
        .join(MatchResult)
        .filter(
            Match.match_date < match_date,
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
        )
        .order_by(Match.match_date.desc(), Match.id.desc())
        .limit(5)
        .all()
    )

    records = []
    for previous_match in matches:
        result = previous_match.result
        is_home = previous_match.home_team_id == team_id
        goals_for = result.home_goals if is_home else result.away_goals
        goals_against = result.away_goals if is_home else result.home_goals
        points = 3 if goals_for > goals_against else 1 if goals_for == goals_against else 0
        corners_for = result.total_corners / 2
        corners_against = result.total_corners / 2
        yellow_for = result.total_yellow_cards / 2
        yellow_against = result.total_yellow_cards / 2
        records.append(
            {
                "GoalsFor": goals_for,
                "GoalsAgainst": goals_against,
                "Points": points,
                "IsBTTS": int(goals_for > 0 and goals_against > 0),
                "IsOver25": int((goals_for + goals_against) > 2.5),
                "IsCornersOver95": int(result.total_corners > 9.5),
                "CornersFor": corners_for,
                "CornersAgainst": corners_against,
                "TotalCorners": result.total_corners,
                "IsYellowCardsOver35": int(result.total_yellow_cards > 3.5),
                "YellowCardsFor": yellow_for,
                "YellowCardsAgainst": yellow_against,
                "TotalYellowCards": result.total_yellow_cards,
            }
        )
    return records


def rolling_features(records: list[dict[str, float | int]]) -> dict[str, float | int]:
    return {
        "MatchesPlayedBefore": len(records),
        "RollingGoalsFor5": mean_value(records, "GoalsFor", 5),
        "RollingGoalsAgainst5": mean_value(records, "GoalsAgainst", 5),
        "RollingPoints3": mean_value(records, "Points", 3),
        "RollingPoints5": mean_value(records, "Points", 5),
        "RollingIsBTTS5": mean_value(records, "IsBTTS", 5),
        "RollingIsOver255": mean_value(records, "IsOver25", 5),
        "RollingIsCornersOver955": mean_value(records, "IsCornersOver95", 5),
        "RollingCornersFor5": mean_value(records, "CornersFor", 5),
        "RollingCornersAgainst5": mean_value(records, "CornersAgainst", 5),
        "RollingTotalCorners5": mean_value(records, "TotalCorners", 5),
        "RollingCornersFor3": mean_value(records, "CornersFor", 3),
        "RollingCornersAgainst3": mean_value(records, "CornersAgainst", 3),
        "RollingIsYellowCardsOver355": mean_value(records, "IsYellowCardsOver35", 5),
        "RollingYellowCardsFor5": mean_value(records, "YellowCardsFor", 5),
        "RollingYellowCardsAgainst5": mean_value(records, "YellowCardsAgainst", 5),
        "RollingTotalYellowCards5": mean_value(records, "TotalYellowCards", 5),
        "RollingYellowCardsFor3": mean_value(records, "YellowCardsFor", 3),
        "RollingYellowCardsAgainst3": mean_value(records, "YellowCardsAgainst", 3),
    }


def add_side_features(row: dict[str, float | int | str], side: str, stats: dict[str, float | int]) -> None:
    row[f"{side}MatchesPlayedBefore"] = stats["MatchesPlayedBefore"]
    row[f"{side}RollingGoalsFor5"] = stats["RollingGoalsFor5"]
    row[f"{side}RollingGoalsAgainst5"] = stats["RollingGoalsAgainst5"]
    row[f"{side}RollingPoints3"] = stats["RollingPoints3"]
    row[f"{side}RollingPoints5"] = stats["RollingPoints5"]
    row[f"{side}RollingBTTSRate5"] = stats["RollingIsBTTS5"]
    row[f"{side}RollingOver25Rate5"] = stats["RollingIsOver255"]
    row[f"{side}RollingCornersOver95Rate5"] = stats["RollingIsCornersOver955"]
    row[f"{side}RollingCornersFor5"] = stats["RollingCornersFor5"]
    row[f"{side}RollingCornersAgainst5"] = stats["RollingCornersAgainst5"]
    row[f"{side}RollingTotalCorners5"] = stats["RollingTotalCorners5"]
    row[f"{side}RollingCornersFor3"] = stats["RollingCornersFor3"]
    row[f"{side}RollingCornersAgainst3"] = stats["RollingCornersAgainst3"]
    row[f"{side}RollingYellowCardsOver35Rate5"] = stats["RollingIsYellowCardsOver355"]
    row[f"{side}RollingYellowCardsFor5"] = stats["RollingYellowCardsFor5"]
    row[f"{side}RollingYellowCardsAgainst5"] = stats["RollingYellowCardsAgainst5"]
    row[f"{side}RollingTotalYellowCards5"] = stats["RollingTotalYellowCards5"]
    row[f"{side}RollingYellowCardsFor3"] = stats["RollingYellowCardsFor3"]
    row[f"{side}RollingYellowCardsAgainst3"] = stats["RollingYellowCardsAgainst3"]


def add_diff_features(row: dict[str, float | int | str]) -> None:
    row["RollingGoalsForDiff5"] = row["HomeRollingGoalsFor5"] - row["AwayRollingGoalsFor5"]
    row["RollingGoalsAgainstDiff5"] = (
        row["HomeRollingGoalsAgainst5"] - row["AwayRollingGoalsAgainst5"]
    )
    row["RollingPointsDiff3"] = row["HomeRollingPoints3"] - row["AwayRollingPoints3"]
    row["RollingPointsDiff5"] = row["HomeRollingPoints5"] - row["AwayRollingPoints5"]
    row["RollingBTTSRateDiff5"] = row["HomeRollingBTTSRate5"] - row["AwayRollingBTTSRate5"]
    row["RollingOver25RateDiff5"] = row["HomeRollingOver25Rate5"] - row["AwayRollingOver25Rate5"]
    row["RollingCornersOver95RateDiff5"] = (
        row["HomeRollingCornersOver95Rate5"] - row["AwayRollingCornersOver95Rate5"]
    )
    row["RollingCornersForDiff5"] = row["HomeRollingCornersFor5"] - row["AwayRollingCornersFor5"]
    row["RollingCornersAgainstDiff5"] = (
        row["HomeRollingCornersAgainst5"] - row["AwayRollingCornersAgainst5"]
    )
    row["RollingTotalCornersDiff5"] = (
        row["HomeRollingTotalCorners5"] - row["AwayRollingTotalCorners5"]
    )
    row["RollingCornersForDiff3"] = row["HomeRollingCornersFor3"] - row["AwayRollingCornersFor3"]
    row["RollingCornersAgainstDiff3"] = (
        row["HomeRollingCornersAgainst3"] - row["AwayRollingCornersAgainst3"]
    )
    row["RollingYellowCardsForDiff5"] = (
        row["HomeRollingYellowCardsFor5"] - row["AwayRollingYellowCardsFor5"]
    )
    row["RollingYellowCardsAgainstDiff5"] = (
        row["HomeRollingYellowCardsAgainst5"] - row["AwayRollingYellowCardsAgainst5"]
    )
    row["RollingYellowCardsOver35RateDiff5"] = (
        row["HomeRollingYellowCardsOver35Rate5"] - row["AwayRollingYellowCardsOver35Rate5"]
    )
    row["RollingTotalYellowCardsDiff5"] = (
        row["HomeRollingTotalYellowCards5"] - row["AwayRollingTotalYellowCards5"]
    )
    row["RollingYellowCardsForDiff3"] = (
        row["HomeRollingYellowCardsFor3"] - row["AwayRollingYellowCardsFor3"]
    )
    row["RollingYellowCardsAgainstDiff3"] = (
        row["HomeRollingYellowCardsAgainst3"] - row["AwayRollingYellowCardsAgainst3"]
    )


def mean_value(records: list[dict[str, float | int]], key: str, limit: int) -> float:
    values = [float(record[key]) for record in records[:limit]]
    return float(sum(values) / len(values)) if values else 0.0


def safe_inverse(value: float) -> float:
    return 1 / value if value > 0 else 0.0
