from __future__ import annotations

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.api.config import ADMIN_DEMO_ENABLED
from src.api.database.session import SessionLocal
from src.api.services.auth_service import authenticate_user, get_user_by_id


ADMIN_SESSION_USER_ID_KEY = "admin_user_id"
ADMIN_SESSION_DEMO_KEY = "admin_demo"


def is_admin_role(role_name: str | None) -> bool:
    return role_name == "admin"


def is_demo_admin_session(request: Request) -> bool:
    return bool(request.session.get(ADMIN_SESSION_DEMO_KEY))


class AdminAuthBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        if ADMIN_DEMO_ENABLED and str(form.get("demo_mode", "")).strip() == "1":
            request.session.clear()
            request.session.update(
                {
                    ADMIN_SESSION_DEMO_KEY: True,
                    "admin_username": "demo",
                    "admin_role": "demo",
                }
            )
            return True

        username_or_email = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
        if not username_or_email or not password:
            return False

        with SessionLocal() as db:
            user = authenticate_user(db, username_or_email, password)
            if user is None or not is_admin_role(user.role.name):
                return False

            request.session.clear()
            request.session.update(
                {
                    ADMIN_SESSION_USER_ID_KEY: user.id,
                    "admin_username": user.username,
                    "admin_role": user.role.name,
                }
            )
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if is_demo_admin_session(request):
            if ADMIN_DEMO_ENABLED:
                return True
            request.session.clear()
            return False

        user_id = request.session.get(ADMIN_SESSION_USER_ID_KEY)
        if user_id is None:
            return False

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            request.session.clear()
            return False

        with SessionLocal() as db:
            user = get_user_by_id(db, user_id_int)
            if user is None or not is_admin_role(user.role.name):
                request.session.clear()
                return False

        return True
