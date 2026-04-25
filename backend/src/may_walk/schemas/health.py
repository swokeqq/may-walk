"""Схемы ендпоинтов проверки состояния."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Ответ проверки состояния приложения."""

    status: Literal['ok']
