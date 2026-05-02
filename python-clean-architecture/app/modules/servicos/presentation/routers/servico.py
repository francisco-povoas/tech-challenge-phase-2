from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.shared.value_objects.id import InvalidIDError
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.servicos.application.dtos.servico import (
    AtualizarServico,
    CriarServicoRequest,
    ServicoResponse,
)
from app.modules.servicos.domain.exceptions import (
    NomeServicoJaCadastradoError,
    ServicoInvalidoError,
    ServicoNaoEncontradoError,
)
from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
from app.modules.servicos.presentation.dependencies import (
    AtivarServicoDep,
    AtualizarServicoDep,
    CriarServico,
    DesativarServicoDep,
    ListarServicos,
    ObterServicoPorId,
)

router = APIRouter()

_DESC_AUTH = """\

Esta operação é restrita a usuários autenticados com perfil `Administrador` ou `Atendente`.

**Requisitos de autenticação:**
- Enviar um token JWT válido no header `Authorization`;
- O token deve pertencer a um usuário ativo com perfil `Administrador` ou `Atendente`.

Exemplo de header:
`Authorization: Bearer <token>`

**Possíveis respostas de autorização:**
- `401 Unauthorized`: token ausente, inválido ou expirado;
- `403 Forbidden`: usuário autenticado, mas sem perfil `Administrador` ou `Atendente`.\
"""

_RESPONSES_AUTH = {
    401: {"description": "Token ausente, inválido ou expirado", "model": ErrorResponse},
    403: {
        "description": "Usuário autenticado não possui perfil Administrador ou Atendente",
        "model": ErrorResponse,
    },
}

_ADMIN_OU_ATENDENTE = Depends(
    RequireRoles(PerfilTipos.ADMINISTRADOR, PerfilTipos.ATENDENTE)
)


@router.post(
    "",
    status_code=201,
    summary="Cria um novo serviço",
    description="""Cria um novo serviço no catálogo da oficina.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        201: {"description": "Serviço criado com sucesso", "model": ServicoResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        409: {"description": "Já existe um serviço com este nome", "model": ErrorResponse},
        422: {"description": "Erro de validação da requisição"},
    },
)
async def criar(
    dto: CriarServicoRequest,
    usecase: CriarServico,
) -> ServicoResponse:
    try:
        return await usecase.execute(dto)
    except ServicoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NomeServicoJaCadastradoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "",
    summary="Lista serviços",
    description="""Retorna uma listagem de serviços cadastrados no catálogo da oficina.
Suporta filtros opcionais por `nome` e `ativo`.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Lista de serviços retornada com sucesso", "model": list[ServicoResponse]},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição"},
    },
)
async def listar(
    usecase: ListarServicos,
    nome: str | None = None,
    ativo: bool | None = None,
) -> list[ServicoResponse]:
    filtros = ListarServicosFiltro(nome=nome, ativo=ativo)
    return await usecase.execute(filtros)


@router.get(
    "/{servico_id}",
    summary="Busca serviço por ID",
    description="""Retorna os dados detalhados de um serviço.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Serviço encontrado", "model": ServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def obter(
    servico_id: UUID,
    usecase: ObterServicoPorId,
) -> ServicoResponse:
    try:
        return await usecase.execute(str(servico_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ServicoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")


@router.patch(
    "/{servico_id}",
    summary="Atualiza dados de um serviço",
    description="""Atualiza parcialmente os dados de um serviço existente no catálogo.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Serviço atualizado com sucesso", "model": ServicoResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def atualizar(
    servico_id: UUID,
    dto: AtualizarServico,
    usecase: AtualizarServicoDep,
) -> ServicoResponse:
    try:
        return await usecase.execute(str(servico_id), dto)
    except ServicoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    except ServicoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{servico_id}/ativar",
    summary="Ativa um serviço",
    description="""Ativa um serviço previamente desativado no catálogo.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Serviço ativado com sucesso", "model": ServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def ativar(
    servico_id: UUID,
    usecase: AtivarServicoDep,
) -> ServicoResponse:
    try:
        return await usecase.execute(str(servico_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ServicoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")


@router.patch(
    "/{servico_id}/desativar",
    summary="Desativa um serviço",
    description="""Desativa um serviço sem removê-lo fisicamente do catálogo.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Serviço desativado com sucesso", "model": ServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def desativar(
    servico_id: UUID,
    usecase: DesativarServicoDep,
) -> ServicoResponse:
    try:
        return await usecase.execute(str(servico_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ServicoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
