"""Общие FastAPI зависимости."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session

from may_walk.core.authentication import AUTH_COOKIE_NAME
from may_walk.db.session import SessionLocal
from may_walk.models.auth_session import AuthSession
from may_walk.services.authentication import get_valid_auth_session

auth_cookie = APIKeyCookie(
    name=AUTH_COOKIE_NAME,
    scheme_name=AUTH_COOKIE_NAME,
    auto_error=False,
)


def get_db() -> Generator[Session]:
    """Выдать SQLAlchemy сессию на время обработки запроса."""
    with SessionLocal() as session:
        yield session


def require_auth(
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str | None, Security(auth_cookie)] = None,
) -> AuthSession:
    """Потребовать валидную auth-сессию для защищенного endpoint'а."""
    if session_id is None:
        _raise_unauthorized()

    try:
        parsed_session_id = UUID(session_id)
    except ValueError:
        _raise_unauthorized()

    auth_session = get_valid_auth_session(db, parsed_session_id)
    if auth_session is None:
        _raise_unauthorized()

    return auth_session


def _raise_unauthorized() -> None:
    """Прервать запрос единым 401 для защищенных endpoint'ов."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Not authenticated',
    )
