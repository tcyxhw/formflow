"""add department_post_level table

Revision ID: 020
Revises: 019
Create Date: 2025-03-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 department_post_level 表
    op.create_table(
        'department_post_level',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, comment='层级（越小越高）'),
        sa.ForeignKeyConstraint(['department_id'], ['department.id']),
        sa.ForeignKeyConstraint(['post_id'], ['position.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'department_id', 'post_id', name='uq_department_post_level')
    )
    
    # 创建索引
    op.create_index(op.f('ix_department_post_level_department_id'), 'department_post_level', ['department_id'], unique=False)
    op.create_index(op.f('ix_department_post_level_post_id'), 'department_post_level', ['post_id'], unique=False)
    op.create_index(op.f('ix_department_post_level_tenant_id'), 'department_post_level', ['tenant_id'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index(op.f('ix_department_post_level_tenant_id'), table_name='department_post_level')
    op.drop_index(op.f('ix_department_post_level_post_id'), table_name='department_post_level')
    op.drop_index(op.f('ix_department_post_level_department_id'), table_name='department_post_level')
    
    # 删除表
    op.drop_table('department_post_level')
