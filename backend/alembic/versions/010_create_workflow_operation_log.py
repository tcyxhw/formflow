"""Create workflow_operation_log table

Revision ID: 010
Revises: 009
Create Date: 2026-03-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    """创建 workflow_operation_log 表"""
    op.create_table(
        'workflow_operation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_instance_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(20), nullable=False, comment='操作类型：SUBMIT/APPROVE/REJECT/CANCEL/CC'),
        sa.Column('operator_id', sa.Integer(), nullable=False, comment='操作人ID'),
        sa.Column('comment', sa.String(500), nullable=True, comment='操作备注'),
        sa.Column('detail_json', postgresql.JSONB(), nullable=True, comment='操作详情'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['process_instance_id'], ['process_instance.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_instance_created', 'workflow_operation_log', 
                    ['process_instance_id', 'created_at'])
    op.create_index('idx_operation_type', 'workflow_operation_log', 
                    ['operation_type', 'created_at'])


def downgrade():
    """回滚 workflow_operation_log 表"""
    op.drop_index('idx_operation_type', 'workflow_operation_log')
    op.drop_index('idx_instance_created', 'workflow_operation_log')
    op.drop_table('workflow_operation_log')
