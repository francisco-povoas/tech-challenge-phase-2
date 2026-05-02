from dataclasses import dataclass
from datetime import datetime, UTC
from app.logger import setup_logger
from app.shared.value_objects.email import Email, InvalidEmailError
from app.shared.value_objects.id import ID
from app.shared.value_objects.password import InvalidPasswordError, Password
from app.shared.ports.hasher import HasherProtocol
from app.modules.iam.application.dtos.usuario import CriarUsuarioRequest, UsuarioResponseWithPerfis
from app.modules.iam.domain.entities.usuario import Usuario, UsuarioPerfil
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.iam.domain.exceptions import InvalidUsuarioError, UsuarioJaExisteError
from app.modules.iam.domain.ports.usuario_uow import UsuarioUnitOfWork

logger = setup_logger(__name__)

@dataclass(frozen=True)
class CriarUsuarioUseCase:
    uow: UsuarioUnitOfWork
    hasher: HasherProtocol

    async def execute(self, dto: CriarUsuarioRequest) -> UsuarioResponseWithPerfis:
        """Cria um novo usuário, garantindo unicidade de e-mail.
        Adiciona perfis ao usuário criado.

        Raises:
            InvalidUsuarioError: Se os dados fornecidos forem inválidos.
            UsuarioJaExisteError: Se já existir usuário com o mesmo e-mail.
        """
        try:
            email = Email(dto.email)
            senha = Password(dto.senha)
        except (InvalidEmailError, InvalidPasswordError) as e:
            logger.warning(f"Dados inválidos ao criar usuário: {e}")
            raise InvalidUsuarioError(str(e))

        perfis_solicitados = list(dict.fromkeys(dto.perfis))
        perfis_permitidos = PerfilTipos.tipos()

        for perfil in perfis_solicitados:
            if perfil not in perfis_permitidos:
                logger.warning(f"Perfil inválido '{perfil}' para usuário {email.value}")
                raise InvalidUsuarioError(
                    f"Perfil inválido: {perfil}. "
                    f"Deve ser um dos seguintes: {', '.join(perfis_permitidos)}"
                )

        async with self.uow:
            if await self.uow.usuario_repo.obter_por_email(email):
                logger.warning(f"Usuário com e-mail {email.value} já existe")
                raise UsuarioJaExisteError(
                    f"Já existe um usuário com o e-mail {email.value}"
                )

            perfis_existentes = {
                perfil.nome: perfil.id
                for perfil in await self.uow.perfil_repo.listar()
                if perfil.ativo
            }

            for perfil in perfis_solicitados:
                if perfil not in perfis_existentes:
                    logger.warning(f"Perfil '{perfil}' não cadastrado ou inativo")
                    raise InvalidUsuarioError(
                        f"Perfil não cadastrado ou inativo: {perfil}"
                    )

            senha_hash = self.hasher.hash(senha.value)
            agora = datetime.now(UTC)

            usuario = Usuario(
                id=ID.generate(),
                nome=dto.nome,
                email=email,
                senha=Password(senha_hash),
                criado_em=agora,
                atualizado_em=agora,
                ativo=True,
            )

            await self.uow.usuario_repo.salvar(usuario)

            for perfil in perfis_solicitados:
                usuario_perfil = UsuarioPerfil(
                    id=ID.generate(),
                    usuario_id=usuario.id,
                    perfil_id=perfis_existentes[perfil],
                    criado_em=agora,
                )

                await self.uow.usuario_repo.adicionar_perfil(usuario_perfil)

            logger.info(f"Usuário {email.value} criado com sucesso")

            return UsuarioResponseWithPerfis(
                id=str(usuario.id),
                nome=usuario.nome,
                email=usuario.email.value,
                perfis=perfis_solicitados,
            )