"""Сервисные операции аутентификации."""

from datetime import UTC, datetime, timedelta

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
