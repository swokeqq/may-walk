"""Эндпоинты проверки состояния сервиса."""

from fastapi import APIRouter

router = APIRouter(tags=['health'])


@router.get('/health')
def healthcheck() -> dict[str, str]:
    """Вернуть статус приложения."""
    return {'status': 'ok'}
