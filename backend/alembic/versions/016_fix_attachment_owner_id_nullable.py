"""fix: allow owner_id nullable for temp attachments

Revision ID: 016
Revises: 015
Create Date: 2024-03-22 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 修改 attachment 表的 owner_id 列，允许 NULL
    op.alter_column('attachment', 'owner_id',
               existing_type=sa.Integer(),
               nullable=True,
               comment='归属ID')


def downgrade() -> None:
    # 回滚：将 owner_id 列改回 NOT NULL
    # 注意：如果存在 NULL 值，回滚会失败
    op.alter_column('attachment', 'owner_id',
               existing_type=sa.Integer(),
               nullable=False,
               comment='归属ID')
