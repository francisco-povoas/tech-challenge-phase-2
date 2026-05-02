from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.estoque.application.dtos.item_estoque import ItemEstoqueResponse
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro
from app.modules.estoque.domain.ports.item_estoque_repo import ItemEstoqueRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarItensEstoqueUseCase:
    item_estoque_repo: ItemEstoqueRepo

    async def execute(self, filtros: ListarItensEstoqueFiltro) -> list[ItemEstoqueResponse]:
        """Lista itens de estoque com filtros opcionais."""
        itens = await self.item_estoque_repo.listar(filtros)

        logger.info(
            "Listagem de itens de estoque executada com filtros tipo=%s nome=%s codigo=%s ativo=%s baixo_estoque=%s",
            filtros.tipo,
            filtros.nome,
            filtros.codigo,
            filtros.ativo,
            filtros.baixo_estoque,
        )
        return [
            ItemEstoqueResponse(
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
            for item in itens
        ]
