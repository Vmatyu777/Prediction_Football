from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin

from src.api.admin.auth import AdminAuthBackend
from src.api.admin.dashboard import DashboardView
from src.api.admin.views import ADMIN_VIEWS
from src.api.config import ADMIN_SESSION_SECRET
from src.api.database.session import engine


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def setup_admin(app: FastAPI) -> None:
    authentication_backend = AdminAuthBackend(secret_key=ADMIN_SESSION_SECRET)
    admin = Admin(
        app=app,
        engine=engine,
        title="Административная панель",
        base_url="/admin",
        templates_dir=str(TEMPLATES_DIR),
        authentication_backend=authentication_backend,
    )
    admin.add_view(DashboardView)
    for view in ADMIN_VIEWS:
        admin.add_view(view)
