from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro


class ItemEstoqueRepo(Protocol):
    """Contrato do repositório de itens de estoque (porta de saída do domínio Estoque)."""

    async def salvar(self, item: ItemEstoque) -> None:
        """Persiste um novo item de estoque."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[ItemEstoque]:
        """Retorna o item com o ID informado, ou None se não encontrado."""
        ...

    async def obter_por_codigo(self, codigo: str) -> Optional[ItemEstoque]:
        """Retorna o item com o código informado, ou None se não encontrado."""
        ...

    async def atualizar(self, item: ItemEstoque) -> Optional[ItemEstoque]:
        """Atualiza os dados do item. Retorna None se não encontrado."""
        ...

    async def listar(self, filtros: ListarItensEstoqueFiltro) -> list[ItemEstoque]:
        """Lista itens de estoque aplicando filtros opcionais."""
        ...

    async def obter_por_id_com_lock(self, _id: ID) -> Optional[ItemEstoque]:
        """Retorna o item com lock pessimista (SELECT ... FOR UPDATE) para operações transacionais."""
        ...
