"""Сервисные операции с администратором."""

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from may_walk.models.admin_user import AdminUser


def create_admin(session: Session, password: str) -> AdminUser:
    """Создать первого и единственного администратора."""
    admin_exists = session.scalar(select(AdminUser.id).limit(1)) is not None
    if admin_exists:
        raise ValueError('Администратор уже создан')

    password_hash = PasswordHasher().hash(password)
    admin = AdminUser(password_hash=password_hash)
    session.add(admin)
    return admin
