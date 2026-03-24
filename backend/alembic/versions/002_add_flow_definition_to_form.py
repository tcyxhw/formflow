"""add flow_definition_id to form table

Revision ID: 002
Revises: 001
Create Date: 2024-01-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 flow_definition_id 字段到 form 表
    op.add_column('form', sa.Column('flow_definition_id', sa.Integer(), nullable=True))
    # 添加外键约束
    op.create_foreign_key('fk_form_flow_definition', 'form', 'flow_definition', ['flow_definition_id'], ['id'])


def downgrade() -> None:
    # 删除外键约束
    op.drop_constraint('fk_form_flow_definition', 'form', type_='foreignkey')
    # 删除字段
    op.drop_column('form', 'flow_definition_id')
