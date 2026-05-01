from decimal import Decimal
from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
from app.modules.servicos.infrastructure.db.models.servico import ServicoModel


class ServicoRepo:
    """Implementação concreta do repositório de serviços (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, servico: Servico) -> None:
        model = ServicoModel(
            id=servico.id.value,
            nome=servico.nome,
            descricao=servico.descricao,
            valor_base=servico.valor_base,
            tempo_medio_minutos=servico.tempo_medio_minutos,
            ativo=servico.ativo,
            criado_em=servico.criado_em,
            atualizado_em=servico.atualizado_em,
        )
        self.session.add(model)

    async def obter_por_id(self, _id: ID) -> Optional[Servico]:
        model = await self.session.get(ServicoModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_nome(self, nome: str) -> Optional[Servico]:
        result = await self.session.exec(
            select(ServicoModel).where(ServicoModel.nome == nome)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def atualizar(self, servico: Servico) -> Optional[Servico]:
        model = await self.session.get(ServicoModel, servico.id.value)
        if not model:
            return None
        model.nome = servico.nome
        model.descricao = servico.descricao
        model.valor_base = servico.valor_base
        model.tempo_medio_minutos = servico.tempo_medio_minutos
        model.ativo = servico.ativo
        model.atualizado_em = servico.atualizado_em
        self.session.add(model)
        return servico

    async def listar(self, filtros: ListarServicosFiltro) -> list[Servico]:
        query = select(ServicoModel)

        if filtros.nome:
            query = query.where(ServicoModel.nome.ilike(f"%{filtros.nome}%"))
        if filtros.ativo is not None:
            query = query.where(ServicoModel.ativo == filtros.ativo)

        result = await self.session.exec(query)
        return [self._to_entity(model) for model in result.all()]

    @staticmethod
    def _to_entity(model: ServicoModel) -> Servico:
        return Servico(
            id=ID.from_string(str(model.id)),
            nome=model.nome,
            descricao=model.descricao,
            valor_base=Decimal(str(model.valor_base)),
            tempo_medio_minutos=model.tempo_medio_minutos,
            ativo=model.ativo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )
