"""add user quick access table

Revision ID: 005
Revises: 004
Create Date: 2025-03-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 user_quick_access 表
    op.create_table(
        'user_quick_access',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('form_id', sa.Integer(), nullable=False, comment='表单ID'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序顺序，数值越小越靠前'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['form_id'], ['form.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', 'form_id', name='uq_user_quick_access')
    )
    
    # 创建索引优化查询性能
    op.create_index('idx_user_quick_access_user', 'user_quick_access', ['user_id', 'tenant_id'])
    op.create_index('idx_user_quick_access_form', 'user_quick_access', ['form_id'])
    op.create_index('idx_user_quick_access', 'user_quick_access', ['tenant_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_user_quick_access', table_name='user_quick_access')
    op.drop_index('idx_user_quick_access_form', table_name='user_quick_access')
    op.drop_index('idx_user_quick_access_user', table_name='user_quick_access')
    
    # 删除表
    op.drop_table('user_quick_access')
