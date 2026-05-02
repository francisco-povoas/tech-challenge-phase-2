from decimal import Decimal
from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque, TipoItemEstoque
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro
from app.modules.estoque.infrastructure.db.models.item_estoque import ItemEstoqueModel


class ItemEstoqueRepo:
    """Implementação concreta do repositório de itens de estoque (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, item: ItemEstoque) -> None:
        model = ItemEstoqueModel(
            id=item.id.value,
            tipo=item.tipo.value,
            nome=item.nome,
            descricao=item.descricao,
            codigo=item.codigo,
            quantidade_disponivel=item.quantidade_disponivel,
            quantidade_reservada=item.quantidade_reservada,
            quantidade_minima=item.quantidade_minima,
            valor_unitario=item.valor_unitario,
            ativo=item.ativo,
            criado_em=item.criado_em,
            atualizado_em=item.atualizado_em,
        )
        self.session.add(model)

    async def obter_por_id(self, _id: ID) -> Optional[ItemEstoque]:
        model = await self.session.get(ItemEstoqueModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_codigo(self, codigo: str) -> Optional[ItemEstoque]:
        result = await self.session.exec(
            select(ItemEstoqueModel).where(ItemEstoqueModel.codigo == codigo)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def atualizar(self, item: ItemEstoque) -> Optional[ItemEstoque]:
        model = await self.session.get(ItemEstoqueModel, item.id.value)
        if not model:
            return None
        model.tipo = item.tipo.value
        model.nome = item.nome
        model.descricao = item.descricao
        model.codigo = item.codigo
        model.quantidade_disponivel = item.quantidade_disponivel
        model.quantidade_reservada = item.quantidade_reservada
        model.quantidade_minima = item.quantidade_minima
        model.valor_unitario = item.valor_unitario
        model.ativo = item.ativo
        model.atualizado_em = item.atualizado_em
        self.session.add(model)
        return item

    async def obter_por_id_com_lock(self, _id: ID) -> Optional[ItemEstoque]:
        """Retorna o item com lock pessimista para evitar condição de corrida em reservas."""

        result = await self.session.execute(
            select(ItemEstoqueModel)
            .where(ItemEstoqueModel.id == _id.value)
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def listar(self, filtros: ListarItensEstoqueFiltro) -> list[ItemEstoque]:
        query = select(ItemEstoqueModel)

        if filtros.tipo is not None:
            query = query.where(ItemEstoqueModel.tipo == filtros.tipo.value)
        if filtros.nome:
            query = query.where(ItemEstoqueModel.nome.ilike(f"%{filtros.nome}%"))
        if filtros.codigo:
            query = query.where(ItemEstoqueModel.codigo == filtros.codigo)
        if filtros.ativo is not None:
            query = query.where(ItemEstoqueModel.ativo == filtros.ativo)
        if filtros.baixo_estoque:
            query = query.where(
                ItemEstoqueModel.quantidade_disponivel <= ItemEstoqueModel.quantidade_minima
            )

        result = await self.session.exec(query)
        return [self._to_entity(model) for model in result.all()]

    @staticmethod
    def _to_entity(model: ItemEstoqueModel) -> ItemEstoque:
        return ItemEstoque(
            id=ID.from_string(str(model.id)),
            tipo=TipoItemEstoque(model.tipo),
            nome=model.nome,
            descricao=model.descricao,
            codigo=model.codigo,
            quantidade_disponivel=model.quantidade_disponivel,
            quantidade_reservada=model.quantidade_reservada,
            quantidade_minima=model.quantidade_minima,
            valor_unitario=Decimal(str(model.valor_unitario)),
            ativo=model.ativo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )
