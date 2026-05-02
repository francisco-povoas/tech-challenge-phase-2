from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class ServicoModel(SQLModel, table=True):
    """Modelo ORM da tabela de catálogo de serviços."""

    __tablename__ = "catalogo_servico"

    id: UUID = Field(primary_key=True)
    nome: str = Field(sa_column=sa.Column(sa.String(100), nullable=False, unique=True))
    descricao: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(255), nullable=True)
    )
    valor_base: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(10, 2), nullable=False)
    )
    tempo_medio_minutos: int = Field(
        sa_column=sa.Column(sa.Integer, nullable=False)
    )
    ativo: bool = Field(
        default=True, sa_column=sa.Column(sa.Boolean, nullable=False, default=True)
    )
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    atualizado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
