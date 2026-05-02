from typing import Protocol

from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo
from app.modules.iam.domain.ports.perfil_repo import PerfilRepo

class UsuarioUnitOfWork(Protocol):
    """Contrato do Unit of Work do módulo IAM."""

    usuario_repo: UsuarioRepo
    perfil_repo: PerfilRepo  # Repositório para perfis (pode ser separado em outro UoW se preferir)

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def commit(self): ...

    async def rollback(self): ...
