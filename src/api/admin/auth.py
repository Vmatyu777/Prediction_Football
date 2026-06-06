from __future__ import annotations

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.api.database.session import SessionLocal
from src.api.services.auth_service import authenticate_user, get_user_by_id


ADMIN_SESSION_USER_ID_KEY = "admin_user_id"


def is_admin_role(role_name: str | None) -> bool:
    return role_name == "admin"


class AdminAuthBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username_or_email = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
        if not username_or_email or not password:
            return False

        with SessionLocal() as db:
            user = authenticate_user(db, username_or_email, password)
            if user is None or not is_admin_role(user.role.name):
                return False

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
