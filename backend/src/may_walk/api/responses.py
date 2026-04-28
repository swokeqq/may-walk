"""Общие OpenAPI-описания ответов API."""

UNAUTHORIZED_RESPONSE = {'description': 'Необходима cookie-аутентификация mw_session.'}
ROUTE_NOT_FOUND_RESPONSE = {'description': 'Маршрут не найден.'}
INVALID_ROUTE_GEOMETRY_RESPONSE = {
    'description': 'Невалидная геометрия маршрута.',
}


def protected_responses(
    responses: dict[int, dict[str, object]] | None = None,
) -> dict[int, dict[str, object]]:
    """Добавить описание 401 к ответам защищенного endpoint'а."""
    return {401: UNAUTHORIZED_RESPONSE, **(responses or {})}
