"""Add missing idx_tenant_created index to workflow_operation_log

Revision ID: 013
Revises: 012
Create Date: 2026-03-16 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    """添加缺失的 idx_tenant_created 索引"""
    op.create_index(
        'idx_tenant_created',
        'workflow_operation_log',
        ['tenant_id', 'created_at']
    )


def downgrade():
    """回滚 idx_tenant_created 索引"""
    op.drop_index('idx_tenant_created', 'workflow_operation_log')
