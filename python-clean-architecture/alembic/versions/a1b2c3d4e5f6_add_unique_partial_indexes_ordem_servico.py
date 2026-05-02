"""add unique partial indexes to ordem_servico_servico and ordem_servico_item

Revision ID: a1b2c3d4e5f6
Revises: 52bbdccca29d
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '52bbdccca29d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice único parcial: impede que o mesmo serviço seja adicionado duas vezes
    # de forma ativa na mesma OS (cancelado = false).
    op.create_index(
        "uq_ordem_servico_servico_ativo",
        "ordem_servico_servico",
        ["ordem_servico_id", "servico_id"],
        unique=True,
        postgresql_where=sa.text("cancelado = false"),
    )

    # Índice único parcial: impede que o mesmo item de estoque seja adicionado
    # duas vezes de forma ativa na mesma OS (status != 'CANCELADO').
    op.create_index(
        "uq_ordem_servico_item_ativo",
        "ordem_servico_item",
        ["ordem_servico_id", "item_estoque_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'CANCELADO'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_ordem_servico_item_ativo",
        table_name="ordem_servico_item",
    )
    op.drop_index(
        "uq_ordem_servico_servico_ativo",
        table_name="ordem_servico_servico",
    )
