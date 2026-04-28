from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.shared.value_objects.id import InvalidIDError
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.clientes.application.dtos.cliente import (
    AtualizarCliente,
    ClienteResponse,
    CriarClienteRequest,
)
from app.modules.clientes.domain.exceptions import (
    ClienteInvalidoError,
    ClienteNaoEncontradoError,
    CpfCnpjJaCadastradoError,
)
from app.modules.clientes.domain.filters.cliente import ListarClientesFiltro
from app.modules.clientes.presentation.dependencies import (
    AtivarClienteDep,
    AtualizarClienteDep,
    CriarCliente,
    DesativarClienteDep,
    ListarClientes,
    ObterClientePorId,
    RemoverClienteDep,
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
    summary="Cria um novo cliente",
    description="""Cria um novo cliente no sistema.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        201: {"description": "Cliente criado com sucesso", "model": ClienteResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        409: {"description": "Já existe um cliente com este CPF/CNPJ", "model": ErrorResponse},
        422: {"description": "Erro de validação da requisição"},
    },
)
async def criar(
    dto: CriarClienteRequest,
    usecase: CriarCliente,
) -> ClienteResponse:
    try:
        return await usecase.execute(dto)
    except ClienteInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CpfCnpjJaCadastradoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "",
    summary="Lista clientes",
    description="""Retorna uma listagem de clientes cadastrados no sistema.
Suporta filtros opcionais por `nome`, `cpf_cnpj` e `ativo`.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Lista de clientes retornada com sucesso", "model": list[ClienteResponse]},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição"},
    },
)
async def listar(
    usecase: ListarClientes,
    nome: str | None = None,
    cpf_cnpj: str | None = None,
    ativo: bool | None = None,
) -> list[ClienteResponse]:
    filtros = ListarClientesFiltro(nome=nome, cpf_cnpj=cpf_cnpj, ativo=ativo)
    return await usecase.execute(filtros)


@router.get(
    "/{cliente_id}",
    summary="Busca cliente por ID",
    description="""Retorna os dados detalhados de um cliente.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Cliente encontrado", "model": ClienteResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def obter(
    cliente_id: UUID,
    usecase: ObterClientePorId,
) -> ClienteResponse:
    try:
        return await usecase.execute(str(cliente_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


@router.patch(
    "/{cliente_id}",
    summary="Atualiza dados de um cliente",
    description="""Atualiza parcialmente os dados cadastrais de um cliente existente.
> **Nota:** tipo_pessoa e cpf_cnpj não podem ser alterados por esta rota.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Cliente atualizado com sucesso", "model": ClienteResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def atualizar(
    cliente_id: UUID,
    dto: AtualizarCliente,
    usecase: AtualizarClienteDep,
) -> ClienteResponse:
    try:
        return await usecase.execute(str(cliente_id), dto)
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    except ClienteInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{cliente_id}/ativar",
    summary="Ativa um cliente",
    description="""Ativa um cliente previamente desativado.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Cliente ativado com sucesso", "model": ClienteResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def ativar(
    cliente_id: UUID,
    usecase: AtivarClienteDep,
) -> ClienteResponse:
    try:
        return await usecase.execute(str(cliente_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


@router.patch(
    "/{cliente_id}/desativar",
    summary="Desativa um cliente",
    description="""Desativa um cliente sem removê-lo fisicamente do banco.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Cliente desativado com sucesso", "model": ClienteResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def desativar(
    cliente_id: UUID,
    usecase: DesativarClienteDep,
) -> ClienteResponse:
    try:
        return await usecase.execute(str(cliente_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


@router.delete(
    "/{cliente_id}",
    status_code=204,
    summary="Remove um cliente",
    description="""Remove permanentemente o cliente informado do sistema.

Em caso de sucesso, retorna `204 No Content` sem corpo de resposta.

""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    response_class=Response,
    responses={
        204: {"description": "Cliente removido com sucesso. Resposta sem corpo."},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def remover(cliente_id: UUID, usecase: RemoverClienteDep) -> None:
    if not await usecase.execute(str(cliente_id)):
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
