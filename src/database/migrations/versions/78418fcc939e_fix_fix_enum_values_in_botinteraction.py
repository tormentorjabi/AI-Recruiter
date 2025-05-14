"""fix: fix enum values in BotInteraction

Revision ID: 78418fcc939e
Revises: d6e403a58cb4
Create Date: 2025-05-14 16:14:17.437479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78418fcc939e'
down_revision: Union[str, None] = 'd6e403a58cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE interactionstate ADD VALUE 'NO_CONSENT'")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        ALTER TABLE bot_interactions ALTER COLUMN state TYPE TEXT;
        DROP TYPE interactionstate;
        CREATE TYPE interactionstate AS ENUM ('STARTED', 'ANSWERING', 'REVIEW', 'COMPLETED', 'PAUSED');
        UPDATE bot_interactions SET state = 'COMPLETED' WHERE state = 'NO_CONSENT';
        ALTER TABLE bot_interactions ALTER COLUMN state TYPE interactionstate USING state::interactionstate;
    """)
