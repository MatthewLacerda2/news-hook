"""add_user_document_enum

Revision ID: add_user_document_enum
Revises: 37e634688625
Create Date: 2025-05-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_user_document_enum'
down_revision: Union[str, None] = '37e634688625'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add USER_DOCUMENT back to datasource enum."""
    # Create a new enum type with the USER_DOCUMENT value
    op.execute("ALTER TYPE datasource ADD VALUE 'USER_DOCUMENT'")


def downgrade() -> None:
    """
    Cannot safely downgrade - would need to remove all USER_DOCUMENT values first.
    """
    pass  # Cannot safely remove enum value if it's in use 