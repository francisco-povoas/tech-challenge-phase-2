from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.application.dtos.item_estoque import ItemEstoqueResponse
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.estoque.domain.ports.item_estoque_uow import ItemEstoqueUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtivarItemEstoqueUseCase:
    uow: ItemEstoqueUnitOfWork

    async def execute(self, item_id: str) -> ItemEstoqueResponse:
        """Ativa um item de estoque previamente desativado.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ItemEstoqueNaoEncontradoError: Se o item não for encontrado.
        """
        id_value = ID.from_string(item_id)

        async with self.uow:
            existente = await self.uow.item_estoque_repo.obter_por_id(id_value)
            if not existente:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque com ID {item_id} não encontrado."
                )

            agora = datetime.now(UTC)

            atualizado = await self.uow.item_estoque_repo.atualizar(
                ItemEstoque(
                    id=existente.id,
                    tipo=existente.tipo,
                    nome=existente.nome,
                    descricao=existente.descricao,
                    codigo=existente.codigo,
                    quantidade_disponivel=existente.quantidade_disponivel,
                    quantidade_reservada=existente.quantidade_reservada,
                    quantidade_minima=existente.quantidade_minima,
                    valor_unitario=existente.valor_unitario,
                    ativo=True,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque com ID {item_id} não encontrado."
                )

            logger.info(f"Item de estoque {item_id} ativado com sucesso")
            return ItemEstoqueResponse(
                id=str(atualizado.id),
                tipo=atualizado.tipo.value,
                nome=atualizado.nome,
                descricao=atualizado.descricao,
                codigo=atualizado.codigo,
                quantidade_disponivel=atualizado.quantidade_disponivel,
                quantidade_reservada=atualizado.quantidade_reservada,
                quantidade_minima=atualizado.quantidade_minima,
                valor_unitario=atualizado.valor_unitario,
                ativo=atualizado.ativo,
            )
