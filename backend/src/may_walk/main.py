"""Точка входа backend-приложения."""

from fastapi import FastAPI

from may_walk.api.router import api_router
from may_walk.core.settings import settings


def create_app() -> FastAPI:
    """Создать и настроить FastAPI приложение."""
    docs_url = '/docs' if settings.debug else None
    redoc_url = '/redoc' if settings.debug else None
    openapi_url = '/openapi.json' if settings.debug else None

    app = FastAPI(
        title='May Walk',
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.include_router(api_router)

    return app


app = create_app()
