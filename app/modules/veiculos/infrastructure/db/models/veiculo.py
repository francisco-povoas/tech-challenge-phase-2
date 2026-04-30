from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class VeiculoModel(SQLModel, table=True):
    """Modelo ORM da tabela de veículos."""

    __tablename__ = "veiculo"

    id: UUID = Field(primary_key=True)
    cliente_id: UUID = Field(
        sa_column=sa.Column(
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cliente.id"),
            nullable=False,
        )
    )
    placa: str = Field(
        sa_column=sa.Column(sa.String(10), nullable=False, unique=True)
    )
    marca: str = Field(sa_column=sa.Column(sa.String(60), nullable=False))
    modelo: str = Field(sa_column=sa.Column(sa.String(60), nullable=False))
    ano_fabricacao: Optional[int] = Field(
        default=None, sa_column=sa.Column(sa.SmallInteger(), nullable=True)
    )
    ano_modelo: Optional[int] = Field(
        default=None, sa_column=sa.Column(sa.SmallInteger(), nullable=True)
    )
    cor: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(30), nullable=True)
    )
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    atualizado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
