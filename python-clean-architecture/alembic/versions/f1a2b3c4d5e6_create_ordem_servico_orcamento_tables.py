"""create ordem_servico_orcamento and ordem_servico_orcamento_comunicacao tables

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela: ordem_servico_orcamento
    op.create_table(
        'ordem_servico_orcamento',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('ordem_servico_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('total_servicos', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_itens', sa.Numeric(12, 2), nullable=False),
        sa.Column('total_geral', sa.Numeric(12, 2), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comunicado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['ordem_servico_id'], ['ordem_servico.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ordem_servico_id', name='uq_ordem_servico_orcamento_ordem_servico_id'),
    )
    op.create_index(
        'ix_ordem_servico_orcamento_ordem_servico_id',
        'ordem_servico_orcamento',
        ['ordem_servico_id'],
    )

    # Tabela: ordem_servico_orcamento_comunicacao
    op.create_table(
        'ordem_servico_orcamento_comunicacao',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('orcamento_id', sa.Uuid(), nullable=False),
        sa.Column('ordem_servico_id', sa.Uuid(), nullable=False),
        sa.Column('canal', sa.String(20), nullable=False),
        sa.Column('destino', sa.String(255), nullable=False),
        sa.Column('sucesso', sa.Boolean(), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=False),
        sa.Column('provedor', sa.String(50), nullable=False),
        sa.Column('referencia_externa', sa.String(255), nullable=True),
        sa.Column('enviado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['orcamento_id'], ['ordem_servico_orcamento.id']),
        sa.ForeignKeyConstraint(['ordem_servico_id'], ['ordem_servico.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_ordem_servico_orcamento_comunicacao_orcamento_id',
        'ordem_servico_orcamento_comunicacao',
        ['orcamento_id'],
    )
    op.create_index(
        'ix_ordem_servico_orcamento_comunicacao_ordem_servico_id',
        'ordem_servico_orcamento_comunicacao',
        ['ordem_servico_id'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_ordem_servico_orcamento_comunicacao_ordem_servico_id',
        table_name='ordem_servico_orcamento_comunicacao',
    )
    op.drop_index(
        'ix_ordem_servico_orcamento_comunicacao_orcamento_id',
        table_name='ordem_servico_orcamento_comunicacao',
    )
    op.drop_table('ordem_servico_orcamento_comunicacao')

    op.drop_index(
        'ix_ordem_servico_orcamento_ordem_servico_id',
        table_name='ordem_servico_orcamento',
    )
    op.drop_table('ordem_servico_orcamento')
