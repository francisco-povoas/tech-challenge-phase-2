"""add respondido_em and motivo_recusa to ordem_servico_orcamento

Revision ID: 20260503_01
Revises: f1a2b3c4d5e6
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260503_01'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ordem_servico_orcamento',
        sa.Column('respondido_em', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'ordem_servico_orcamento',
        sa.Column('motivo_recusa', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('ordem_servico_orcamento', 'motivo_recusa')
    op.drop_column('ordem_servico_orcamento', 'respondido_em')
