from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.api.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


database_url = make_url(DATABASE_URL)
engine_kwargs = {"pool_pre_ping": True}
if database_url.get_backend_name() == "sqlite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
