"""Auth ендпоинты."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from may_walk.api.dependencies import get_db
from may_walk.core.settings import settings
from may_walk.schemas.auth import AuthStatusResponse, LoginRequest
from may_walk.services.auth import authenticate_admin, create_auth_session

AUTH_COOKIE_NAME = 'mw_session'
AUTH_COOKIE_PATH = '/'

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login', response_model=AuthStatusResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthStatusResponse:
    """Войти по паролю администратора."""
    admin = authenticate_admin(db, request.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
        )

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
