"""ORM модель администратора."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from may_walk.db.base import Base

if TYPE_CHECKING:
    from may_walk.models.auth_session import AuthSession


class AdminUser(Base):
    """Администратор (пользователь)."""

    __tablename__ = 'admin_user'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    sessions: Mapped[list['AuthSession']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
