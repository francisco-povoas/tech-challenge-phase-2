from typing import Optional, Protocol

from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.modules.iam.domain.filters.usuario import ListarUsuariosFiltro
from app.modules.iam.domain.entities.usuario import Usuario


class UsuarioRepo(Protocol):
    """Contrato do repositório de usuários (porta de saída do domínio IAM)."""

    async def salvar(self, usuario: Usuario) -> None:
        """Persiste um novo usuário."""
        ...

    async def obter_por_id(self, _id: ID) -> Optional[Usuario]:
        """Retorna o usuário com o ID informado, ou None se não encontrado."""
        ...

    async def obter_por_email(self, email: Email) -> Optional[Usuario]:
        """Retorna o usuário com o e-mail informado, ou None se não encontrado."""
        ...

    async def atualizar(self, usuario: Usuario) -> Optional[Usuario]:
        """Atualiza os dados do usuário. Retorna None se não encontrado."""
        ...

    async def remover(self, _id: ID) -> bool:
        """Remove o usuário. Retorna True se removido, False se não encontrado."""
        ...

    async def listar(self, filtros: ListarUsuariosFiltro) -> list[Usuario]:
        """Lista usuários aplicando filtros opcionais."""
        ...


## relacao usuario_perfil

    async def adicionar_perfil(self, usuario_id: ID, perfil_id: ID) -> None:
        """Associa um perfil a um usuário."""
        ...

    async def listar_perfis_do_usuario(self, usuario_id: ID) -> list[str]:
        """Lista os perfis associados a um usuário."""
        ...