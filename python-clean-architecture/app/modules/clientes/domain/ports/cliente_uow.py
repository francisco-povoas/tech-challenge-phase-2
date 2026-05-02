from typing import Protocol

from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo


class ClienteUnitOfWork(Protocol):
    """Contrato do Unit of Work do módulo Clientes."""

    cliente_repo: ClienteRepo

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self): ...

    async def rollback(self): ...
