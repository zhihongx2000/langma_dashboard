from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    database_url = settings.database_url
    connect_args: dict[str, object] = {}

    if database_url.startswith("sqlite:///"):
        database_path = Path(database_url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False}

    return create_engine(database_url, future=True, connect_args=connect_args)


@lru_cache
def get_session_factory():
    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def clear_db_caches() -> None:
    get_session_factory.cache_clear()
    get_engine.cache_clear()
