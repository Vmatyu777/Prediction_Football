from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Date, cast, func
from sqlalchemy.orm import joinedload
from sqladmin import BaseView, expose

from src.api.database.models import Match, MatchSource, Model, Prediction, User, UserQueryHistory
from src.api.database.session import SessionLocal


class DashboardView(BaseView):
    name = "Панель управления"
    icon = "fa-solid fa-chart-line"

    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request):
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        first_chart_day = now.date() - timedelta(days=6)

        with SessionLocal() as db:
            total_users = int(db.query(func.count(User.id)).scalar() or 0)
            users_last_7_days = int(
                db.query(func.count(User.id))
                .filter(User.created_at >= seven_days_ago)
                .scalar()
                or 0
            )
            total_matches = int(db.query(func.count(Match.id)).scalar() or 0)
            upcoming_matches = int(
                db.query(func.count(Match.id))
                .filter(~Match.result.has())
                .scalar()
                or 0
            )
            total_predictions = int(db.query(func.count(Prediction.id)).scalar() or 0)
            predictions_last_7_days = int(
                db.query(func.count(Prediction.id))
                .filter(Prediction.created_at >= seven_days_ago)
                .scalar()
                or 0
            )
            prediction_rows_by_day = (
                db.query(cast(Prediction.created_at, Date), func.count(Prediction.id))
                .filter(Prediction.created_at >= seven_days_ago)
                .group_by(cast(Prediction.created_at, Date))
                .order_by(cast(Prediction.created_at, Date).asc())
                .all()
            )
            predictions_by_day = {row[0].isoformat(): int(row[1]) for row in prediction_rows_by_day}
            prediction_chart = [
                {
                    "label": (first_chart_day + timedelta(days=offset)).isoformat(),
                    "value": predictions_by_day.get((first_chart_day + timedelta(days=offset)).isoformat(), 0),
                }
                for offset in range(7)
            ]
            matches_by_source = [
                {"label": source_name, "value": int(count)}
                for source_name, count in (
                    db.query(MatchSource.name, func.count(Match.id))
                    .join(Match, Match.source_id == MatchSource.id)
                    .group_by(MatchSource.name)
                    .order_by(func.count(Match.id).desc())
                    .all()
                )
            ]
            predictions_by_model = [
                {"label": model_name, "value": int(count)}
                for model_name, count in (
                    db.query(Model.name, func.count(Prediction.id))
                    .join(Prediction, Prediction.model_id == Model.id)
                    .group_by(Model.name)
                    .order_by(func.count(Prediction.id).desc())
                    .all()
                )
            ]
            latest_predictions = (
                db.query(Prediction)
                .options(
                    joinedload(Prediction.match).joinedload(Match.home_team),
                    joinedload(Prediction.match).joinedload(Match.away_team),
                )
                .order_by(Prediction.created_at.desc(), Prediction.id.desc())
                .limit(10)
                .all()
            )
            latest_history = (
                db.query(UserQueryHistory)
                .options(
                    joinedload(UserQueryHistory.user),
                    joinedload(UserQueryHistory.prediction)
                    .joinedload(Prediction.match)
                    .joinedload(Match.home_team),
                    joinedload(UserQueryHistory.prediction)
                    .joinedload(Prediction.match)
                    .joinedload(Match.away_team),
                )
                .order_by(UserQueryHistory.query_date.desc(), UserQueryHistory.id.desc())
                .limit(10)
                .all()
            )

        return await self.templates.TemplateResponse(
            request,
            "admin_dashboard.html",
            {
                "total_users": total_users,
                "users_last_7_days": users_last_7_days,
                "total_matches": total_matches,
                "upcoming_matches": upcoming_matches,
                "total_predictions": total_predictions,
                "predictions_last_7_days": predictions_last_7_days,
                "prediction_chart": prediction_chart,
                "matches_by_source": matches_by_source,
                "predictions_by_model": predictions_by_model,
                "latest_predictions": latest_predictions,
                "latest_history": latest_history,
            },
        )
