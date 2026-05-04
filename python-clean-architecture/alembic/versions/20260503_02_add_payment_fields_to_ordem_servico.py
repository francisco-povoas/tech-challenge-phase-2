"""add payment fields to ordem_servico

Revision ID: 20260503_02
Revises: 20260503_01
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260503_02'
down_revision: Union[str, Sequence[str], None] = '20260503_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'ordem_servico',
        sa.Column('pagamento_registrado_em', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'ordem_servico',
        sa.Column('forma_pagamento', sa.String(length=30), nullable=True),
    )
    op.add_column(
        'ordem_servico',
        sa.Column('valor_pago', sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        'ordem_servico',
        sa.Column('pagamento_observacao', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('ordem_servico', 'pagamento_observacao')
    op.drop_column('ordem_servico', 'valor_pago')
    op.drop_column('ordem_servico', 'forma_pagamento')
    op.drop_column('ordem_servico', 'pagamento_registrado_em')
