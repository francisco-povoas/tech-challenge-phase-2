from typing_extensions import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, Depends

from app.shared.value_objects.id import InvalidIDError
from app.modules.iam.application.dtos.usuario import (
    AtualizarUsuario,
    CriarUsuarioRequest,
    UsuarioResponse,
    UsuarioResponseWithPerfis,
)
from app.modules.iam.domain.exceptions import (
    InvalidUsuarioError,
    UsuarioJaExisteError,
    UsuarioNaoEncontradoError,
)
from app.modules.iam.domain.filters.usuario import ListarUsuariosFiltro
from app.shared.value_objects.email import InvalidEmailError
from app.modules.iam.presentation.dependencies import (
    CriarUsuario,
    ObterUsuario,
    ListarUsuarios,
    AtualizarUsuario as AtualizarUsuarioDep,
    RemoverUsuario,
)

from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos

router = APIRouter()

_DESC_AUTH = """\

Esta operação é restrita a usuários autenticados com perfil `Administrador`.

**Requisitos de autenticação:**
- Enviar um token JWT válido no header `Authorization`;
- O token deve pertencer a um usuário ativo com perfil `Administrador`.

Exemplo de header:
`Authorization: Bearer <token>`

**Possíveis respostas de autorização:**
- `401 Unauthorized`: token ausente, inválido ou expirado;
- `403 Forbidden`: usuário autenticado, mas sem perfil `Administrador`.\
"""

_RESPONSES_AUTH = {
    401: {"description": "Token ausente, inválido ou expirado", "model": ErrorResponse},
    403: {"description": "Usuário autenticado não possui perfil Administrador", "model": ErrorResponse},
}

@router.post(
    "",
    status_code=201,
    summary="Cria um novo usuário",
    description="""Cria um novo usuário no sistema e vincula os perfis informados na requisição.

""" + _DESC_AUTH,
    dependencies=[Depends(RequireRoles(PerfilTipos.ADMINISTRADOR))],
    responses={
        201: {"description": "Usuário criado com sucesso", "model": UsuarioResponseWithPerfis},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        409: {"description": "Já existe um usuário com este e-mail", "model": ErrorResponse},
        422: {"description": "Erro de validação da requisição"},
    },
)
async def criar(
    dto: CriarUsuarioRequest,
    usecase: CriarUsuario,
) -> UsuarioResponseWithPerfis:
    try:
        return await usecase.execute(dto)
    except (InvalidUsuarioError, InvalidEmailError) as e:
        raise HTTPException(400, detail=str(e))
    except UsuarioJaExisteError:
        raise HTTPException(409, detail="Já existe um usuário com este e-mail")


@router.get(
    "",
    summary="Lista usuários",
    description="""Retorna uma listagem resumida de usuários cadastrados no sistema.

Suporta filtros opcionais por `nome`, `e-mail` e `ativo`.

> **Atenção:** esta resposta **não inclui perfis** vinculados ao usuário.
> Para consultar os perfis, utilize `GET /api/v1/usuarios/{usuario_id}`.

""" + _DESC_AUTH,
    dependencies=[Depends(RequireRoles(PerfilTipos.ADMINISTRADOR))],
    responses={
        200: {"description": "Lista de usuários retornada com sucesso", "model": list[UsuarioResponse]},
        400: {"description": "Filtro inválido", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição"},
    },
)
async def listar(
    usecase: ListarUsuarios,
    nome: str | None = None,
    email: str | None = None,
    ativo: bool | None = None,
) -> list[UsuarioResponse]:
    try:
        filtros = ListarUsuariosFiltro(nome=nome, email=email, ativo=ativo)
        return await usecase.execute(filtros)
    except (InvalidUsuarioError, InvalidEmailError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{usuario_id}",
    summary="Busca usuário por ID",
    description="""Retorna os dados detalhados de um usuário, **incluindo os perfis vinculados**.

""" + _DESC_AUTH,
    dependencies=[Depends(RequireRoles(PerfilTipos.ADMINISTRADOR))],
    responses={
        200: {"description": "Usuário encontrado", "model": UsuarioResponseWithPerfis},
        **_RESPONSES_AUTH,
        404: {"description": "Usuário não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def obter(usuario_id: UUID, usecase: ObterUsuario) -> UsuarioResponseWithPerfis:
    try:
        return await usecase.execute(str(usuario_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except UsuarioNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


@router.delete(
    "/{usuario_id}",
    status_code=204,
    summary="Remove um usuário",
    description="""Remove permanentemente o usuário informado do sistema.

Em caso de sucesso, retorna `204 No Content` sem corpo de resposta.

> **TODO futuro:** bloquear remoção do último administrador ativo do sistema.

""" + _DESC_AUTH,
    dependencies=[Depends(RequireRoles(PerfilTipos.ADMINISTRADOR))],
    response_class=Response,
    responses={
        204: {"description": "Usuário removido com sucesso. Resposta sem corpo."},
        **_RESPONSES_AUTH,
        404: {"description": "Usuário não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def remover(usuario_id: UUID, usecase: RemoverUsuario) -> None:
    if not await usecase.execute(str(usuario_id)):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

@router.patch(
    "/{usuario_id}",
    summary="Atualiza dados de um usuário",
    description="""Atualiza parcialmente os dados cadastrais de um usuário existente.

> **Nota:** esta rota não deve ser utilizada para alteração de senha ou gerenciamento de perfis.

""" + _DESC_AUTH,
    dependencies=[Depends(RequireRoles(PerfilTipos.ADMINISTRADOR))],
    responses={
        200: {"description": "Usuário atualizado com sucesso", "model": UsuarioResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Usuário não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def atualizar(
    usuario_id: UUID,
    dto: AtualizarUsuario,
    usecase: AtualizarUsuarioDep
) -> UsuarioResponse:
    try:
        return await usecase.execute(str(usuario_id), dto)
    except UsuarioNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except (InvalidUsuarioError, InvalidEmailError) as e:
        raise HTTPException(status_code=400, detail=str(e))
