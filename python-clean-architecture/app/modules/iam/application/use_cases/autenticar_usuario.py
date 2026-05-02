from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.email import Email, InvalidEmailError
from app.shared.ports.hasher import HasherProtocol
from app.modules.iam.application.dtos.usuario import UsuarioResponseWithPerfis
from app.modules.iam.domain.exceptions import AutenticacaoFalhouError
from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AutenticarUsuarioUseCase:
    usuario_repo: UsuarioRepo
    hasher: HasherProtocol

    async def execute(self, email_str: str, senha_str: str) -> UsuarioResponseWithPerfis:
        """Autentica um usuário por e-mail e senha.

        Raises:
            AutenticacaoFalhouError: Se as credenciais forem inválidas.
        """
        try:
            email = Email(email_str)
        except InvalidEmailError:
            raise AutenticacaoFalhouError("Credenciais inválidas")

        usuario = await self.usuario_repo.obter_por_email(email)
        if not usuario or not self.hasher.verify(senha_str, usuario.senha.value):
            raise AutenticacaoFalhouError("Credenciais inválidas")

        # buscar perfis do usuário
        perfis = await self.usuario_repo.listar_perfis_do_usuario(usuario.id)

        logger.info(f"Usuário {email_str} autenticado com sucesso")
        return UsuarioResponseWithPerfis(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email.value,
            perfis=perfis
        )