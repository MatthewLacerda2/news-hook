"""unifying httpmethod enum

Revision ID: d6153d5b8015
Revises: 17a16ffb1457
Create Date: 2025-05-28 17:56:55.392531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd6153d5b8015'
down_revision: Union[str, None] = '17a16ffb1457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create a temporary column
    op.add_column('alert_prompts', sa.Column('http_method_new', sa.String(), nullable=True))
    
    # Copy data to the temporary column
    op.execute("UPDATE alert_prompts SET http_method_new = http_method::text")
    
    # Drop the old column
    op.drop_column('alert_prompts', 'http_method')
    
    # Create new enum type
    http_method = postgresql.ENUM('POST', 'PUT', 'PATCH', name='httpmethod', create_type=False)
    http_method.drop(op.get_bind(), checkfirst=True)
    http_method = postgresql.ENUM('POST', 'PUT', 'PATCH', name='httpmethod', create_type=True)
    
    # Add new column with new enum type
    op.add_column('alert_prompts', sa.Column('http_method', sa.Enum('POST', 'PUT', 'PATCH', name='httpmethod'), nullable=False, server_default='POST'))
    
    # Copy data back
    op.execute("UPDATE alert_prompts SET http_method = http_method_new::httpmethod")
    
    # Drop temporary column
    op.drop_column('alert_prompts', 'http_method_new')


def downgrade() -> None:
    """Downgrade schema."""
    # Create a temporary column
    op.add_column('alert_prompts', sa.Column('http_method_old', sa.String(), nullable=True))
    
    # Copy data to the temporary column
    op.execute("UPDATE alert_prompts SET http_method_old = http_method::text")
    
    # Drop the old column
    op.drop_column('alert_prompts', 'http_method')
    
    # Recreate old enum type
    http_method = postgresql.ENUM('POST', 'PUT', 'PATCH', name='httpmethod', create_type=False)
    http_method.drop(op.get_bind(), checkfirst=True)
    http_method = postgresql.ENUM('POST', 'PUT', 'PATCH', name='httpmethod', create_type=True)
    
    # Add column with old enum type
    op.add_column('alert_prompts', sa.Column('http_method', sa.Enum('POST', 'PUT', 'PATCH', name='httpmethod'), nullable=False, server_default='POST'))
    
    # Copy data back
    op.execute("UPDATE alert_prompts SET http_method = http_method_old::httpmethod")
    
    # Drop temporary column
    op.drop_column('alert_prompts', 'http_method_old')
