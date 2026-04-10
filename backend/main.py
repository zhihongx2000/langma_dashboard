from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.router import api_router
from backend.config.settings import get_settings
from backend.db.session import get_session_factory
from backend.services.bootstrap_service import initialize_database, seed_defaults


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    session_factory = get_session_factory()
    with session_factory() as db:
        seed_defaults(db)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(api_router, prefix=settings.api_prefix)
    return application


app = create_app()
