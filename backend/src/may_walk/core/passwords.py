"""Хеширование и проверка паролей."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Вернуть Argon2-хеш пароля."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль против Argon2-хеша."""
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
