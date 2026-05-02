from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.application.dtos.item_estoque import ItemEstoqueResponse
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.estoque.domain.ports.item_estoque_repo import ItemEstoqueRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterItemEstoquePorIdUseCase:
    item_estoque_repo: ItemEstoqueRepo

    async def execute(self, item_id: str) -> ItemEstoqueResponse:
        """Retorna os dados de um item de estoque pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ItemEstoqueNaoEncontradoError: Se o item não for encontrado.
        """
        id_value = ID.from_string(item_id)
        item = await self.item_estoque_repo.obter_por_id(id_value)

        if not item:
            raise ItemEstoqueNaoEncontradoError(f"Item de estoque com ID {item_id} não encontrado.")

        logger.info(f"Item de estoque {item_id} obtido com sucesso")
        return ItemEstoqueResponse(
            id=str(item.id),
            tipo=item.tipo.value,
            nome=item.nome,
            descricao=item.descricao,
            codigo=item.codigo,
            quantidade_disponivel=item.quantidade_disponivel,
            quantidade_reservada=item.quantidade_reservada,
            quantidade_minima=item.quantidade_minima,
            valor_unitario=item.valor_unitario,
            ativo=item.ativo,
        )
