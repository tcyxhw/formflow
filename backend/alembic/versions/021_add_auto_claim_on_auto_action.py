"""Add auto_claim_on_auto_action to flow_node

Revision ID: 021
Revises: 020
Create Date: 2026-04-04

"""
from alembic import op
import sqlalchemy as sa

revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'flow_node',
        sa.Column(
            'auto_claim_on_auto_action',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='自动审批时自动认领'
        )
    )


def downgrade() -> None:
    op.drop_column('flow_node', 'auto_claim_on_auto_action')