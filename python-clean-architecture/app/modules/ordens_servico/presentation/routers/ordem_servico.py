"""Router de Ordens de Serviço."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.shared.value_objects.id import InvalidIDError
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.shared.infra.api.dependencies.permissions import RequireRoles
from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.veiculos.domain.exceptions import VeiculoNaoEncontradoError
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    AdicionarItemNaOSRequest,
    AdicionarServicoNaOSRequest,
    CriarOrdemServicoRequest,
    OrdemServicoDetalheResponse,
    OrdemServicoItemResponse,
    OrdemServicoResumoResponse,
    OrdemServicoServicoResponse,
    RegistrarDiagnosticoRequest,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.exceptions import (
    ItemJaAdicionadoNaOrdemServicoError,
    OrdemServicoInvalidaError,
    OrdemServicoItemNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoServicoNaoEncontradoError,
    OrdemServicoTransicaoInvalidaError,
    ServicoJaAdicionadoNaOrdemServicoError,
)
from app.modules.ordens_servico.domain.filters.ordem_servico import ListarOrdensServicoFiltro
from app.modules.ordens_servico.presentation.dependencies import (
    AdicionarItemDep,
    AdicionarServicoDep,
    ConcluirDiagnosticoDep,
    CriarOrdemServicoDep,
    IniciarDiagnosticoDep,
    ListarOrdensServicoDep,
    ObterOrdemServicoPorIdDep,
    RegistrarDiagnosticoDep,
    RemoverItemDep,
    RemoverServicoDep,
)

router = APIRouter()

_ADMIN_ATENDENTE = Depends(
    RequireRoles(PerfilTipos.ADMINISTRADOR, PerfilTipos.ATENDENTE)
)
_ADMIN_MECANICO = Depends(
    RequireRoles(PerfilTipos.ADMINISTRADOR, PerfilTipos.MECANICO)
)
_ADMIN_ATENDENTE_MECANICO = Depends(
    RequireRoles(PerfilTipos.ADMINISTRADOR, PerfilTipos.ATENDENTE, PerfilTipos.MECANICO)
)

_RESPONSES_AUTH = {
    401: {"description": "Token ausente, inválido ou expirado", "model": ErrorResponse},
    403: {"description": "Permissão insuficiente", "model": ErrorResponse},
}


# ---------------------------------------------------------------------------
# Criar OS
# ---------------------------------------------------------------------------


@router.post(
    "",
    status_code=201,
    summary="Criar Ordem de Serviço",
    responses={
        **_RESPONSES_AUTH,
        422: {"description": "Dados inválidos", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def criar_ordem_servico(
    dto: CriarOrdemServicoRequest,
    usecase: CriarOrdemServicoDep,
) -> OrdemServicoResumoResponse:
    try:
        return await usecase.execute(dto)
    except (ClienteNaoEncontradoError, VeiculoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Listar OS
# ---------------------------------------------------------------------------


@router.get(
    "",
    summary="Listar Ordens de Serviço",
    responses=_RESPONSES_AUTH,
    dependencies=[_ADMIN_ATENDENTE_MECANICO],
)
async def listar_ordens_servico(
    usecase: ListarOrdensServicoDep,
    status: Optional[StatusOrdemServico] = None,
    cliente_id: Optional[UUID] = None,
    veiculo_id: Optional[UUID] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> list[OrdemServicoResumoResponse]:
    from datetime import datetime

    filtros = ListarOrdensServicoFiltro(
        status=status,
        cliente_id=str(cliente_id) if cliente_id else None,
        veiculo_id=str(veiculo_id) if veiculo_id else None,
        data_inicio=datetime.fromisoformat(data_inicio) if data_inicio else None,
        data_fim=datetime.fromisoformat(data_fim) if data_fim else None,
    )
    return await usecase.execute(filtros)


# ---------------------------------------------------------------------------
# Detalhar OS
# ---------------------------------------------------------------------------


@router.get(
    "/{ordem_servico_id}",
    summary="Detalhar Ordem de Serviço",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE_MECANICO],
)
async def obter_ordem_servico(
    ordem_servico_id: UUID,
    usecase: ObterOrdemServicoPorIdDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Iniciar Diagnóstico
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/iniciar-diagnostico",
    summary="Iniciar Diagnóstico",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        422: {"description": "Transição inválida", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def iniciar_diagnostico(
    ordem_servico_id: UUID,
    usecase: IniciarDiagnosticoDep,
) -> OrdemServicoResumoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoTransicaoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Registrar Diagnóstico
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/diagnostico",
    summary="Registrar Diagnóstico",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        422: {"description": "Dados inválidos ou transição inválida", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def registrar_diagnostico(
    ordem_servico_id: UUID,
    dto: RegistrarDiagnosticoRequest,
    usecase: RegistrarDiagnosticoDep,
) -> OrdemServicoResumoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto)
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Adicionar Serviço à OS
# ---------------------------------------------------------------------------


@router.post(
    "/{ordem_servico_id}/servicos",
    status_code=201,
    summary="Adicionar Serviço à OS",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS ou Serviço não encontrado", "model": ErrorResponse},
        409: {"description": "Serviço já adicionado à OS", "model": ErrorResponse},
        422: {"description": "Dados inválidos ou status inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def adicionar_servico(
    ordem_servico_id: UUID,
    dto: AdicionarServicoNaOSRequest,
    usecase: AdicionarServicoDep,
) -> OrdemServicoServicoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto)
    except (OrdemServicoNaoEncontradaError, ServicoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ServicoJaAdicionadoNaOrdemServicoError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Remover/Cancelar Serviço da OS
# ---------------------------------------------------------------------------


@router.delete(
    "/{ordem_servico_id}/servicos/{ordem_servico_servico_id}",
    status_code=204,
    summary="Remover Serviço da OS",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS ou vínculo de serviço não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido para a operação", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def remover_servico(
    ordem_servico_id: UUID,
    ordem_servico_servico_id: UUID,
    usecase: RemoverServicoDep,
) -> None:
    try:
        await usecase.execute(str(ordem_servico_id), str(ordem_servico_servico_id))
    except (OrdemServicoNaoEncontradaError, OrdemServicoServicoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Adicionar Item à OS
# ---------------------------------------------------------------------------


@router.post(
    "/{ordem_servico_id}/itens",
    status_code=201,
    summary="Adicionar Item de Estoque à OS",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS ou Item de estoque não encontrado", "model": ErrorResponse},
        409: {"description": "Item já adicionado à OS", "model": ErrorResponse},
        422: {"description": "Dados inválidos ou status inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def adicionar_item(
    ordem_servico_id: UUID,
    dto: AdicionarItemNaOSRequest,
    usecase: AdicionarItemDep,
) -> OrdemServicoItemResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto)
    except (OrdemServicoNaoEncontradaError, ItemEstoqueNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ItemJaAdicionadoNaOrdemServicoError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Remover/Cancelar Item da OS
# ---------------------------------------------------------------------------


@router.delete(
    "/{ordem_servico_id}/itens/{ordem_servico_item_id}",
    status_code=204,
    summary="Remover Item da OS",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS ou vínculo de item não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido para a operação", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def remover_item(
    ordem_servico_id: UUID,
    ordem_servico_item_id: UUID,
    usecase: RemoverItemDep,
) -> None:
    try:
        await usecase.execute(str(ordem_servico_id), str(ordem_servico_item_id))
    except (OrdemServicoNaoEncontradaError, OrdemServicoItemNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Concluir Diagnóstico
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/concluir-diagnostico",
    summary="Concluir Diagnóstico",
    responses={
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        422: {"description": "Requisitos não atendidos para concluir diagnóstico", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def concluir_diagnostico(
    ordem_servico_id: UUID,
    usecase: ConcluirDiagnosticoDep,
) -> OrdemServicoResumoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
