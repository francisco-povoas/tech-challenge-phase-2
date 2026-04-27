from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.shared.value_objects.password import Password
from app.modules.iam.domain.entities.usuario import Usuario
from app.modules.iam.domain.entities.usuario import UsuarioPerfil
from app.modules.iam.domain.filters.usuario import ListarUsuariosFiltro
from app.modules.iam.infrastructure.db.models.usuario import UsuarioModel
from app.modules.iam.infrastructure.db.models.usuario_perfil import UsuarioPerfilModel
from app.modules.iam.infrastructure.db.models.perfil import PerfilModel
from datetime import datetime, UTC

class UsuarioRepo:
    """Implementação concreta do repositório de usuários (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, usuario: Usuario) -> None:
        model = UsuarioModel(
            id=usuario.id.value,
            nome=usuario.nome,
            email=usuario.email.value,
            senha_hash=usuario.senha.value,
            criado_em=usuario.criado_em,
            atualizado_em=usuario.atualizado_em,
            ativo=usuario.ativo,
        )
        self.session.add(model)

    async def obter_por_email(self, email: Email) -> Optional[Usuario]:
        result = await self.session.exec(
            select(UsuarioModel).where(UsuarioModel.email == email.value)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_id(self, _id: ID) -> Optional[Usuario]:
        model = await self.session.get(UsuarioModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def atualizar(self, usuario: Usuario) -> Optional[Usuario]:
        model = await self.session.get(UsuarioModel, usuario.id.value)
        if not model:
            return None
        model.nome = usuario.nome
        model.email = usuario.email.value
        self.session.add(model)
        return usuario

    async def remover(self, _id: ID) -> bool:
        model = await self.session.get(UsuarioModel, _id.value)
        if not model:
            return False
        await self.session.delete(model)
        return True

    async def listar(self, filtros: ListarUsuariosFiltro) -> list[Usuario]:
        query = select(UsuarioModel)

        if filtros.nome:
            query = query.where(UsuarioModel.nome.ilike(f"%{filtros.nome}%"))
        if filtros.email:
            query = query.where(UsuarioModel.email == filtros.email)
        if filtros.ativo is not None:
            query = query.where(UsuarioModel.ativo == filtros.ativo)

        result = await self.session.exec(query)
        models = result.all()
        return [self._to_entity(model) for model in models]

    async def adicionar_perfil(self, usuario_perfil: UsuarioPerfil) -> None:
        model = UsuarioPerfilModel(
            id=usuario_perfil.id.value,
            usuario_id=usuario_perfil.usuario_id.value,
            perfil_id=usuario_perfil.perfil_id.value,
            criado_em=usuario_perfil.criado_em,
            )

        self.session.add(model)
        # commit na camada de aplicação (UoW) para garantir atomicidade

    async def listar_perfis_do_usuario(self, usuario_id: ID) -> list[str]:
        result = await self.session.exec(
            select(PerfilModel.nome)
            .join(UsuarioPerfilModel, UsuarioPerfilModel.perfil_id == PerfilModel.id)
            .where(UsuarioPerfilModel.usuario_id == usuario_id.value)
            .where(PerfilModel.ativo == True)  # noqa: E712
        )

        return list(result.all())

    @staticmethod
    def _to_entity(model: UsuarioModel) -> Usuario:
        return Usuario(
            id=ID.from_string(str(model.id)),
            nome=model.nome,
            email=Email(model.email),
            senha=Password(model.senha_hash),
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            ativo=model.ativo,
        )
