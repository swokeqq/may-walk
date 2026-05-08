"""ORM модель опорного сегмента расчетной сети."""

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from may_walk.db.base import Base


class ReferenceSegment(Base):
    """Сегмент канонической расчетной сети на базе OSM."""

    __tablename__ = 'reference_segment'
    __table_args__ = (
        CheckConstraint(
            'surface_class IN '
            "('asphalt', 'forest_path', 'field_path', 'rail', 'other')",
            name='ck_reference_segment_surface_class',
        ),
        Index(
            'ix_reference_segment_geometry',
            'geometry',
            postgresql_using='gist',
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type='LINESTRING',
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    surface_class: Mapped[str] = mapped_column(String(32), nullable=False)


class ReferenceSegmentImportState(Base):
    """Состояние последнего импорта опорных сегментов."""

    __tablename__ = 'reference_segment_import_state'
    __table_args__ = (
        CheckConstraint(
            'id = 1',
            name='ck_reference_segment_import_state_singleton',
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
