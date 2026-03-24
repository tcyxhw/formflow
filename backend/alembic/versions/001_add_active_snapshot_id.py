"""add active_snapshot_id

Revision ID: 001
Revises: 
Create Date: 2024-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 active_snapshot_id 字段到 flow_definition 表
    op.add_column('flow_definition', sa.Column('active_snapshot_id', sa.Integer(), nullable=True))
    # 添加外键约束
    op.create_foreign_key('fk_flow_definition_active_snapshot', 'flow_definition', 'flow_snapshot', ['active_snapshot_id'], ['id'])


def downgrade() -> None:
    # 删除外键约束
    op.drop_constraint('fk_flow_definition_active_snapshot', 'flow_definition', type_='foreignkey')
    # 删除字段
    op.drop_column('flow_definition', 'active_snapshot_id')