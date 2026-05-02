from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class ClienteModel(SQLModel, table=True):
    """Modelo ORM da tabela de clientes."""

    __tablename__ = "cliente"

    id: UUID = Field(primary_key=True)
    tipo_pessoa: str = Field(sa_column=sa.Column(sa.CHAR(2), nullable=False))
    nome_razao_social: str = Field(sa_column=sa.Column(sa.String(150), nullable=False))
    cpf_cnpj: str = Field(
        sa_column=sa.Column(sa.String(14), nullable=False, unique=True)
    )
    telefone: str = Field(sa_column=sa.Column(sa.String(20), nullable=False))
    email: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(150), nullable=True)
    )
    cep: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(8), nullable=True)
    )
    logradouro: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(150), nullable=True)
    )
    numero: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(20), nullable=True)
    )
    complemento: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(100), nullable=True)
    )
    bairro: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(100), nullable=True)
    )
    cidade: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(100), nullable=True)
    )
    uf: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.CHAR(2), nullable=True)
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
