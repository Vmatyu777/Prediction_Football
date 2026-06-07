from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, ForeignKeyFilter, StaticValuesFilter

from src.api.admin.auth import ADMIN_SESSION_USER_ID_KEY, is_demo_admin_session
from src.api.database.models import (
    Bookmaker,
    Country,
    ExternalSource,
    League,
    Match,
    MatchResult,
    MatchSource,
    MatchStatus,
    Metric,
    Model,
    ModelMetric,
    ModelType,
    Odds,
    Prediction,
    PredictionCharacteristic,
    PredictionCharacteristicValue,
    Season,
    Team,
    TeamEloRating,
    User,
    UserQueryHistory,
    UserRole,
)
from src.api.database.session import SessionLocal


class IntegerStaticValuesFilter(StaticValuesFilter):
    async def get_filtered_query(self, query, value: Any, model: Any):
        if value == "":
            return query

        column_obj = getattr(model, self.column) if isinstance(self.column, str) else self.column
        return query.filter(column_obj == int(value))


def format_match_label(match: Match | None) -> str:
    if match is None:
        return "Матч не указан"

    home_team = match.__dict__.get("home_team")
    away_team = match.__dict__.get("away_team")
    if home_team is not None and away_team is not None:
        return f"{home_team} vs {away_team} ({match.match_date:%Y-%m-%d})"

    return f"Матч #{match.id} ({match.match_date:%Y-%m-%d})"


def format_prediction_label(prediction: Prediction | None) -> str:
    if prediction is None:
        return "Прогноз не указан"

    match = prediction.__dict__.get("match")
    match_label = format_match_label(match) if match is not None else f"Матч #{prediction.match_id}"
    return f"Прогноз #{prediction.id} — {match_label}"


def format_prediction_match(prediction: Prediction, _attribute: Any) -> str:
    return format_match_label(prediction.__dict__.get("match"))


def format_history_prediction(history: UserQueryHistory, _attribute: Any) -> str:
    return format_prediction_label(history.__dict__.get("prediction"))


DEMO_ADMIN_VISIBLE_IDENTITIES = {
    "user",
    "match",
    "match-result",
    "prediction",
    "user-query-history",
    "model",
    "model-metric",
    "country",
    "league",
    "season",
    "team",
}


class SecureModelView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    can_export = True
    page_size = 50
    page_size_options = [25, 50, 100]

    def is_visible(self, request) -> bool:
        if is_demo_admin_session(request):
            return self.identity in DEMO_ADMIN_VISIBLE_IDENTITIES
        return super().is_visible(request)

    def is_accessible(self, request) -> bool:
        if is_demo_admin_session(request):
            return self.identity in DEMO_ADMIN_VISIBLE_IDENTITIES
        return super().is_accessible(request)

    async def insert_model(self, request, data: dict) -> Any:
        if is_demo_admin_session(request):
            raise PermissionError("Demo mode is read-only")
        return await super().insert_model(request, data)

    async def update_model(self, request, pk: str, data: dict) -> Any:
        if is_demo_admin_session(request):
            raise PermissionError("Demo mode is read-only")
        return await super().update_model(request, pk, data)

    async def delete_model(self, request, pk: Any) -> None:
        if is_demo_admin_session(request):
            raise PermissionError("Demo mode is read-only")
        await super().delete_model(request, pk)


class UserAdmin(SecureModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"
    category = "Аккаунты"
    can_edit = True
    column_list = [User.id, User.username, User.email, User.role, User.created_at, User.last_history_viewed_at]
    column_details_list = [User.id, User.username, User.email, User.role, User.created_at, User.last_history_viewed_at]
    column_labels = {
        User.id: "ID",
        User.username: "Логин",
        User.email: "Почта",
        User.role: "Роль",
        User.created_at: "Создан",
        User.last_history_viewed_at: "История просмотрена",
    }
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    column_default_sort = [(User.created_at, True)]
    column_filters = [ForeignKeyFilter(User.role_id, UserRole.name, title="Роль")]
    form_columns = [User.role]

    async def on_model_change(self, data: dict, model: User, is_created: bool, request) -> None:
        if is_created or "role" not in data:
            return

        new_role_id = self._extract_role_id(data["role"])
        if new_role_id is None:
            return

        current_admin_id = request.session.get(ADMIN_SESSION_USER_ID_KEY)
        try:
            current_admin_id = int(current_admin_id)
        except (TypeError, ValueError):
            current_admin_id = None

        with SessionLocal() as db:
            new_role = db.get(UserRole, new_role_id)
            current_role = db.get(UserRole, model.role_id)
            admin_count = (
                db.query(User)
                .join(UserRole)
                .filter(UserRole.name == "admin")
                .count()
            )

        if new_role is None or new_role.name == "admin" or current_role is None:
            return

        is_self_demotion = current_role.name == "admin" and model.id == current_admin_id
        is_last_admin_demotion = current_role.name == "admin" and admin_count <= 1

        if is_last_admin_demotion:
            raise ValueError("Нельзя убрать последнего администратора системы")

        if is_self_demotion:
            raise ValueError("Нельзя понизить собственную роль администратора")

    @staticmethod
    def _extract_role_id(role_value: Any) -> int | None:
        if isinstance(role_value, UserRole):
            return role_value.id
        try:
            return int(role_value)
        except (TypeError, ValueError):
            return None


class UserRoleAdmin(SecureModelView, model=UserRole):
    name = "Роль пользователя"
    name_plural = "Роли пользователей"
    icon = "fa-solid fa-user-shield"
    category = "Аккаунты"
    column_list = [UserRole.id, UserRole.name]
    column_details_list = column_list
    column_labels = {UserRole.id: "ID", UserRole.name: "Название"}
    column_searchable_list = [UserRole.name]
    column_sortable_list = [UserRole.id, UserRole.name]


class MatchAdmin(SecureModelView, model=Match):
    name = "Матч"
    name_plural = "Матчи"
    icon = "fa-solid fa-futbol"
    category = "Футбольные данные"
    column_list = [
        Match.id,
        Match.match_date,
        Match.season,
        Match.home_team,
        Match.away_team,
        Match.status,
        Match.source,
        Match.external_match_id,
    ]
    column_details_list = [
        Match.id,
        Match.match_date,
        Match.season,
        Match.home_team,
        Match.away_team,
        Match.status,
        Match.source,
        Match.external_source,
        Match.external_match_id,
        Match.last_synced_at,
    ]
    column_labels = {
        Match.id: "ID",
        Match.match_date: "Дата матча",
        Match.season: "Сезон",
        Match.home_team: "Хозяева",
        Match.away_team: "Гости",
        Match.status: "Статус",
        Match.source: "Источник",
        Match.external_source: "Внешний источник",
        Match.external_match_id: "Внешний ID",
        Match.last_synced_at: "Последняя синхронизация",
    }
    column_searchable_list = [Match.external_match_id]
    column_sortable_list = [Match.id, Match.match_date]
    column_default_sort = [(Match.match_date, True), (Match.id, True)]
    column_filters = [
        ForeignKeyFilter(Match.season_id, Season.name, title="Сезон"),
        ForeignKeyFilter(Match.status_id, MatchStatus.name, title="Статус"),
        ForeignKeyFilter(Match.source_id, MatchSource.name, title="Источник"),
        ForeignKeyFilter(Match.external_source_id, ExternalSource.name, title="Внешний источник"),
    ]


class MatchResultAdmin(SecureModelView, model=MatchResult):
    name = "Результат матча"
    name_plural = "Результаты матчей"
    icon = "fa-solid fa-square-poll-vertical"
    category = "Футбольные данные"
    column_list = [
        MatchResult.id,
        MatchResult.match_id,
        MatchResult.actual_outcome,
        MatchResult.home_goals,
        MatchResult.away_goals,
        MatchResult.total_corners,
        MatchResult.total_yellow_cards,
    ]
    column_details_list = column_list
    column_labels = {
        MatchResult.id: "ID",
        MatchResult.match_id: "ID матча",
        MatchResult.actual_outcome: "Исход",
        MatchResult.home_goals: "Голы хозяев",
        MatchResult.away_goals: "Голы гостей",
        MatchResult.total_corners: "Угловые",
        MatchResult.total_yellow_cards: "Жёлтые карточки",
    }
    column_sortable_list = [MatchResult.id, MatchResult.match_id]
    column_filters = [
        IntegerStaticValuesFilter(
            MatchResult.actual_outcome,
            values=[(0, "П2"), (1, "Ничья"), (2, "П1")],
            title="Исход",
        )
    ]


class OddsAdmin(SecureModelView, model=Odds):
    name = "Коэффициенты"
    name_plural = "Коэффициенты"
    icon = "fa-solid fa-percent"
    category = "Футбольные данные"
    column_list = [
        Odds.id,
        Odds.match_id,
        Odds.bookmaker,
        Odds.home_win_odds,
        Odds.draw_odds,
        Odds.away_win_odds,
        Odds.over25_odds,
        Odds.under25_odds,
        Odds.collected_at,
    ]
    column_details_list = column_list
    column_labels = {
        Odds.id: "ID",
        Odds.match_id: "ID матча",
        Odds.bookmaker: "Букмекер",
        Odds.home_win_odds: "П1",
        Odds.draw_odds: "Ничья",
        Odds.away_win_odds: "П2",
        Odds.over25_odds: "ТБ 2.5",
        Odds.under25_odds: "ТМ 2.5",
        Odds.collected_at: "Собрано",
    }
    column_sortable_list = [Odds.id, Odds.match_id, Odds.collected_at]
    column_filters = [ForeignKeyFilter(Odds.bookmaker_id, Bookmaker.name, title="Букмекер")]


class PredictionAdmin(SecureModelView, model=Prediction):
    name = "Прогноз"
    name_plural = "Прогнозы"
    icon = "fa-solid fa-chart-simple"
    category = "Прогнозы"
    column_list = [
        Prediction.id,
        Prediction.created_at,
        Prediction.match,
        Prediction.model,
        Prediction.predicted_outcome,
        Prediction.home_win_probability,
        Prediction.draw_probability,
        Prediction.away_win_probability,
    ]
    column_details_list = column_list
    column_labels = {
        Prediction.id: "ID",
        Prediction.created_at: "Создан",
        Prediction.match: "Матч",
        Prediction.model: "Модель",
        Prediction.predicted_outcome: "Исход",
        Prediction.home_win_probability: "Вероятность П1",
        Prediction.draw_probability: "Вероятность ничьей",
        Prediction.away_win_probability: "Вероятность П2",
    }
    column_sortable_list = [Prediction.id, Prediction.created_at, Prediction.match_id, Prediction.model_id]
    column_default_sort = [(Prediction.created_at, True), (Prediction.id, True)]
    column_formatters = {
        Prediction.match: format_prediction_match,
    }
    column_formatters_detail = column_formatters
    column_filters = [
        ForeignKeyFilter(Prediction.model_id, Model.name, title="Модель"),
        IntegerStaticValuesFilter(
            Prediction.predicted_outcome,
            values=[(0, "П2"), (1, "Ничья"), (2, "П1")],
            title="Исход",
        ),
    ]

    def list_query(self, request):
        return (
            select(Prediction)
            .options(selectinload(Prediction.match).selectinload(Match.home_team))
            .options(selectinload(Prediction.match).selectinload(Match.away_team))
            .options(selectinload(Prediction.model))
        )

    def details_query(self, request):
        return (
            super()
            .details_query(request)
            .options(selectinload(Prediction.match).selectinload(Match.home_team))
            .options(selectinload(Prediction.match).selectinload(Match.away_team))
            .options(selectinload(Prediction.model))
        )


class PredictionCharacteristicValueAdmin(SecureModelView, model=PredictionCharacteristicValue):
    name = "Значение характеристики прогноза"
    name_plural = "Значения характеристик прогноза"
    icon = "fa-solid fa-list-check"
    category = "Прогнозы"
    column_list = [
        PredictionCharacteristicValue.prediction_id,
        PredictionCharacteristicValue.characteristic_id,
        PredictionCharacteristicValue.predicted_value,
        PredictionCharacteristicValue.probability,
    ]
    column_details_list = column_list
    column_labels = {
        PredictionCharacteristicValue.prediction_id: "ID прогноза",
        PredictionCharacteristicValue.characteristic_id: "ID характеристики",
        PredictionCharacteristicValue.predicted_value: "Значение",
        PredictionCharacteristicValue.probability: "Вероятность",
    }
    column_filters = [
        ForeignKeyFilter(
            PredictionCharacteristicValue.characteristic_id,
            PredictionCharacteristic.name,
            title="Характеристика",
        ),
        StaticValuesFilter(
            PredictionCharacteristicValue.predicted_value,
            values=[
                ("A", "П2"),
                ("D", "Ничья"),
                ("H", "П1"),
                ("Yes", "Да"),
                ("No", "Нет"),
            ],
            title="Значение",
        ),
    ]


class UserQueryHistoryAdmin(SecureModelView, model=UserQueryHistory):
    name = "История запросов"
    name_plural = "История запросов"
    icon = "fa-solid fa-clock-rotate-left"
    category = "Прогнозы"
    column_list = [
        UserQueryHistory.id,
        UserQueryHistory.query_date,
        UserQueryHistory.user,
        UserQueryHistory.prediction,
    ]
    column_details_list = column_list
    column_labels = {
        UserQueryHistory.id: "ID",
        UserQueryHistory.query_date: "Дата запроса",
        UserQueryHistory.user: "Пользователь",
        UserQueryHistory.prediction: "Прогноз",
    }
    column_sortable_list = [UserQueryHistory.id, UserQueryHistory.query_date, UserQueryHistory.user_id]
    column_default_sort = [(UserQueryHistory.query_date, True), (UserQueryHistory.id, True)]
    column_formatters = {
        UserQueryHistory.prediction: format_history_prediction,
    }
    column_formatters_detail = column_formatters
    column_filters = [ForeignKeyFilter(UserQueryHistory.user_id, User.username, title="Пользователь")]

    def list_query(self, request):
        return (
            select(UserQueryHistory)
            .options(selectinload(UserQueryHistory.user))
            .options(
                selectinload(UserQueryHistory.prediction)
                .selectinload(Prediction.match)
                .selectinload(Match.home_team)
            )
            .options(
                selectinload(UserQueryHistory.prediction)
                .selectinload(Prediction.match)
                .selectinload(Match.away_team)
            )
        )

    def details_query(self, request):
        return (
            super()
            .details_query(request)
            .options(selectinload(UserQueryHistory.user))
            .options(
                selectinload(UserQueryHistory.prediction)
                .selectinload(Prediction.match)
                .selectinload(Match.home_team)
            )
            .options(
                selectinload(UserQueryHistory.prediction)
                .selectinload(Prediction.match)
                .selectinload(Match.away_team)
            )
        )


class ModelAdmin(SecureModelView, model=Model):
    name = "Модель"
    name_plural = "Модели"
    icon = "fa-solid fa-brain"
    category = "Модели"
    column_list = [Model.id, Model.name, Model.version, Model.trained_at, Model.file_path, Model.model_type]
    column_details_list = column_list
    column_labels = {
        Model.id: "ID",
        Model.name: "Название",
        Model.version: "Версия",
        Model.trained_at: "Обучена",
        Model.file_path: "Путь к файлу",
        Model.model_type: "Тип модели",
    }
    column_searchable_list = [Model.name, Model.version, Model.file_path]
    column_sortable_list = [Model.id, Model.name, Model.version, Model.trained_at]
    column_filters = [ForeignKeyFilter(Model.model_type_id, ModelType.name, title="Тип модели")]


class ModelMetricAdmin(SecureModelView, model=ModelMetric):
    name = "Метрика модели"
    name_plural = "Метрики моделей"
    icon = "fa-solid fa-gauge-high"
    category = "Модели"
    column_list = [ModelMetric.model_id, ModelMetric.metric_id, ModelMetric.metric_value, ModelMetric.is_primary]
    column_details_list = column_list
    column_labels = {
        ModelMetric.model_id: "ID модели",
        ModelMetric.metric_id: "ID метрики",
        ModelMetric.metric_value: "Значение",
        ModelMetric.is_primary: "Основная",
    }
    column_filters = [
        ForeignKeyFilter(ModelMetric.model_id, Model.name, title="Модель"),
        ForeignKeyFilter(ModelMetric.metric_id, Metric.name, title="Метрика"),
        BooleanFilter(ModelMetric.is_primary, title="Основная"),
    ]


class CountryAdmin(SecureModelView, model=Country):
    name = "Страна"
    name_plural = "Страны"
    icon = "fa-solid fa-globe"
    category = "Справочники"
    column_list = [Country.id, Country.name]
    column_details_list = column_list
    column_labels = {Country.id: "ID", Country.name: "Название"}
    column_searchable_list = [Country.name]
    column_sortable_list = [Country.id, Country.name]


class LeagueAdmin(SecureModelView, model=League):
    name = "Лига"
    name_plural = "Лиги"
    icon = "fa-solid fa-table-list"
    category = "Справочники"
    column_list = [League.id, League.name, League.country]
    column_details_list = column_list
    column_labels = {League.id: "ID", League.name: "Название", League.country: "Страна"}
    column_searchable_list = [League.name]
    column_sortable_list = [League.id, League.name]
    column_filters = [ForeignKeyFilter(League.country_id, Country.name, title="Страна")]


class SeasonAdmin(SecureModelView, model=Season):
    name = "Сезон"
    name_plural = "Сезоны"
    icon = "fa-solid fa-calendar"
    category = "Справочники"
    column_list = [Season.id, Season.name, Season.start_date, Season.end_date, Season.league]
    column_details_list = column_list
    column_labels = {
        Season.id: "ID",
        Season.name: "Название",
        Season.start_date: "Начало",
        Season.end_date: "Окончание",
        Season.league: "Лига",
    }
    column_searchable_list = [Season.name]
    column_sortable_list = [Season.id, Season.name, Season.start_date]
    column_filters = [ForeignKeyFilter(Season.league_id, League.name, title="Лига")]


class TeamAdmin(SecureModelView, model=Team):
    name = "Команда"
    name_plural = "Команды"
    icon = "fa-solid fa-people-group"
    category = "Справочники"
    column_list = [Team.id, Team.name, Team.country]
    column_details_list = column_list
    column_labels = {Team.id: "ID", Team.name: "Название", Team.country: "Страна"}
    column_searchable_list = [Team.name]
    column_sortable_list = [Team.id, Team.name]
    column_filters = [ForeignKeyFilter(Team.country_id, Country.name, title="Страна")]


class TeamEloRatingAdmin(SecureModelView, model=TeamEloRating):
    name = "Рейтинг ELO команды"
    name_plural = "Рейтинги ELO команд"
    icon = "fa-solid fa-chart-line"
    category = "Футбольные данные"
    column_list = [
        TeamEloRating.id,
        TeamEloRating.rating_date,
        TeamEloRating.team,
        TeamEloRating.elo_value,
    ]
    column_details_list = [
        TeamEloRating.id,
        TeamEloRating.rating_date,
        TeamEloRating.team,
        TeamEloRating.team_id,
        TeamEloRating.elo_value,
    ]
    column_labels = {
        TeamEloRating.id: "ID",
        TeamEloRating.rating_date: "Дата рейтинга",
        TeamEloRating.team: "Команда",
        TeamEloRating.team_id: "ID команды",
        TeamEloRating.elo_value: "ELO",
    }
    column_sortable_list = [TeamEloRating.id, TeamEloRating.rating_date, TeamEloRating.elo_value]
    column_default_sort = [(TeamEloRating.rating_date, True), (TeamEloRating.id, True)]
    column_filters = [ForeignKeyFilter(TeamEloRating.team_id, Team.name, title="Команда")]


class MetricAdmin(SecureModelView, model=Metric):
    name = "Метрика"
    name_plural = "Метрики"
    icon = "fa-solid fa-ruler"
    category = "Справочники"
    column_list = [Metric.id, Metric.name]
    column_details_list = column_list
    column_labels = {Metric.id: "ID", Metric.name: "Название"}
    column_searchable_list = [Metric.name]
    column_sortable_list = [Metric.id, Metric.name]


class ModelTypeAdmin(SecureModelView, model=ModelType):
    name = "Тип модели"
    name_plural = "Типы моделей"
    icon = "fa-solid fa-diagram-project"
    category = "Справочники"
    column_list = [ModelType.id, ModelType.name]
    column_details_list = column_list
    column_labels = {ModelType.id: "ID", ModelType.name: "Название"}
    column_searchable_list = [ModelType.name]
    column_sortable_list = [ModelType.id, ModelType.name]


class MatchSourceAdmin(SecureModelView, model=MatchSource):
    name = "Источник матча"
    name_plural = "Источники матчей"
    icon = "fa-solid fa-database"
    category = "Справочники"
    column_list = [MatchSource.id, MatchSource.name]
    column_details_list = column_list
    column_labels = {MatchSource.id: "ID", MatchSource.name: "Название"}
    column_searchable_list = [MatchSource.name]
    column_sortable_list = [MatchSource.id, MatchSource.name]


class ExternalSourceAdmin(SecureModelView, model=ExternalSource):
    name = "Внешний источник"
    name_plural = "Внешние источники"
    icon = "fa-solid fa-cloud"
    category = "Справочники"
    column_list = [ExternalSource.id, ExternalSource.name]
    column_details_list = column_list
    column_labels = {ExternalSource.id: "ID", ExternalSource.name: "Название"}
    column_searchable_list = [ExternalSource.name]
    column_sortable_list = [ExternalSource.id, ExternalSource.name]


class BookmakerAdmin(SecureModelView, model=Bookmaker):
    name = "Букмекер"
    name_plural = "Букмекеры"
    icon = "fa-solid fa-building-columns"
    category = "Справочники"
    column_list = [Bookmaker.id, Bookmaker.name]
    column_details_list = column_list
    column_labels = {Bookmaker.id: "ID", Bookmaker.name: "Название"}
    column_searchable_list = [Bookmaker.name]
    column_sortable_list = [Bookmaker.id, Bookmaker.name]


class PredictionCharacteristicAdmin(SecureModelView, model=PredictionCharacteristic):
    name = "Характеристика прогноза"
    name_plural = "Характеристики прогноза"
    icon = "fa-solid fa-tags"
    category = "Справочники"
    column_list = [PredictionCharacteristic.id, PredictionCharacteristic.name]
    column_details_list = column_list
    column_labels = {PredictionCharacteristic.id: "ID", PredictionCharacteristic.name: "Название"}
    column_searchable_list = [PredictionCharacteristic.name]
    column_sortable_list = [PredictionCharacteristic.id, PredictionCharacteristic.name]


class MatchStatusAdmin(SecureModelView, model=MatchStatus):
    name = "Статус матча"
    name_plural = "Статусы матчей"
    icon = "fa-solid fa-circle-info"
    category = "Справочники"
    column_list = [MatchStatus.id, MatchStatus.name]
    column_details_list = column_list
    column_labels = {MatchStatus.id: "ID", MatchStatus.name: "Название"}
    column_searchable_list = [MatchStatus.name]
    column_sortable_list = [MatchStatus.id, MatchStatus.name]


ADMIN_VIEWS = [
    UserAdmin,
    UserRoleAdmin,
    MatchAdmin,
    MatchResultAdmin,
    OddsAdmin,
    PredictionAdmin,
    PredictionCharacteristicValueAdmin,
    UserQueryHistoryAdmin,
    ModelAdmin,
    ModelMetricAdmin,
    CountryAdmin,
    LeagueAdmin,
    SeasonAdmin,
    TeamAdmin,
    TeamEloRatingAdmin,
    MetricAdmin,
    ModelTypeAdmin,
    MatchSourceAdmin,
    ExternalSourceAdmin,
    BookmakerAdmin,
    PredictionCharacteristicAdmin,
    MatchStatusAdmin,
]
