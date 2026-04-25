"""Ограничить таблицу администраторов одной записью."""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260425_000001'
down_revision: str | None = '20260424_000002'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Добавить уникальный индекс, разрешающий только одного администратора."""
    op.execute('CREATE UNIQUE INDEX uq_admin_user_singleton ON admin_user ((true))')


def downgrade() -> None:
    """Удалить ограничение на единственную запись администратора."""
    op.execute('DROP INDEX uq_admin_user_singleton')
