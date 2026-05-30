from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from src.api.database.models import League, Match, MatchResult, Odds, Season
from src.api.schemas import (
    LeagueResponse,
    MatchDetailResponse,
    MatchResultResponse,
    MatchSummaryResponse,
    OddsResponse,
    SeasonResponse,
    TeamResponse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREDICTION_QUALITY_MATCH_SCORES_PATH = (
    PROJECT_ROOT / "reports" / "tables" / "prediction_quality" / "prediction_quality_match_scores.csv"
)


def list_matches(
    db: Session,
    *,
    league: str | None = None,
    season: str | None = None,
    match_date: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MatchSummaryResponse]:
    query = db.query(Match).join(Match.season).join(Season.league)

    if league:
        query = query.filter(League.name == league)
    if season:
        query = query.filter(Season.name == season)
    if match_date:
        start = datetime.combine(match_date, datetime.min.time())
        end = datetime.combine(match_date, datetime.max.time())
        query = query.filter(Match.match_date >= start, Match.match_date <= end)

    matches = query.order_by(Match.match_date.desc(), Match.id.desc()).offset(offset).limit(limit).all()
    return [build_match_summary(match) for match in matches]


def get_match_detail(db: Session, match_id: int) -> MatchDetailResponse | None:
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return None
    return build_match_detail(match)


def list_upcoming_matches(db: Session, *, limit: int = 50, offset: int = 0) -> list[MatchSummaryResponse]:
    matches = (
        db.query(Match)
        .filter(~Match.result.has())
        .order_by(Match.match_date.asc(), Match.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [build_match_summary(match) for match in matches]


def list_recent_matches(db: Session, *, limit: int = 50, offset: int = 0) -> list[MatchSummaryResponse]:
    matches = (
        db.query(Match)
        .join(MatchResult)
        .order_by(Match.match_date.desc(), Match.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [build_match_summary(match) for match in matches]


def list_sampled_recent_matches(db: Session, *, per_league_season: int = 5) -> list[MatchSummaryResponse]:
    seasons = (
        db.query(Season)
        .join(Season.league)
        .order_by(Season.name.desc(), League.name.asc())
        .all()
    )
    sampled_matches = []

    for season in seasons:
        matches = (
            db.query(Match)
            .join(MatchResult)
            .filter(Match.season_id == season.id)
            .order_by(Match.match_date.desc(), Match.id.desc())
            .limit(per_league_season)
            .all()
        )
        sampled_matches.extend(matches)

    sampled_matches.sort(
        key=lambda match: (
            match.match_date,
            _sort_text_desc(match.season.league.name),
            _sort_text_desc(match.home_team.name),
            match.id,
        ),
        reverse=True,
    )
    return [build_match_summary(match) for match in sampled_matches]


def list_showcase_matches(db: Session, *, per_league_season: int = 5) -> list[MatchSummaryResponse]:
    showcase_ids = select_showcase_match_ids(per_league_season=per_league_season)
    if not showcase_ids:
        return []

    matches = db.query(Match).filter(Match.id.in_(showcase_ids)).all()
    match_by_id = {match.id: match for match in matches}
    ordered_matches = [match_by_id[match_id] for match_id in showcase_ids if match_id in match_by_id]
    return [build_match_summary(match) for match in ordered_matches]


def select_showcase_match_ids(*, per_league_season: int = 5) -> list[int]:
    if not PREDICTION_QUALITY_MATCH_SCORES_PATH.exists():
        raise FileNotFoundError(
            "Prediction quality report not found. Run "
            "`python src/analysis/prediction_quality_analysis.py` first."
        )

    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = {}
    with PREDICTION_QUALITY_MATCH_SCORES_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row["league"], row["season"])
            grouped_rows.setdefault(key, []).append(row)

    selected_rows = []
    for group_rows in grouped_rows.values():
        selected_rows.extend(
            sorted(
                group_rows,
                key=lambda row: (
                    int(row["total_hits_without_exact_5"]),
                    parse_report_datetime(row["match_date"]),
                    int(row["match_id"]),
                ),
                reverse=True,
            )[:per_league_season]
        )

    selected_rows.sort(
        key=lambda row: (
            row["season"],
            row["league"],
            int(row["total_hits_without_exact_5"]),
            parse_report_datetime(row["match_date"]),
            int(row["match_id"]),
        ),
        reverse=True,
    )
    return [int(row["match_id"]) for row in selected_rows]


def parse_report_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _sort_text_desc(value: str) -> tuple[int, ...]:
    return tuple(-ord(character) for character in value)


def build_match_summary(match: Match) -> MatchSummaryResponse:
    return MatchSummaryResponse(
        id=match.id,
        match_date=match.match_date,
        league=match.season.league.name,
        season=match.season.name,
        home_team=match.home_team.name,
        away_team=match.away_team.name,
        status=match.status.name,
        source=match.source.name,
        result=build_result_response(match.result),
    )


def build_match_detail(match: Match) -> MatchDetailResponse:
    return MatchDetailResponse(
        id=match.id,
        match_date=match.match_date,
        league=LeagueResponse(
            id=match.season.league.id,
            name=match.season.league.name,
            country=match.season.league.country.name,
        ),
        season=SeasonResponse(id=match.season.id, name=match.season.name),
        home_team=TeamResponse(
            id=match.home_team.id,
            name=match.home_team.name,
            country=match.home_team.country.name,
        ),
        away_team=TeamResponse(
            id=match.away_team.id,
            name=match.away_team.name,
            country=match.away_team.country.name,
        ),
        status=match.status.name,
        source=match.source.name,
        result=build_result_response(match.result),
        odds=[build_odds_response(odds) for odds in match.odds],
    )


def build_result_response(result: MatchResult | None) -> MatchResultResponse | None:
    if result is None:
        return None
    return MatchResultResponse(
        actual_outcome=result.actual_outcome,
        home_goals=result.home_goals,
        away_goals=result.away_goals,
        total_corners=result.total_corners,
        total_yellow_cards=result.total_yellow_cards,
    )


def build_odds_response(odds: Odds) -> OddsResponse:
    return OddsResponse(
        id=odds.id,
        bookmaker=odds.bookmaker.name,
        home_win_odds=float(odds.home_win_odds),
        draw_odds=float(odds.draw_odds),
        away_win_odds=float(odds.away_win_odds),
        collected_at=odds.collected_at,
    )
