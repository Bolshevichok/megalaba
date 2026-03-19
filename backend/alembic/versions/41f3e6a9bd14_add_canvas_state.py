"""Add canvas_state to greenhouses

Revision ID: 41f3e6a9bd14
Revises: user_device_model_cleanup
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41f3e6a9bd14'
down_revision: Union[str, None] = 'user_device_model_cleanup'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('greenhouses', sa.Column('canvas_state', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('greenhouses', 'canvas_state')
