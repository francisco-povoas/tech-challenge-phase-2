from typing import Protocol

from app.modules.estoque.domain.ports.item_estoque_repo import ItemEstoqueRepo


class ItemEstoqueUnitOfWork(Protocol):
    """Contrato do Unit of Work do módulo Estoque."""

    item_estoque_repo: ItemEstoqueRepo

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self): ...

    async def rollback(self): ...
