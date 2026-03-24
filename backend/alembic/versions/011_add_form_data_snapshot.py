"""Add form_data_snapshot to process_instance

Revision ID: 011
Revises: 010
Create Date: 2026-03-16 14:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """添加 form_data_snapshot 字段到 process_instance 表"""
    op.add_column('process_instance', 
        sa.Column('form_data_snapshot', postgresql.JSONB(), nullable=True, 
                  comment='表单数据快照'))


def downgrade():
    """回滚 form_data_snapshot 字段"""
    op.drop_column('process_instance', 'form_data_snapshot')
