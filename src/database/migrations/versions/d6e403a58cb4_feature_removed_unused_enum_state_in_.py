"""feature: removed unused enum state in BotInteraction

Revision ID: d6e403a58cb4
Revises: ccb1ce9c3a90
Create Date: 2025-05-14 16:09:07.839093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6e403a58cb4'
down_revision: Union[str, None] = 'ccb1ce9c3a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
