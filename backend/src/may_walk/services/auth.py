"""Сервисные операции аутентификации."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from may_walk.core.passwords import verify_password
from may_walk.models.admin_user import AdminUser
from may_walk.models.auth_session import AuthSession


def authenticate_admin(session: Session, password: str) -> AdminUser | None:
    """Вернуть администратора, если пароль корректен."""
    admin = session.scalar(select(AdminUser).limit(1))
    if admin is None or not verify_password(password, admin.password_hash):
        return None

    return admin


def create_auth_session(
    session: Session,
    admin: AdminUser,
    ttl_hours: int,
) -> AuthSession:
    """Создать серверную auth-сессию администратора."""
    auth_session = AuthSession(
        user_id=admin.id,
        expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
    )
    session.add(auth_session)
    return auth_session


def get_valid_auth_session(session: Session, session_id: UUID) -> AuthSession | None:
    """Вернуть auth-сессию, если она существует, активна и не истекла."""
    auth_session = session.get(AuthSession, session_id)
    if auth_session is None:
        return None
    if auth_session.revoked_at is not None:
        return None
    if auth_session.expires_at <= datetime.now(UTC):
        return None

    return auth_session
