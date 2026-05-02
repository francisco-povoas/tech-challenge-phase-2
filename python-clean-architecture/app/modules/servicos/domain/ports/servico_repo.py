from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.filters.servico import ListarServicosFiltro


class ServicoRepo(Protocol):
    """Contrato do repositório de serviços (porta de saída do domínio Serviços)."""

    async def salvar(self, servico: Servico) -> None:
        """Persiste um novo serviço."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[Servico]:
        """Retorna o serviço com o ID informado, ou None se não encontrado."""
        ...

    async def obter_por_nome(self, nome: str) -> Optional[Servico]:
        """Retorna o serviço com o nome informado, ou None se não encontrado."""
        ...

    async def atualizar(self, servico: Servico) -> Optional[Servico]:
        """Atualiza os dados do serviço. Retorna None se não encontrado."""
        ...

    async def listar(self, filtros: ListarServicosFiltro) -> list[Servico]:
        """Lista serviços aplicando filtros opcionais."""
        ...
