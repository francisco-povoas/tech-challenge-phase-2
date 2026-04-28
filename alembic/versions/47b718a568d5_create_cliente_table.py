"""create cliente table

Revision ID: 47b718a568d5
Revises: 692e8bc96fc1
Create Date: 2026-04-28 00:44:59.903264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '47b718a568d5'
down_revision: Union[str, Sequence[str], None] = '692e8bc96fc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tipo_pessoa", sa.CHAR(length=2), nullable=False),
        sa.Column("nome_razao_social", sa.String(length=150), nullable=False),
        sa.Column("cpf_cnpj", sa.String(length=14), nullable=False),
        sa.Column("telefone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("cep", sa.String(length=8), nullable=True),
        sa.Column("logradouro", sa.String(length=150), nullable=True),
        sa.Column("numero", sa.String(length=20), nullable=True),
        sa.Column("complemento", sa.String(length=100), nullable=True),
        sa.Column("bairro", sa.String(length=100), nullable=True),
        sa.Column("cidade", sa.String(length=100), nullable=True),
        sa.Column("uf", sa.CHAR(length=2), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cpf_cnpj", name="uq_cliente_cpf_cnpj"),
        sa.CheckConstraint("tipo_pessoa IN ('PF', 'PJ')", name="ck_cliente_tipo_pessoa"),
    )


def downgrade() -> None:
    op.drop_table("cliente")
