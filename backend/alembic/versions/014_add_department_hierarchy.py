"""添加部门层级支持：is_root字段、department_post表、user_department_post表

Revision ID: 014
Revises: 013
Create Date: 2026-03-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 添加department表的is_root和sort_order字段
    op.add_column('department', sa.Column('is_root', sa.Boolean(), nullable=False, server_default='false', comment='是否是根部门'))
    op.add_column('department', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0', comment='排序'))
    
    # 2. 创建department_post表
    op.create_table('department_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False, comment='部门ID'),
        sa.Column('post_id', sa.Integer(), nullable=False, comment='岗位ID'),
        sa.Column('is_head', sa.Boolean(), nullable=False, server_default='false', comment='是否是主负责人岗位'),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['position.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'department_id', 'post_id', name='uq_department_post')
    )
    op.create_index(op.f('ix_department_post_id'), 'department_post', ['id'], unique=False)
    
    # 3. 创建user_department_post表
    op.create_table('user_department_post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('department_id', sa.Integer(), nullable=False, comment='部门ID'),
        sa.Column('post_id', sa.Integer(), nullable=True, comment='岗位ID（学生可为空）'),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.ForeignKeyConstraint(['post_id'], ['position.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'user_id', 'department_id', 'post_id', name='uq_user_department_post')
    )
    op.create_index(op.f('ix_user_department_post_id'), 'user_department_post', ['id'], unique=False)


def downgrade() -> None:
    # 1. 删除user_department_post表
    op.drop_index(op.f('ix_user_department_post_id'), table_name='user_department_post')
    op.drop_table('user_department_post')
    
    # 2. 删除department_post表
    op.drop_index(op.f('ix_department_post_id'), table_name='department_post')
    op.drop_table('department_post')
    
    # 3. 删除department表的is_root和sort_order字段
    op.drop_column('department', 'sort_order')
    op.drop_column('department', 'is_root')
