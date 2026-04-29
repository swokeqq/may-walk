"""Cхемы ендпоинтов аутентификации."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Запрос входа пользователя."""

    password: str = Field(description='Пароль пользователя.')


class AuthStatusResponse(BaseModel):
    """Ответ с состоянием аутентификации."""

    authenticated: bool = Field(description='Флаг действующей auth-сессии.')
