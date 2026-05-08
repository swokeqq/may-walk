"""Добавить состояние импорта опорных сегментов."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260508_000001'
down_revision: str | None = '20260425_000001'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Создать singleton-таблицу состояния импорта reference_segment."""
    op.create_table(
        'reference_segment_import_state',
        sa.Column('id', sa.SmallInteger(), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column(
            'imported_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            'id = 1', name='ck_reference_segment_import_state_singleton'
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Удалить состояние импорта reference_segment."""
    op.drop_table('reference_segment_import_state')
