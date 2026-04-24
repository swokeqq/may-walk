"""ORM модель опорного сегмента расчетной сети."""

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from may_walk.db.base import Base


class ReferenceSegment(Base):
    """Сегмент канонической расчетной сети на базе OSM."""

    __tablename__ = 'reference_segment'
    __table_args__ = (
        CheckConstraint(
            "surface_class IN "
            "('asphalt', 'forest_path', 'field_path', 'rail', 'other')",
            name='ck_reference_segment_surface_class',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type='LINESTRING',
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    surface_class: Mapped[str] = mapped_column(String(32), nullable=False)
