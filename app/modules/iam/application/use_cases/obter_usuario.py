from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.iam.application.dtos.usuario import UsuarioResponseWithPerfis
from app.modules.iam.domain.exceptions import UsuarioNaoEncontradoError
from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterUsuarioUseCase:
    usuario_repo: UsuarioRepo

    async def execute(self, usuario_id: str) -> UsuarioResponseWithPerfis:
        """Retorna os dados de um usuário pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            UsuarioNaoEncontradoError: Se o usuário não for encontrado.
        """
        id_value = ID.from_string(usuario_id)
        usuario = await self.usuario_repo.obter_por_id(id_value)

        perfis_usuario = await self.usuario_repo.listar_perfis_do_usuario(id_value)

        if not usuario:
            raise UsuarioNaoEncontradoError(f"Usuário com ID {usuario_id} não encontrado")

        return UsuarioResponseWithPerfis(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email.value,
            perfis= perfis_usuario)
