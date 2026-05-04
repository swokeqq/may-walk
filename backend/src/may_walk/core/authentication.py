"""Базовая инфраструктура аутентификации."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

AUTH_COOKIE_NAME = 'mw_session'
AUTH_COOKIE_PATH = '/'

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Вернуть Argon2-хеш пароля."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль против Argon2-хеша."""
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
