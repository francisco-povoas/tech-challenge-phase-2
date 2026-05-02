"""Modelo ORM da tabela ordem_servico_servico."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrdemServicoServicoModel(SQLModel, table=True):
    """Modelo ORM do vínculo de serviço em uma Ordem de Serviço."""

    __tablename__ = "ordem_servico_servico"

    id: UUID = Field(primary_key=True)
    ordem_servico_id: UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("ordem_servico.id"), nullable=False)
    )
    servico_id: UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("catalogo_servico.id"), nullable=False)
    )
    nome_servico: str = Field(sa_column=sa.Column(sa.String(100), nullable=False))
    descricao_servico: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(255), nullable=True)
    )
    valor_unitario: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(10, 2), nullable=False)
    )
    tempo_estimado_minutos: int = Field(
        sa_column=sa.Column(sa.Integer, nullable=False)
    )
    tempo_executado_minutos: Optional[int] = Field(
        default=None, sa_column=sa.Column(sa.Integer, nullable=True)
    )
    observacao: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.Text, nullable=True)
    )
    cancelado: bool = Field(
        default=False, sa_column=sa.Column(sa.Boolean, nullable=False, default=False)
    )
