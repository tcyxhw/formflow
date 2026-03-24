"""add reject_strategy field to flow_node

Revision ID: 008
Revises: 007
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 reject_strategy 列到 flow_node 表
    op.add_column(
        'flow_node',
        sa.Column(
            'reject_strategy',
            sa.String(20),
            nullable=False,
            server_default='TO_START',
            comment='驳回策略：TO_START/TO_PREVIOUS'
        )
    )


def downgrade() -> None:
    # 删除 reject_strategy 列
    op.drop_column('flow_node', 'reject_strategy')
