from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.entities.veiculo import Veiculo


class VeiculoRepo(Protocol):
    """Contrato do repositório de veículos (porta de saída do domínio Veículos)."""

    async def salvar(self, veiculo: Veiculo) -> None: ...

    async def obter_por_id(self, _id: ID) -> Optional[Veiculo]: ...

    async def obter_por_placa(self, placa: str) -> Optional[Veiculo]: ...

    async def listar_por_cliente(self, cliente_id: str) -> list[Veiculo]: ...

    async def remover(self, _id: ID) -> bool: ...
