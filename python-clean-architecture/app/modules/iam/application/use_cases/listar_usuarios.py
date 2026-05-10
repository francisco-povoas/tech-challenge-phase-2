from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.email import Email, InvalidEmailError
from app.modules.iam.application.dtos.usuario import UsuarioResponse
from app.modules.iam.domain.exceptions import InvalidUsuarioError
from app.modules.iam.domain.filters.usuario import ListarUsuariosFiltro
from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarUsuariosUseCase:
    usuario_repo: UsuarioRepo

    async def execute(self, filtros: ListarUsuariosFiltro) -> list[UsuarioResponse]:
        """Lista usuários com filtros opcionais por nome, e-mail e status ativo."""
        email = filtros.email
        if email:
            try:
                email = Email(email).value
            except InvalidEmailError as e:
                raise InvalidUsuarioError(str(e))

        usuarios = await self.usuario_repo.listar(
            ListarUsuariosFiltro(nome=filtros.nome, email=email, ativo=filtros.ativo)
        )

        logger.info(
            "Listagem de usuários executada com filtros nome=%s email=%s ativo=%s",
            filtros.nome,
            filtros.email,
            filtros.ativo,
        )
        return [
            UsuarioResponse(
                id=str(usuario.id),
                nome=usuario.nome,
                email=usuario.email.value,
            )
            for usuario in usuarios
        ]
