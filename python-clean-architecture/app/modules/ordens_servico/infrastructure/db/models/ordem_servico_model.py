"""Modelo ORM da tabela ordem_servico."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrdemServicoModel(SQLModel, table=True):
    """Modelo ORM da tabela de Ordens de Serviço."""

    __tablename__ = "ordem_servico"

    id: UUID = Field(primary_key=True)
    cliente_id: UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("cliente.id"), nullable=False)
    )
    veiculo_id: UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("veiculo.id"), nullable=False)
    )
    status: str = Field(sa_column=sa.Column(sa.String(30), nullable=False))
    queixa_inicial: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    diagnostico: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.Text, nullable=True)
    )
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    atualizado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    iniciado_diagnostico_em: Optional[datetime] = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    diagnostico_concluido_em: Optional[datetime] = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )

    # Campos de pagamento
    pagamento_registrado_em: Optional[datetime] = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    forma_pagamento: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(30), nullable=True)
    )
    valor_pago: Optional[Decimal] = Field(
        default=None,
        sa_column=sa.Column(sa.Numeric(precision=12, scale=2), nullable=True),
    )
    pagamento_observacao: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.Text, nullable=True)
    )
