"""${message}

Revision ID: ${rev_id}
Revises: ${up_revision}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(rev_id)}
down_revision = ${repr(up_revision)}
branch_labels = ${repr(branch_labels)} if branch_labels else None
depends_on = ${repr(depends_on)} if depends_on else None


def upgrade() -> ${upgrades if upgrades else "pass"}


def downgrade() -> ${downgrades if downgrades else "pass"}