"""Models mapping update cleanup

Revision ID: replace_me_with_hash
Revises: 135e3365ff14
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'user_device_model_cleanup'
down_revision: Union[str, None] = '135e3365ff14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop user columns
    op.drop_column('users', 'billing_address')
    op.drop_column('users', 'phone')

    # Make devices.greenhouse_id nullable
    op.alter_column('devices', 'greenhouse_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    # Re-add user columns
    op.add_column('users', sa.Column('phone', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('billing_address', sa.TEXT(), autoincrement=False, nullable=True))
    
    # Make devices.greenhouse_id non-nullable again
    op.alter_column('devices', 'greenhouse_id',
               existing_type=sa.INTEGER(),
               nullable=False)
