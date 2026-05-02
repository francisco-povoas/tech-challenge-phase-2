from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.filters.veiculo import ListarVeiculosFiltro


class VeiculoRepo(Protocol):
    """Contrato do repositório de veículos (porta de saída do domínio Veículos)."""

    async def salvar(self, veiculo: Veiculo) -> None:
        """Persiste um novo veículo."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[Veiculo]:
        """Retorna o veículo com o ID informado, ou None se não encontrado."""
        ...

    async def obter_por_placa(self, placa: str) -> Optional[Veiculo]:
        """Retorna o veículo com a placa informada (normalizada), ou None se não encontrado."""
        ...

    async def atualizar(self, veiculo: Veiculo) -> Optional[Veiculo]:
        """Atualiza os dados do veículo. Retorna None se não encontrado."""
        ...

    async def listar(self, filtros: ListarVeiculosFiltro) -> list[Veiculo]:
        """Lista veículos aplicando filtros opcionais."""
        ...

    async def remover(self, _id: ID) -> bool:
        """Remove o veículo. Retorna True se removido, False se não encontrado."""
        ...
