"""empty message

Revision ID: fe08569f402b
Revises: dcbe63544adc
Create Date: 2024-03-16 13:23:43.301669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe08569f402b'
down_revision: Union[str, None] = 'dcbe63544adc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'bank', ['name'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'bank', type_='unique')
    # ### end Alembic commands ###
