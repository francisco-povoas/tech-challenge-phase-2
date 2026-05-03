"""Modelo ORM da tabela ordem_servico_orcamento."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrdemServicoOrcamentoModel(SQLModel, table=True):
    """Modelo ORM do orçamento gerado a partir de uma OS."""

    __tablename__ = "ordem_servico_orcamento"

    id: UUID = Field(primary_key=True)
    ordem_servico_id: UUID = Field(
        sa_column=sa.Column(
            sa.Uuid,
            sa.ForeignKey("ordem_servico.id"),
            nullable=False,
            unique=True,
        )
    )
    status: str = Field(sa_column=sa.Column(sa.String(20), nullable=False))
    total_servicos: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(12, 2), nullable=False)
    )
    total_itens: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(12, 2), nullable=False)
    )
    total_geral: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(12, 2), nullable=False)
    )
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    atualizado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    comunicado_em: Optional[datetime] = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    observacao: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.Text, nullable=True)
    )
