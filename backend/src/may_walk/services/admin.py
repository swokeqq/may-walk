"""Сервисные операции с администратором."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from may_walk.core.passwords import hash_password
from may_walk.models.admin_user import AdminUser


def create_admin(session: Session, password: str) -> AdminUser:
    """Создать первого и единственного администратора."""
    admin_exists = session.scalar(select(AdminUser.id).limit(1)) is not None
    if admin_exists:
        raise ValueError('Администратор уже создан')

    admin = AdminUser(password_hash=hash_password(password))
    session.add(admin)
    return admin
