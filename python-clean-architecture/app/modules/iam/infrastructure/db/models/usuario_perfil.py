from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel
import sqlalchemy as sa

class UsuarioPerfilModel(SQLModel, table=True):
    """Modelo ORM da tabela de usuários e perfis."""

    __tablename__ = "usuario_perfil"
    __table_args__ = (
        sa.UniqueConstraint("usuario_id", "perfil_id", name="uix_usuario_perfil"),
    )

    id: UUID = Field(primary_key=True)
    usuario_id: UUID = Field(foreign_key="usuario.id")
    perfil_id: UUID = Field(foreign_key="perfil.id")
    criado_em: datetime = Field(
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False)
    )
