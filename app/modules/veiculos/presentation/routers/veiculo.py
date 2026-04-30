from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.shared.value_objects.id import InvalidIDError
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.veiculos.application.dtos.veiculo import (
    AtualizarVeiculo,
    CriarVeiculoRequest,
    VeiculoResponse,
)
from app.modules.veiculos.domain.exceptions import (
    PlacaJaCadastradaError,
    VeiculoInvalidoError,
    VeiculoNaoEncontradoError,
)
from app.modules.veiculos.domain.filters.veiculo import ListarVeiculosFiltro
from app.modules.veiculos.presentation.dependencies import (
    AtualizarVeiculoDep,
    CriarVeiculo,
    ListarVeiculos,
    ObterVeiculoPorId,
    RemoverVeiculoDep,
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
    summary="Cria um novo veículo",
    description="""Cria um novo veículo vinculado a um cliente existente.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        201: {"description": "Veículo criado com sucesso", "model": VeiculoResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Cliente não encontrado", "model": ErrorResponse},
        409: {"description": "Já existe um veículo com esta placa", "model": ErrorResponse},
        422: {"description": "Erro de validação da requisição"},
    },
)
async def criar(
    dto: CriarVeiculoRequest,
    usecase: CriarVeiculo,
) -> VeiculoResponse:
    try:
        return await usecase.execute(dto)
    except VeiculoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClienteNaoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlacaJaCadastradaError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "",
    summary="Lista veículos",
    description="""Retorna uma listagem de veículos cadastrados no sistema.
Suporta filtros opcionais por `cliente_id`, `placa`, `marca` e `modelo`.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Lista de veículos retornada com sucesso", "model": list[VeiculoResponse]},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição"},
    },
)
async def listar(
    usecase: ListarVeiculos,
    cliente_id: UUID | None = None,
    placa: str | None = None,
    marca: str | None = None,
    modelo: str | None = None,
) -> list[VeiculoResponse]:
    filtros = ListarVeiculosFiltro(
        cliente_id=cliente_id,
        placa=placa,
        marca=marca,
        modelo=modelo,
    )
    return await usecase.execute(filtros)


@router.get(
    "/{veiculo_id}",
    summary="Busca veículo por ID",
    description="""Retorna os dados detalhados de um veículo.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Veículo encontrado", "model": VeiculoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Veículo não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def obter(
    veiculo_id: UUID,
    usecase: ObterVeiculoPorId,
) -> VeiculoResponse:
    try:
        return await usecase.execute(str(veiculo_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except VeiculoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")


@router.patch(
    "/{veiculo_id}",
    summary="Atualiza dados de um veículo",
    description="""Atualiza parcialmente os dados de um veículo existente.
> **Nota:** cliente_id e placa não podem ser alterados por esta rota.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Veículo atualizado com sucesso", "model": VeiculoResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Veículo não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def atualizar(
    veiculo_id: UUID,
    dto: AtualizarVeiculo,
    usecase: AtualizarVeiculoDep,
) -> VeiculoResponse:
    try:
        return await usecase.execute(str(veiculo_id), dto)
    except VeiculoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    except VeiculoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{veiculo_id}",
    status_code=204,
    summary="Remove um veículo",
    description="""Remove permanentemente o veículo informado do sistema.

Em caso de sucesso, retorna `204 No Content` sem corpo de resposta.

""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    response_class=Response,
    responses={
        204: {"description": "Veículo removido com sucesso. Resposta sem corpo."},
        **_RESPONSES_AUTH,
        404: {"description": "Veículo não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def remover(veiculo_id: UUID, usecase: RemoverVeiculoDep) -> None:
    if not await usecase.execute(str(veiculo_id)):
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
