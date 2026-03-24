"""add form permission system tables

Revision ID: 004
Revises: 003
Create Date: 2025-03-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 创建 user_department 中间表
    op.create_table(
        'user_department',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false', comment='是否为主属部门'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', 'department_id', name='uq_user_department')
    )
    op.create_index('idx_user_department_user', 'user_department', ['user_id'])
    op.create_index('idx_user_department_dept', 'user_department', ['department_id'])
    
    # 2. 迁移现有 User.department_id 数据到 user_department 表
    op.execute("""
        INSERT INTO user_department (tenant_id, user_id, department_id, is_primary, created_at, updated_at)
        SELECT tenant_id, id, department_id, TRUE, NOW(), NOW()
        FROM "user"
        WHERE department_id IS NOT NULL
    """)
    
    # 3. 为 form_permission 表添加 include_children 字段
    op.add_column('form_permission', 
        sa.Column('include_children', sa.Boolean(), nullable=True, server_default='true', comment='部门类型时是否包含子部门'))
    
    # 4. 更新存量数据：部门类型设为 TRUE，其他类型设为 NULL
    op.execute("""
        UPDATE form_permission 
        SET include_children = TRUE 
        WHERE grant_type = 'department'
    """)
    op.execute("""
        UPDATE form_permission 
        SET include_children = NULL 
        WHERE grant_type != 'department'
    """)
    
    # 5. 创建索引优化查询性能
    op.create_index('idx_form_permission_form_type_target', 
        'form_permission', ['form_id', 'grant_type', 'grantee_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_form_permission_form_type_target', table_name='form_permission')
    
    # 删除 include_children 字段
    op.drop_column('form_permission', 'include_children')
    
    # 删除 user_department 表索引和表
    op.drop_index('idx_user_department_dept', table_name='user_department')
    op.drop_index('idx_user_department_user', table_name='user_department')
    op.drop_table('user_department')
