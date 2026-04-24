"""Точка входа backend-приложения."""

from fastapi import FastAPI

from may_walk.api.router import api_router


def create_app() -> FastAPI:
    """Создать и настроить FastAPI приложение."""
    app = FastAPI(title='May Walk')
    app.include_router(api_router)
    return app


app = create_app()
