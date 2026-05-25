from __future__ import annotations

from datetime import date, datetime

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


def build_match_summary(match: Match) -> MatchSummaryResponse:
    return MatchSummaryResponse(
        id=match.id,
        match_date=match.match_date,
        league=match.season.league.name,
        season=match.season.name,
        home_team=match.home_team.name,
        away_team=match.away_team.name,
        status=match.status.name,
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
