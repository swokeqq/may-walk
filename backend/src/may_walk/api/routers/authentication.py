"""Endpoint'ы аутентификации."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from may_walk.api.dependencies import AUTH_COOKIE_NAME, AUTH_COOKIE_PATH, get_db
from may_walk.core.settings import settings
from may_walk.schemas.authentication import AuthStatusResponse, LoginRequest
from may_walk.services.authentication import (
    authenticate_admin,
    create_auth_session,
    get_valid_auth_session,
    revoke_auth_session,
)

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login', response_model=AuthStatusResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthStatusResponse | JSONResponse:
    """Войти по паролю администратора."""
    admin = authenticate_admin(db, request.password)
    if admin is None:
        return _unauthenticated_response()

    auth_session = create_auth_session(db, admin, settings.auth_session_ttl_hours)
    db.commit()

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=str(auth_session.id),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path=AUTH_COOKIE_PATH,
    )
    return AuthStatusResponse(authenticated=True)


@router.get('/status', response_model=AuthStatusResponse)
def auth_status(
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str | None, Cookie(alias=AUTH_COOKIE_NAME)] = None,
) -> AuthStatusResponse | JSONResponse:
    """Вернуть статус текущей auth-сессии."""
    if session_id is None:
        return _unauthenticated_response()

    try:
        parsed_session_id = UUID(session_id)
    except ValueError:
        return _unauthenticated_response()

    if get_valid_auth_session(db, parsed_session_id) is None:
        return _unauthenticated_response()

    return AuthStatusResponse(authenticated=True)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str | None, Cookie(alias=AUTH_COOKIE_NAME)] = None,
) -> Response:
    """Выйти из текущей auth-сессии."""
    if session_id is not None:
        try:
            parsed_session_id = UUID(session_id)
        except ValueError:
            parsed_session_id = None

        if parsed_session_id is not None:
            auth_session = get_valid_auth_session(db, parsed_session_id)
            if auth_session is not None:
                revoke_auth_session(auth_session)
                db.commit()

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


def _unauthenticated_response() -> JSONResponse:
    """Вернуть единый 401-ответ для невалидной auth-сессии."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=AuthStatusResponse(authenticated=False).model_dump(),
    )
