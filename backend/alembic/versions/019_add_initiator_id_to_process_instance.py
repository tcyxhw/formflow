"""add initiator_id to process_instance

Revision ID: 019
Revises: 018
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa


revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'process_instance',
        sa.Column('initiator_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True, comment='发起人ID')
    )


def downgrade():
    op.drop_column('process_instance', 'initiator_id')