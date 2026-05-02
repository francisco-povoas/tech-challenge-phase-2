"""Dependências de infraestrutura do módulo IAM para injeção via FastAPI."""
from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.shared.infra.security.crypto import Hasher
from app.shared.ports.hasher import HasherProtocol
from app.modules.iam.domain.ports.usuario_repo import UsuarioRepo as UsuarioRepoProtocol
from app.modules.iam.domain.ports.usuario_uow import UsuarioUnitOfWork as UsuarioUoWProtocol
from app.modules.iam.infrastructure.db.repositories.usuario_repo import UsuarioRepo
from app.modules.iam.infrastructure.db.uow.usuario_uow import usuario_uow_factory
from app.modules.iam.application.use_cases import (
    CriarUsuarioUseCase,
    AutenticarUsuarioUseCase,
    ObterUsuarioUseCase,
    ListarUsuariosUseCase,
    AtualizarUsuarioUseCase,
    RemoverUsuarioUseCase,
)


# --- Infraestrutura ---

def get_hasher() -> HasherProtocol:
    return Hasher()


async def get_usuario_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> UsuarioRepoProtocol:
    return UsuarioRepo(session)


async def get_usuario_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> UsuarioUoWProtocol:
    return usuario_uow_factory(session)  # type: ignore[misc]


_HasherDep = Annotated[HasherProtocol, Depends(get_hasher)]
_RepoDep = Annotated[UsuarioRepoProtocol, Depends(get_usuario_repo)]
_UoWDep = Annotated[UsuarioUoWProtocol, Depends(get_usuario_uow)]


# --- Use Cases ---

def get_criar_usuario(uow: _UoWDep, hasher: _HasherDep) -> CriarUsuarioUseCase:
    return CriarUsuarioUseCase(uow=uow, hasher=hasher)


def get_autenticar_usuario(repo: _RepoDep, hasher: _HasherDep) -> AutenticarUsuarioUseCase:
    return AutenticarUsuarioUseCase(usuario_repo=repo, hasher=hasher)


def get_obter_usuario(repo: _RepoDep) -> ObterUsuarioUseCase:
    return ObterUsuarioUseCase(usuario_repo=repo)


def get_listar_usuarios(repo: _RepoDep) -> ListarUsuariosUseCase:
    return ListarUsuariosUseCase(usuario_repo=repo)


def get_atualizar_usuario(uow: _UoWDep) -> AtualizarUsuarioUseCase:
    return AtualizarUsuarioUseCase(uow=uow)


def get_remover_usuario(uow: _UoWDep) -> RemoverUsuarioUseCase:
    return RemoverUsuarioUseCase(uow=uow)


CriarUsuario = Annotated[CriarUsuarioUseCase, Depends(get_criar_usuario)]
AutenticarUsuario = Annotated[AutenticarUsuarioUseCase, Depends(get_autenticar_usuario)]
ObterUsuario = Annotated[ObterUsuarioUseCase, Depends(get_obter_usuario)]
ListarUsuarios = Annotated[ListarUsuariosUseCase, Depends(get_listar_usuarios)]
AtualizarUsuario = Annotated[AtualizarUsuarioUseCase, Depends(get_atualizar_usuario)]
RemoverUsuario = Annotated[RemoverUsuarioUseCase, Depends(get_remover_usuario)]
