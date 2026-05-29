from __future__ import annotations

from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.api.config import AUTH_ACCESS_TOKEN_EXPIRE_MINUTES, AUTH_ALGORITHM, AUTH_SECRET_KEY
from src.api.database.models import User, UserRole
from src.api.database.session import SessionLocal
from src.api.schemas import AuthUserResponse, RegisterRequest


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user: User) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expires_at,
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)


def decode_user_id(token: str) -> int:
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Token subject is missing")
        return int(subject)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        created_at=user.created_at,
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.id == user_id)
        .first()
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_user_id(credentials.credentials)
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        db.expunge(user)
        db.expunge(user.role)
        return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    if credentials is None:
        return None
    return get_current_user(credentials)


def register_user(db: Session, request: RegisterRequest) -> User:
    username = request.username.strip()
    email = request.email.strip().lower()

    existing = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .first()
    )
    if existing is not None:
        detail = "Username already exists" if existing.username == username else "Email already exists"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    role = db.query(UserRole).filter(UserRole.name == "user").first()
    if role is None:
        role = UserRole(name="user")
        db.add(role)
        db.flush()

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(request.password),
        created_at=datetime.utcnow(),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username_or_email: str, password: str) -> User | None:
    identifier = username_or_email.strip()
    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(or_(User.username == identifier, User.email == identifier.lower()))
        .first()
    )
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
