from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo
from app.modules.iam.domain.ports.usuario_uow import UsuarioUnitOfWork


logger = setup_logger(__name__)


@dataclass(frozen=True)
class RemoverUsuarioUseCase:
    uow: UsuarioUnitOfWork

    async def execute(self, usuario_id: str) -> bool:
        """Remove um usuário pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
        """
        # TODO: antes de remover/desativar usuário, validar se ele é o último
        # administrador ativo do sistema. Se for, bloquear a operação para evitar
        # deixar o sistema sem admin.

        # Detalhe:
        # Ao deletar um usuario, é preciso deletar também os registros de associação com perfis (tabela pivo).
        # Isso pode ser feito com cascade delete no banco, ou manualmente na aplicação.
        # Foi implementado com cascade na migration.
        
        async with self.uow:
            id_value = ID.from_string(usuario_id)
            resultado = await self.uow.usuario_repo.remover(id_value)

            if resultado:
                logger.info(f"Usuário {usuario_id} removido com sucesso")
            return resultado
