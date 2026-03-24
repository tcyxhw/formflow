"""Extend task table with task_type and comment

Revision ID: 012
Revises: 011
Create Date: 2026-03-16 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    """扩展 task 表，添加 task_type 和 comment 字段"""
    op.add_column('task', 
        sa.Column('task_type', sa.String(20), server_default='approve', 
                  comment='任务类型：approve/cc'))
    op.add_column('task', 
        sa.Column('comment', sa.String(500), nullable=True, 
                  comment='审批意见'))


def downgrade():
    """回滚 task 表扩展"""
    op.drop_column('task', 'comment')
    op.drop_column('task', 'task_type')
