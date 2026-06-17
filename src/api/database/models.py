from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.database.session import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    leagues: Mapped[list["League"]] = relationship(back_populates="country")
    teams: Mapped[list["Team"]] = relationship(back_populates="country")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)

    country: Mapped["Country"] = relationship(back_populates="leagues")
    seasons: Mapped[list["Season"]] = relationship(back_populates="league")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)

    league: Mapped["League"] = relationship(back_populates="seasons")
    matches: Mapped[list["Match"]] = relationship(back_populates="season")

    def __str__(self) -> str:
        league = self.__dict__.get("league")
        if league is not None:
            return f"{league.name} - {self.name}"
        return self.name

    __repr__ = __str__


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

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class TeamEloRating(Base):
    __tablename__ = "team_elo_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating_date: Mapped[date] = mapped_column(Date, nullable=False)
    elo_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="elo_ratings")

    def __str__(self) -> str:
        team = self.__dict__.get("team")
        team_label = str(team) if team is not None else f"team #{self.team_id}"
        return f"{team_label} {self.rating_date}: {self.elo_value}"

    __repr__ = __str__


class MatchStatus(Base):
    __tablename__ = "match_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    matches: Mapped[list["Match"]] = relationship(back_populates="status")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class MatchSource(Base):
    __tablename__ = "match_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    matches: Mapped[list["Match"]] = relationship(back_populates="source")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class ExternalSource(Base):
    __tablename__ = "external_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    matches: Mapped[list["Match"]] = relationship(back_populates="external_source")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("external_source_id", "external_match_id", name="uq_matches_external_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("match_statuses.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("match_sources.id"), nullable=False)
    external_source_id: Mapped[int | None] = mapped_column(ForeignKey("external_sources.id"))
    external_match_id: Mapped[str | None] = mapped_column(String(100))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime)

    season: Mapped["Season"] = relationship(back_populates="matches")
    home_team: Mapped["Team"] = relationship(back_populates="home_matches", foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(back_populates="away_matches", foreign_keys=[away_team_id])
    status: Mapped["MatchStatus"] = relationship(back_populates="matches")
    source: Mapped["MatchSource"] = relationship(back_populates="matches")
    external_source: Mapped["ExternalSource | None"] = relationship(back_populates="matches")
    result: Mapped["MatchResult | None"] = relationship(back_populates="match")
    odds: Mapped[list["Odds"]] = relationship(back_populates="match")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="match")

    def __str__(self) -> str:
        home_team = self.__dict__.get("home_team")
        away_team = self.__dict__.get("away_team")
        home_label = str(home_team) if home_team is not None else f"team #{self.home_team_id}"
        away_label = str(away_team) if away_team is not None else f"team #{self.away_team_id}"
        return f"{home_label} vs {away_label} ({self.match_date:%Y-%m-%d})"

    __repr__ = __str__


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

    def __str__(self) -> str:
        return f"{self.home_goals}:{self.away_goals}"

    __repr__ = __str__


class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    odds: Mapped[list["Odds"]] = relationship(back_populates="bookmaker")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class Odds(Base):
    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    home_win_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    draw_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    away_win_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    over25_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    under25_odds: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False)
    bookmaker_id: Mapped[int] = mapped_column(ForeignKey("bookmakers.id"), nullable=False)

    match: Mapped["Match"] = relationship(back_populates="odds")
    bookmaker: Mapped["Bookmaker"] = relationship(back_populates="odds")

    def __str__(self) -> str:
        bookmaker = self.__dict__.get("bookmaker")
        bookmaker_label = str(bookmaker) if bookmaker is not None else f"bookmaker #{self.bookmaker_id}"
        return f"{bookmaker_label} odds for match #{self.match_id}"

    __repr__ = __str__


class ModelType(Base):
    __tablename__ = "model_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    models: Mapped[list["Model"]] = relationship(back_populates="model_type")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


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

    def __str__(self) -> str:
        return f"{self.name} {self.version}"

    __repr__ = __str__


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    model_metrics: Mapped[list["ModelMetric"]] = relationship(back_populates="metric")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    model: Mapped["Model"] = relationship(back_populates="metrics")
    metric: Mapped["Metric"] = relationship(back_populates="model_metrics")

    def __str__(self) -> str:
        metric = self.__dict__.get("metric")
        metric_label = str(metric) if metric is not None else f"metric #{self.metric_id}"
        return f"{metric_label}: {self.metric_value}"

    __repr__ = __str__


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

    def __str__(self) -> str:
        return f"Prediction #{self.id}"

    __repr__ = __str__


class PredictionCharacteristic(Base):
    __tablename__ = "prediction_characteristics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    values: Mapped[list["PredictionCharacteristicValue"]] = relationship(back_populates="characteristic")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class PredictionCharacteristicValue(Base):
    __tablename__ = "prediction_characteristic_values"

    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), primary_key=True)
    characteristic_id: Mapped[int] = mapped_column(ForeignKey("prediction_characteristics.id"), primary_key=True)
    predicted_value: Mapped[str] = mapped_column(String(20), nullable=False)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    prediction: Mapped["Prediction"] = relationship(back_populates="characteristic_values")
    characteristic: Mapped["PredictionCharacteristic"] = relationship(back_populates="values")

    def __str__(self) -> str:
        characteristic = self.__dict__.get("characteristic")
        characteristic_label = (
            str(characteristic) if characteristic is not None else f"characteristic #{self.characteristic_id}"
        )
        return f"{characteristic_label}: {self.predicted_value}"

    __repr__ = __str__


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_history_viewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"), nullable=False)

    role: Mapped["UserRole"] = relationship(back_populates="users")
    query_history: Mapped[list["UserQueryHistory"]] = relationship(back_populates="user")

    def __str__(self) -> str:
        return self.username

    __repr__ = __str__


class UserQueryHistory(Base):
    __tablename__ = "user_query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="query_history")
    prediction: Mapped["Prediction"] = relationship(back_populates="query_history")

    def __str__(self) -> str:
        user = self.__dict__.get("user")
        prediction = self.__dict__.get("prediction")
        user_label = str(user) if user is not None else f"user #{self.user_id}"
        prediction_label = str(prediction) if prediction is not None else f"prediction #{self.prediction_id}"
        return f"{user_label} -> {prediction_label}"

    __repr__ = __str__
