from typing import Protocol

from app.modules.servicos.domain.ports.servico_repo import ServicoRepo


class ServicoUnitOfWork(Protocol):
    """Contrato do Unit of Work do módulo Serviços."""

    servico_repo: ServicoRepo

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self): ...

    async def rollback(self): ...
