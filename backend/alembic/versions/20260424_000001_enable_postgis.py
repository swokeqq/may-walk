"""Включить расширение PostGIS."""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260424_000001'
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Включить расширение PostGIS."""
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')


def downgrade() -> None:
    """Удалить расширение PostGIS."""
    op.execute('DROP EXTENSION IF EXISTS postgis')
