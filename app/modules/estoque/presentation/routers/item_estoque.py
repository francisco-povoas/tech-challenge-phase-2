from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.shared.value_objects.id import InvalidIDError
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.estoque.application.dtos.item_estoque import (
    AtualizarItemEstoque,
    CriarItemEstoqueRequest,
    ItemEstoqueResponse,
)
from app.modules.estoque.domain.entities.item_estoque import TipoItemEstoque
from app.modules.estoque.domain.exceptions import (
    CodigoItemEstoqueJaCadastradoError,
    ItemEstoqueInvalidoError,
    ItemEstoqueNaoEncontradoError,
)
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro
from app.modules.estoque.presentation.dependencies import (
    AtivarItemEstoqueDep,
    AtualizarItemEstoqueDep,
    CriarItemEstoque,
    DesativarItemEstoqueDep,
    ListarItensEstoque,
    ObterItemEstoquePorId,
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
    summary="Cria um novo item de estoque",
    description="""Cria um novo item de estoque (peça ou insumo).\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        201: {"description": "Item de estoque criado com sucesso", "model": ItemEstoqueResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        409: {"description": "Já existe um item de estoque com este código", "model": ErrorResponse},
        422: {"description": "Erro de validação da requisição"},
    },
)
async def criar(
    dto: CriarItemEstoqueRequest,
    usecase: CriarItemEstoque,
) -> ItemEstoqueResponse:
    try:
        return await usecase.execute(dto)
    except ItemEstoqueInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CodigoItemEstoqueJaCadastradoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "",
    summary="Lista itens de estoque",
    description="""Retorna uma listagem de itens de estoque cadastrados.
Suporta filtros opcionais por `tipo`, `nome`, `codigo`, `ativo` e `baixo_estoque`.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Lista de itens retornada com sucesso", "model": list[ItemEstoqueResponse]},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição"},
    },
)
async def listar(
    usecase: ListarItensEstoque,
    tipo: Optional[TipoItemEstoque] = None,
    nome: Optional[str] = None,
    codigo: Optional[str] = None,
    ativo: Optional[bool] = None,
    baixo_estoque: Optional[bool] = None,
) -> list[ItemEstoqueResponse]:
    filtros = ListarItensEstoqueFiltro(
        tipo=tipo,
        nome=nome,
        codigo=codigo,
        ativo=ativo,
        baixo_estoque=baixo_estoque,
    )
    return await usecase.execute(filtros)


@router.get(
    "/{item_id}",
    summary="Busca item de estoque por ID",
    description="""Retorna os dados detalhados de um item de estoque.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Item encontrado", "model": ItemEstoqueResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Item de estoque não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def obter(
    item_id: UUID,
    usecase: ObterItemEstoquePorId,
) -> ItemEstoqueResponse:
    try:
        return await usecase.execute(str(item_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ItemEstoqueNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")


@router.patch(
    "/{item_id}",
    summary="Atualiza dados de um item de estoque",
    description="""Atualiza parcialmente os dados de um item de estoque existente.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Item atualizado com sucesso", "model": ItemEstoqueResponse},
        400: {"description": "Dados inválidos", "model": ErrorResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Item de estoque não encontrado", "model": ErrorResponse},
        409: {"description": "Já existe um item de estoque com este código", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def atualizar(
    item_id: UUID,
    dto: AtualizarItemEstoque,
    usecase: AtualizarItemEstoqueDep,
) -> ItemEstoqueResponse:
    try:
        return await usecase.execute(str(item_id), dto)
    except ItemEstoqueNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")
    except ItemEstoqueInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CodigoItemEstoqueJaCadastradoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch(
    "/{item_id}/ativar",
    summary="Ativa um item de estoque",
    description="""Ativa um item de estoque previamente desativado.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Item ativado com sucesso", "model": ItemEstoqueResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Item de estoque não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def ativar(
    item_id: UUID,
    usecase: AtivarItemEstoqueDep,
) -> ItemEstoqueResponse:
    try:
        return await usecase.execute(str(item_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ItemEstoqueNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")


@router.patch(
    "/{item_id}/desativar",
    summary="Desativa um item de estoque",
    description="""Desativa um item de estoque sem removê-lo fisicamente do banco.\n""" + _DESC_AUTH,
    dependencies=[_ADMIN_OU_ATENDENTE],
    responses={
        200: {"description": "Item desativado com sucesso", "model": ItemEstoqueResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Item de estoque não encontrado", "model": ErrorResponse},
        422: {"description": "ID inválido ou erro de validação da requisição"},
    },
)
async def desativar(
    item_id: UUID,
    usecase: DesativarItemEstoqueDep,
) -> ItemEstoqueResponse:
    try:
        return await usecase.execute(str(item_id))
    except InvalidIDError as e:
        raise HTTPException(status_code=422, detail=f"ID inválido: {e}")
    except ItemEstoqueNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado")
