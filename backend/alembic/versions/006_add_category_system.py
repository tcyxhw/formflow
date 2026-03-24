"""add category system for form organization

Revision ID: 006
Revises: 005
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 category 表
    op.create_table(
        'category',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('name', sa.String(50), nullable=False, comment='分类名称'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false', comment='是否为默认分类'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_category_tenant_name')
    )
    
    # 创建索引
    op.create_index('idx_category_tenant', 'category', ['tenant_id'])
    
    # 添加 category_id 列到 form 表
    op.add_column('form', sa.Column('category_id', sa.Integer(), nullable=True, comment='分类ID'))
    
    # 添加外键约束
    op.create_foreign_key('fk_form_category_id', 'form', 'category', ['category_id'], ['id'], ondelete='SET NULL')
    
    # 更新 form 表的索引
    op.create_index('idx_form_tenant_category_id', 'form', ['tenant_id', 'category_id'])


def downgrade() -> None:
    # 删除 form 表的索引
    op.drop_index('idx_form_tenant_category_id', table_name='form')
    
    # 删除外键约束
    op.drop_constraint('fk_form_category_id', 'form', type_='foreignkey')
    
    # 删除 category_id 列
    op.drop_column('form', 'category_id')
    
    # 删除 category 表的索引
    op.drop_index('idx_category_tenant', table_name='category')
    
    # 删除 category 表
    op.drop_table('category')
