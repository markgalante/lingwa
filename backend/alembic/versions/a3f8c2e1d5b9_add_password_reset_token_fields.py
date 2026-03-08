"""add password reset token fields

Revision ID: a3f8c2e1d5b9
Revises: 76fc1fd4c587
Create Date: 2026-03-08 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3f8c2e1d5b9'
down_revision: str | None = '76fc1fd4c587'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_reset_token_expires')
    op.drop_column('users', 'password_reset_token')
