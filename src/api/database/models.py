from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.database.session import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    leagues: Mapped[list["League"]] = relationship(back_populates="country")
    teams: Mapped[list["Team"]] = relationship(back_populates="country")


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)

    country: Mapped["Country"] = relationship(back_populates="leagues")
    seasons: Mapped[list["Season"]] = relationship(back_populates="league")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    league: Mapped["League"] = relationship(back_populates="seasons")
    matches: Mapped[list["Match"]] = relationship(back_populates="season")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)

    country: Mapped["Country"] = relationship(back_populates="teams")
    elo_ratings: Mapped[list["TeamEloRating"]] = relationship(back_populates="team")
    home_matches: Mapped[list["Match"]] = relationship(
        back_populates="home_team",
        foreign_keys="Match.home_team_id",
    )
    away_matches: Mapped[list["Match"]] = relationship(
        back_populates="away_team",
        foreign_keys="Match.away_team_id",
    )


class TeamEloRating(Base):
    __tablename__ = "team_elo_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating_date: Mapped[date] = mapped_column(Date, nullable=False)
    elo_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="elo_ratings")


class MatchStatus(Base):
    __tablename__ = "match_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    matches: Mapped[list["Match"]] = relationship(back_populates="status")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("match_statuses.id"), nullable=False)

    season: Mapped["Season"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(back_populates="home_matches", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(back_populates="away_matches", foreign_keys=[away_team_id])
    status: Mapped["MatchStatus"] = relationship(back_populates="matches")
    result: Mapped["MatchResult | None"] = relationship(back_populates="match")
    odds: Mapped[list["Odds"]] = relationship(back_populates="match")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="match")


class MatchResult(Base):
    __tablename__ = "match_results"
    __table_args__ = (CheckConstraint("actual_outcome in (0, 1, 2)", name="ck_match_results_actual_outcome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actual_outcome: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    home_goals: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    away_goals: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_corners: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_yellow_cards: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, unique=True)

    match: Mapped["Match"] = relationship(back_populates="result")


class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    odds: Mapped[list["Odds"]] = relationship(back_populates="bookmaker")


class Odds(Base):
    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    home_win_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    draw_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    away_win_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    bookmaker_id: Mapped[int] = mapped_column(ForeignKey("bookmakers.id"), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="odds")
    bookmaker: Mapped["Bookmaker"] = relationship(back_populates="odds")


class ModelType(Base):
    __tablename__ = "model_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    models: Mapped[list["Model"]] = relationship(back_populates="model_type")


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    model_type_id: Mapped[int] = mapped_column(ForeignKey("model_types.id"), nullable=False)

    model_type: Mapped["ModelType"] = relationship(back_populates="models")
    metrics: Mapped[list["ModelMetric"]] = relationship(back_populates="model")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    model_metrics: Mapped[list["ModelMetric"]] = relationship(back_populates="metric")


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    model: Mapped["Model"] = relationship(back_populates="metrics")
    metric: Mapped["Metric"] = relationship(back_populates="model_metrics")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (CheckConstraint("predicted_outcome in (0, 1, 2)", name="ck_predictions_predicted_outcome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    predicted_outcome: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    home_win_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    draw_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    away_win_probability: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)

    model: Mapped["Model"] = relationship(back_populates="predictions")
    match: Mapped["Match"] = relationship(back_populates="predictions")
    characteristic_values: Mapped[list["PredictionCharacteristicValue"]] = relationship(
        back_populates="prediction"
    )
    query_history: Mapped[list["UserQueryHistory"]] = relationship(back_populates="prediction")


class PredictionCharacteristic(Base):
    __tablename__ = "prediction_characteristics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    values: Mapped[list["PredictionCharacteristicValue"]] = relationship(back_populates="characteristic")


class PredictionCharacteristicValue(Base):
    __tablename__ = "prediction_characteristic_values"

    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), primary_key=True)
    characteristic_id: Mapped[int] = mapped_column(ForeignKey("prediction_characteristics.id"), primary_key=True)
    predicted_value: Mapped[str] = mapped_column(String(20), nullable=False)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    prediction: Mapped["Prediction"] = relationship(back_populates="characteristic_values")
    characteristic: Mapped["PredictionCharacteristic"] = relationship(back_populates="values")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"), nullable=False)

    role: Mapped["UserRole"] = relationship(back_populates="users")
    query_history: Mapped[list["UserQueryHistory"]] = relationship(back_populates="user")


class UserQueryHistory(Base):
    __tablename__ = "user_query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="query_history")
    prediction: Mapped["Prediction"] = relationship(back_populates="query_history")
