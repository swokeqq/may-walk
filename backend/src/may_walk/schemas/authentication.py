"""Cхемы ендпоинтов аутентификации."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Запрос входа администратора."""

    password: str


class AuthStatusResponse(BaseModel):
    """Ответ с состоянием аутентификации."""

    authenticated: bool
