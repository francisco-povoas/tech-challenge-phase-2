from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel
import sqlalchemy as sa

class PerfilModel(SQLModel, table=True):
    """Modelo ORM da tabela de perfil."""

    __tablename__ = "perfil"


    id: UUID = Field(primary_key=True)
    nome: str = Field(unique=True, max_length=30)
    descricao: str = Field(max_length=150)
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    atualizado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
    ativo: bool = Field(default=True, nullable=False)
