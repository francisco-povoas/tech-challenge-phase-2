from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.modules.iam.application.dtos.usuario import AtualizarUsuario, UsuarioResponse
from app.modules.iam.domain.entities.usuario import Usuario
from app.modules.iam.domain.exceptions import UsuarioNaoEncontradoError
from app.modules.iam.domain.ports.usuario_uow import UsuarioUnitOfWork
from datetime import datetime, UTC

logger = setup_logger(__name__)

#TO DO: Implementar atualizacao de senha e status ativo/inativo e perfis...

@dataclass(frozen=True)
class AtualizarUsuarioUseCase:
    uow: UsuarioUnitOfWork

    async def execute(self, usuario_id: str, dto: AtualizarUsuario) -> UsuarioResponse:
        """Atualiza os dados de um usuário existente.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            InvalidEmailError: Se o novo e-mail for inválido.
            UsuarioNaoEncontradoError: Se o usuário não for encontrado.
        """
        id_value = ID.from_string(usuario_id)

        async with self.uow:
            existente = await self.uow.usuario_repo.obter_por_id(id_value)
            if not existente:
                raise UsuarioNaoEncontradoError(f"Usuário com ID {usuario_id} não encontrado")

            agora = datetime.now(UTC)

            atualizado = await self.uow.usuario_repo.atualizar(
                Usuario(
                    id=existente.id,
                    nome=dto.nome or existente.nome,
                    email=Email(dto.email) if dto.email else existente.email,
                    senha=existente.senha,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                    ativo=existente.ativo,
                )
            )

            if not atualizado:
                raise UsuarioNaoEncontradoError(f"Usuário com ID {usuario_id} não encontrado")

            logger.info(f"Usuário {usuario_id} atualizado com sucesso")
            return UsuarioResponse(
                id=str(atualizado.id),
                nome=atualizado.nome,
                email=atualizado.email.value,
            )
