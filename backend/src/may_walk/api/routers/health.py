"""Эндпоинты проверки состояния сервиса."""

from fastapi import APIRouter

from may_walk.schemas.health import HealthResponse

router = APIRouter(tags=['health'])


@router.get('/health', response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    """Вернуть статус приложения."""
    return HealthResponse(status='ok')
