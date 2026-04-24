"""Создать таблицы администраторов, опорной сети, маршрутов и сессий."""

from typing import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260424_000002'
down_revision: str | None = '20260424_000001'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Создать таблицы администраторов, опорной сети, маршрутов и сессий."""
    op.create_table(
        'admin_user',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reference_segment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            'geometry',
            geoalchemy2.types.Geometry(
                geometry_type='LINESTRING',
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column('surface_class', sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            'surface_class IN '
            "('asphalt', 'forest_path', 'field_path', 'rail', 'other')",
            name='ck_reference_segment_surface_class',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'route',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column(
            'geometry',
            geoalchemy2.types.Geometry(
                geometry_type='MULTILINESTRING',
                srid=4326,
                spatial_index=False,
            ),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'auth_session',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['admin_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_reference_segment_geometry',
        'reference_segment',
        ['geometry'],
        unique=False,
        postgresql_using='gist',
    )
    op.create_index(
        'ix_route_geometry',
        'route',
        ['geometry'],
        unique=False,
        postgresql_using='gist',
    )
    op.create_index(
        'ix_auth_session_expires_at',
        'auth_session',
        ['expires_at'],
        unique=False,
    )
    op.create_index(
        'ix_auth_session_revoked_at',
        'auth_session',
        ['revoked_at'],
        unique=False,
    )
    op.create_index(
        'ix_auth_session_user_id',
        'auth_session',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    """Удалить таблицы администраторов, опорной сети, маршрутов и сессий."""
    op.drop_index('ix_auth_session_user_id', table_name='auth_session')
    op.drop_index('ix_auth_session_revoked_at', table_name='auth_session')
    op.drop_index('ix_auth_session_expires_at', table_name='auth_session')
    op.drop_index('ix_route_geometry', table_name='route', postgresql_using='gist')
    op.drop_index(
        'ix_reference_segment_geometry',
        table_name='reference_segment',
        postgresql_using='gist',
    )
    op.drop_table('auth_session')
    op.drop_table('route')
    op.drop_table('reference_segment')
    op.drop_table('admin_user')
