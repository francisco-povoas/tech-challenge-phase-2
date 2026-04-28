from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.filters.cliente import ListarClientesFiltro


class ClienteRepo(Protocol):
    """Contrato do repositório de clientes (porta de saída do domínio Clientes)."""

    async def salvar(self, cliente: Cliente) -> None:
        """Persiste um novo cliente."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[Cliente]:
        """Retorna o cliente com o ID informado, ou None se não encontrado."""
        ...

    async def obter_por_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Cliente]:
        """Retorna o cliente com o CPF/CNPJ informado, ou None se não encontrado."""
        ...

    async def atualizar(self, cliente: Cliente) -> Optional[Cliente]:
        """Atualiza os dados do cliente. Retorna None se não encontrado."""
        ...

    async def listar(self, filtros: ListarClientesFiltro) -> list[Cliente]:
        """Lista clientes aplicando filtros opcionais."""
        ...

    async def remover(self, _id: ID) -> bool:
        """Remove o cliente. Retorna True se removido, False se não encontrado."""
        ...
