from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.iam.domain.entities.perfil import Perfil
from app.modules.iam.infrastructure.db.models.perfil import PerfilModel


class PerfilRepo:
    """Implementação concreta do repositório de perfil (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def obter_por_nome(self, nome: str) -> Optional[Perfil]:
        result = await self.session.exec(
            select(PerfilModel).where(PerfilModel.nome == nome)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_id(self, _id: ID) -> Optional[Perfil]:
        model = await self.session.get(PerfilModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def listar(self) -> list[Perfil]:
        # retorna todos perfis sem filtros, pois não há filtros definidos para perfis
        result = await self.session.exec(select(PerfilModel))
        models = result.all()
        return [self._to_entity(model) for model in models]

    @staticmethod
    def _to_entity(model: PerfilModel) -> Perfil:
        return Perfil(
            id=ID.from_string(str(model.id)),
            nome=model.nome,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            ativo=model.ativo,
            descricao=model.descricao,
        )
