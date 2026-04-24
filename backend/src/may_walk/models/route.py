"""ORM модель маршрута."""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from may_walk.db.base import Base


class Route(Base):
    """Маршрут."""

    __tablename__ = 'route'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geometry: Mapped[object | None] = mapped_column(
        Geometry(
            geometry_type='MULTILINESTRING',
            srid=4326,
            spatial_index=False,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
