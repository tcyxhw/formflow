"""fix workflow tenant_id

Revision ID: 003
Revises: 002
Create Date: 2024-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 为所有 workflow 表设置 tenant_id 字段可以为空，并设置默认值
    tables = ['flow_definition', 'flow_node', 'flow_route', 'flow_snapshot', 'process_instance', 'task', 'task_action_log']
    for table in tables:
        # 先设置为可空
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP NOT NULL")
        # 设置默认值
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT 1")
        # 设置为不可空
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")


def downgrade() -> None:
    pass