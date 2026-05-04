"""Схемы статистики маршрутов."""

from pydantic import BaseModel, Field


class RouteStatsResponse(BaseModel):
    """Статистика маршрута по классам покрытия."""

    asphalt_m: float = Field(description='Длина асфальтовых участков в метрах.')
    forest_path_m: float = Field(description='Длина лесных троп в метрах.')
    field_path_m: float = Field(description='Длина полевых троп в метрах.')
    rail_m: float = Field(description='Длина железнодорожных участков в метрах.')
    other_m: float = Field(description='Длина прочих участков в метрах.')
    total_m: float = Field(description='Общая длина учтенных участков в метрах.')
