"""add approve_threshold to flow_node

Revision ID: 017
Revises: 016
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa


revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'flow_node',
        sa.Column('approve_threshold', sa.Integer(), nullable=True, comment='percent策略阈值(1-100)')
    )


def downgrade():
    op.drop_column('flow_node', 'approve_threshold')
