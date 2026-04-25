"""Общие FastAPI зависимости."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from may_walk.db.session import SessionLocal


def get_db() -> Generator[Session]:
    """Выдать SQLAlchemy сессию на время обработки запроса."""
    with SessionLocal() as session:
        yield session
