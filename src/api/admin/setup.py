from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src.api.admin.auth import AdminAuthBackend, is_demo_admin_session
from src.api.admin.dashboard import DashboardView
from src.api.admin.views import ADMIN_VIEWS
from src.api.config import ADMIN_SESSION_SECRET
from src.api.database.session import engine


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class DemoSafeAdmin(Admin):
    async def create(self, request: Request):
        if is_demo_admin_session(request):
            raise HTTPException(status_code=403, detail="Demo mode is read-only")
        return await super().create(request)

    async def edit(self, request: Request):
        if is_demo_admin_session(request):
            raise HTTPException(status_code=403, detail="Demo mode is read-only")
        return await super().edit(request)

    async def delete(self, request: Request):
        if is_demo_admin_session(request):
            raise HTTPException(status_code=403, detail="Demo mode is read-only")
        return await super().delete(request)

    async def export(self, request: Request):
        if is_demo_admin_session(request):
            raise HTTPException(status_code=403, detail="Demo mode is read-only")
        return await super().export(request)


def setup_admin(app: FastAPI) -> None:
    authentication_backend = AdminAuthBackend(secret_key=ADMIN_SESSION_SECRET)
    admin = DemoSafeAdmin(
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
