from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class ItemEstoqueModel(SQLModel, table=True):
    """Modelo ORM da tabela de itens de estoque."""

    __tablename__ = "item_estoque"

    id: UUID = Field(primary_key=True)
    tipo: str = Field(sa_column=sa.Column(sa.String(10), nullable=False))
    nome: str = Field(sa_column=sa.Column(sa.String(100), nullable=False))
    descricao: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(255), nullable=True)
    )
    codigo: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(50), nullable=True, unique=True)
    )
    quantidade_disponivel: int = Field(
        default=0, sa_column=sa.Column(sa.Integer, nullable=False, default=0)
    )
    quantidade_reservada: int = Field(
        default=0, sa_column=sa.Column(sa.Integer, nullable=False, default=0)
    )
    quantidade_minima: int = Field(
        default=0, sa_column=sa.Column(sa.Integer, nullable=False, default=0)
    )
    valor_unitario: Decimal = Field(
        sa_column=sa.Column(sa.Numeric(10, 2), nullable=False)
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
