"""removed_user_document

Revision ID: 911c66a91178
Revises: 9dfc110ccf47
Create Date: 2025-05-21 17:00:05.927809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '911c66a91178'
down_revision: Union[str, None] = '9dfc110ccf47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
