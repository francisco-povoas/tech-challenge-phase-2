"""Modelo ORM da tabela ordem_servico_orcamento_comunicacao."""

from datetime import datetime
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class OrdemServicoOrcamentoComunicacaoModel(SQLModel, table=True):
    """Modelo ORM do registro de comunicação do orçamento ao cliente."""

    __tablename__ = "ordem_servico_orcamento_comunicacao"

    id: UUID = Field(primary_key=True)
    orcamento_id: UUID = Field(
        sa_column=sa.Column(
            sa.Uuid,
            sa.ForeignKey("ordem_servico_orcamento.id"),
            nullable=False,
        )
    )
    ordem_servico_id: UUID = Field(
        sa_column=sa.Column(
            sa.Uuid,
            sa.ForeignKey("ordem_servico.id"),
            nullable=False,
        )
    )
    canal: str = Field(sa_column=sa.Column(sa.String(20), nullable=False))
    destino: str = Field(sa_column=sa.Column(sa.String(255), nullable=False))
    sucesso: bool = Field(sa_column=sa.Column(sa.Boolean, nullable=False))
    mensagem: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    provedor: str = Field(sa_column=sa.Column(sa.String(50), nullable=False))
    referencia_externa: Optional[str] = Field(
        default=None, sa_column=sa.Column(sa.String(255), nullable=True)
    )
    enviado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
