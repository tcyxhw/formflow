"""add condition_branches field to flow_node

Revision ID: 009
Revises: 008
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 condition_branches 列到 flow_node 表
    op.add_column(
        'flow_node',
        sa.Column(
            'condition_branches',
            sa.JSON,
            nullable=True,
            comment='条件分支配置：{"branches": [...], "default_target_node_id": ...}'
        )
    )


def downgrade() -> None:
    # 删除 condition_branches 列
    op.drop_column('flow_node', 'condition_branches')
