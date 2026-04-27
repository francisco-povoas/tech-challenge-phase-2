from typing import Optional, Protocol

from app.shared.value_objects.id import ID
from app.modules.iam.domain.entities.perfil import Perfil

class PerfilRepo(Protocol):
    """Contrato do repositório de perfis (porta de saída do domínio IAM)."""

    async def obter_por_nome(self, nome: str) -> Optional[Perfil]:
        """Retorna o perfil com o nome informado, ou None se não encontrado."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[Perfil]:
        """Retorna o perfil com o ID informado, ou None se não encontrado."""
        ...

    async def listar(self) -> list[Perfil]:
        """Lista perfis."""
        ...
