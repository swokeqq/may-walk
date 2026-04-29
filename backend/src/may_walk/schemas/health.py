"""Схемы ендпоинтов проверки состояния."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Ответ проверки состояния приложения."""

    status: Literal['ok'] = Field(description='Статус приложения.')
