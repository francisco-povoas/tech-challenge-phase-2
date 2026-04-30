from typing import Protocol

from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo


class VeiculoUnitOfWork(Protocol):
    """Contrato do Unit of Work do módulo Veículos."""

    veiculo_repo: VeiculoRepo

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self): ...

    async def rollback(self): ...
