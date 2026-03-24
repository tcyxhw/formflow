"""add avatar_url to user

Revision ID: 018
Revises: 017
Create Date: 2026-03-23

"""
from alembic import op
import sqlalchemy as sa


revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('avatar_url', sa.String(500), nullable=True, comment='头像URL')
    )


def downgrade():
    op.drop_column('user', 'avatar_url')
