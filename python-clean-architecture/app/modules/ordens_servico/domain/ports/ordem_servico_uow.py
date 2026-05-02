"""Contrato do Unit of Work do módulo Ordens de Serviço."""

from typing import Optional, Protocol

from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo
from app.modules.estoque.domain.ports.item_estoque_repo import ItemEstoqueRepo


class OrdemServicoUnitOfWork(Protocol):
    """Agrupa OS repo e ItemEstoque repo na mesma transação."""

    ordem_servico_repo: OrdemServicoRepo
    item_estoque_repo: ItemEstoqueRepo

    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...
    async def commit(self): ...
    async def rollback(self): ...
