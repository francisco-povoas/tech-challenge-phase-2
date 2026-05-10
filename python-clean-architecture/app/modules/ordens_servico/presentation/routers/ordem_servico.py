"""Router de Ordens de Serviço."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

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
    EstatisticaTempoExecucaoServicoResponse,
    GerarOrcamentoRequest,
    ListagemExecucoesServicoResponse,
    OrcamentoComunicacaoResponse,
    OrcamentoResponse,
    OrdemServicoDetalheResponse,
    OrdemServicoItemResponse,
    OrdemServicoResumoResponse,
    OrdemServicoServicoResponse,
    RecusarOrcamentoRequest,
    RegistrarDiagnosticoRequest,
    RegistrarPagamentoOrdemServicoRequest,
    RegistrarTempoExecutadoServicoRequest,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.exceptions import (
    ClienteSemContatoParaOrcamentoError,
    EstoqueReservadoInsuficienteError,
    ItemJaAdicionadoNaOrdemServicoError,
    ItemOrdemServicoStatusInvalidoError,
    OrcamentoJaExisteParaOrdemServicoError,
    OrcamentoNaoEncontradoError,
    OrcamentoStatusInvalidoError,
    OrdemServicoInvalidaError,
    OrdemServicoItemNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoPagamentoJaRegistradoError,
    OrdemServicoPagamentoNaoRegistradoError,
    OrdemServicoPossuiItemAReceberError,
    OrdemServicoPossuiItemPendenteError,
    OrdemServicoPossuiItemReservadoError,
    OrdemServicoPossuiServicoSemTempoExecutadoError,
    OrdemServicoServicoNaoEncontradoError,
    OrdemServicoTransicaoInvalidaError,
    OrdemServicoServicoCanceladoError,
    ServicoJaAdicionadoNaOrdemServicoError,
    TempoExecutadoInvalidoError,
    ValorPagamentoInvalidoError,
    ValorPagamentoMenorQueOrcamentoError,
)
from app.modules.ordens_servico.domain.filters.ordem_servico import ListarOrdensServicoFiltro
from app.modules.ordens_servico.presentation.dependencies import (
    AdicionarItemDep,
    AdicionarServicoDep,
    AprovarOrcamentoDep,
    ConcluirDiagnosticoDep,
    ConfirmarRecebimentoItemDep,
    CriarOrdemServicoDep,
    EntregarOrdemServicoDep,
    GerarOrcamentoDep,
    IniciarDiagnosticoDep,
    IniciarExecucaoDep,
    ListarComunicacoesDep,
    ListarExecucoesServicoDep,
    ListarOrdensServicoDep,
    ObterEstatisticaTempoExecucaoDep,
    ObterOrcamentoPorOSDep,
    ObterOrdemServicoPorIdDep,
    RecusarOrcamentoDep,
    RegistrarDiagnosticoDep,
    RegistrarPagamentoDep,
    RegistrarTempoExecutadoDep,
    RemoverItemDep,
    RemoverServicoDep,
    FinalizarOrdemServicoDep,
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
        201: {"description": "Ordem de Serviço criada com sucesso", "model": OrdemServicoResumoResponse},
        404: {"description": "Cliente ou veículo não encontrado", "model": ErrorResponse},
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
    status_code=200,
    summary="Listar Ordens de Serviço",
    responses={
        200: {"description": "Lista de Ordens de Serviço retornada com sucesso", "model": list[OrdemServicoResumoResponse]},
        **_RESPONSES_AUTH,
        422: {"description": "Erro de validação da requisição", "model": ErrorResponse},
    },
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

    filtros = ListarOrdensServicoFiltro(
        status=status,
        cliente_id=str(cliente_id) if cliente_id else None,
        veiculo_id=str(veiculo_id) if veiculo_id else None,
        data_inicio=datetime.fromisoformat(data_inicio) if data_inicio else None,
        data_fim=datetime.fromisoformat(data_fim) if data_fim else None,
    )
    return await usecase.execute(filtros)


# ---------------------------------------------------------------------------
# Métricas — Estatística de tempo de execução por serviço do catálogo
# ---------------------------------------------------------------------------


@router.get(
    "/metricas/servicos/{servico_id}/tempo-execucao",
    status_code=200,
    summary="Estatística de tempo de execução de um serviço",
    responses={
        200: {"description": "Estatística retornada com sucesso", "model": EstatisticaTempoExecucaoServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID do serviço inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def obter_estatistica_tempo_execucao_servico(
    servico_id: UUID,
    usecase: ObterEstatisticaTempoExecucaoDep,
) -> EstatisticaTempoExecucaoServicoResponse:

    try:
        return await usecase.execute(str(servico_id))
    except ServicoNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/metricas/servicos/{servico_id}/execucoes",
    status_code=200,
    summary="Listagem de execuções de um serviço",
    responses={
        200: {"description": "Execuções retornadas com sucesso", "model": ListagemExecucoesServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "Serviço não encontrado", "model": ErrorResponse},
        422: {"description": "ID do serviço inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def listar_execucoes_servico(
    servico_id: UUID,
    usecase: ListarExecucoesServicoDep,
) -> ListagemExecucoesServicoResponse:
    try:
        return await usecase.execute(str(servico_id))
    except ServicoNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Detalhar OS
# ---------------------------------------------------------------------------


@router.get(
    "/{ordem_servico_id}",
    status_code=200,
    summary="Detalhar Ordem de Serviço",
    responses={
        200: {"description": "Ordem de Serviço retornada com sucesso", "model": OrdemServicoDetalheResponse},
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
    status_code=200,
    summary="Iniciar Diagnóstico",
    responses={
        200: {"description": "Diagnóstico iniciado com sucesso", "model": OrdemServicoResumoResponse},
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
    status_code=200,
    summary="Registrar Diagnóstico",
    responses={
        200: {"description": "Diagnóstico registrado com sucesso", "model": OrdemServicoResumoResponse},
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
        201: {"description": "Serviço adicionado à OS com sucesso", "model": OrdemServicoServicoResponse},
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
        204: {"description": "Serviço removido da OS com sucesso"},
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
        201: {"description": "Item adicionado à OS com sucesso", "model": OrdemServicoItemResponse},
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
        204: {"description": "Item removido da OS com sucesso"},
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
    status_code=200,
    summary="Concluir Diagnóstico",
    responses={
        200: {"description": "Diagnóstico concluído com sucesso", "model": OrdemServicoResumoResponse},
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


# ---------------------------------------------------------------------------
# Gerar Orçamento
# ---------------------------------------------------------------------------


@router.post(
    "/{ordem_servico_id}/orcamento",
    status_code=201,
    summary="Gerar Orçamento da OS",
    responses={
        201: {"description": "Orçamento gerado com sucesso", "model": OrcamentoResponse},
        **_RESPONSES_AUTH,
        400: {"description": "Cliente sem contato para envio de orçamento", "model": ErrorResponse},
        404: {"description": "OS ou cliente não encontrado", "model": ErrorResponse},
        409: {"description": "Orçamento já existe para esta OS", "model": ErrorResponse},
        422: {"description": "Status inválido ou dados insuficientes", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def gerar_orcamento(
    ordem_servico_id: UUID,
    usecase: GerarOrcamentoDep,
    dto: GerarOrcamentoRequest = GerarOrcamentoRequest(),
) -> OrcamentoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto)
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrcamentoJaExisteParaOrdemServicoError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ClienteSemContatoParaOrcamentoError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (OrdemServicoInvalidaError, OrdemServicoTransicaoInvalidaError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Obter Orçamento da OS
# ---------------------------------------------------------------------------


@router.get(
    "/{ordem_servico_id}/orcamento",
    status_code=200,
    summary="Obter Orçamento da OS",
    responses={
        200: {"description": "Orçamento retornado com sucesso", "model": OrcamentoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou orçamento não encontrado", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE_MECANICO],
)
async def obter_orcamento(
    ordem_servico_id: UUID,
    usecase: ObterOrcamentoPorOSDep,
) -> OrcamentoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except (OrdemServicoNaoEncontradaError, OrcamentoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Listar Comunicações do Orçamento
# ---------------------------------------------------------------------------


@router.get(
    "/{ordem_servico_id}/orcamento/comunicacoes",
    status_code=200,
    summary="Listar Comunicações do Orçamento",
    responses={
        200: {"description": "Comunicações retornadas com sucesso", "model": list[OrcamentoComunicacaoResponse]},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou orçamento não encontrado", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE_MECANICO],
)
async def listar_comunicacoes_orcamento(
    ordem_servico_id: UUID,
    usecase: ListarComunicacoesDep,
) -> list[OrcamentoComunicacaoResponse]:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except (OrdemServicoNaoEncontradaError, OrcamentoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Aprovar Orçamento
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/orcamento/aprovar",
    status_code=200,
    summary="Aprovar Orçamento da OS",
    responses={
        200: {"description": "Orçamento aprovado com sucesso", "model": OrcamentoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou orçamento não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido para a operação", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def aprovar_orcamento(
    ordem_servico_id: UUID,
    usecase: AprovarOrcamentoDep,
) -> OrcamentoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except (OrdemServicoNaoEncontradaError, OrcamentoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoTransicaoInvalidaError, OrcamentoStatusInvalidoError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Recusar Orçamento
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/orcamento/recusar",
    status_code=200,
    summary="Recusar Orçamento da OS",
    responses={
        200: {"description": "Orçamento recusado com sucesso", "model": OrcamentoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou orçamento não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido para a operação", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def recusar_orcamento(
    ordem_servico_id: UUID,
    usecase: RecusarOrcamentoDep,
    dto: RecusarOrcamentoRequest = RecusarOrcamentoRequest(),
) -> OrcamentoResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto.motivo_recusa)
    except (OrdemServicoNaoEncontradaError, OrcamentoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (OrdemServicoTransicaoInvalidaError, OrcamentoStatusInvalidoError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Confirmar Recebimento de Item A_RECEBER
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/itens/{ordem_servico_item_id}/confirmar-recebimento",
    status_code=200,
    summary="Confirmar Recebimento de Item Pendente",
    responses={
        200: {"description": "Recebimento de item confirmado com sucesso", "model": OrdemServicoDetalheResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou item não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido para a operação", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def confirmar_recebimento_item(
    ordem_servico_id: UUID,
    ordem_servico_item_id: UUID,
    usecase: ConfirmarRecebimentoItemDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(
            str(ordem_servico_id),
            str(ordem_servico_item_id),
        )
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoItemNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ItemEstoqueNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoTransicaoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ItemOrdemServicoStatusInvalidoError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

# ---------------------------------------------------------------------------
# Iniciar Execução da OS
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/iniciar-execucao",
    status_code=200,
    summary="Iniciar Execução da OS",
    responses={
        200: {"description": "Execução da OS iniciada com sucesso", "model": OrdemServicoDetalheResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        422: {"description": "Status inválido ou item A_RECEBER pendente", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def iniciar_execucao(
    ordem_servico_id: UUID,
    usecase: IniciarExecucaoDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoPossuiItemAReceberError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OrdemServicoTransicaoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Registrar Tempo Executado em Serviço da OS
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/servicos/{ordem_servico_servico_id}/tempo-executado",
    status_code=200,
    summary="Registrar Tempo Executado em Serviço da OS",
    responses={
        200: {"description": "Tempo executado registrado com sucesso", "model": OrdemServicoServicoResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou serviço não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido, serviço cancelado ou tempo inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def registrar_tempo_executado(
    ordem_servico_id: UUID,
    ordem_servico_servico_id: UUID,
    dto: RegistrarTempoExecutadoServicoRequest,
    usecase: RegistrarTempoExecutadoDep,
) -> OrdemServicoServicoResponse:
    try:
        return await usecase.execute(
            str(ordem_servico_id),
            str(ordem_servico_servico_id),
            dto.tempo_executado_minutos,
        )
    except (OrdemServicoNaoEncontradaError, OrdemServicoServicoNaoEncontradoError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoServicoCanceladoError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except TempoExecutadoInvalidoError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OrdemServicoTransicaoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Finalizar OS
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/finalizar",
    status_code=200,
    summary="Finalizar OS",
    responses={
        200: {"description": "OS finalizada com sucesso", "model": OrdemServicoDetalheResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        422: {"description": "Status inválido ou serviço ativo sem tempo executado", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_MECANICO],
)
async def finalizar_ordem_servico(
    ordem_servico_id: UUID,
    usecase: FinalizarOrdemServicoDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoPossuiServicoSemTempoExecutadoError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except OrdemServicoTransicaoInvalidaError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Registrar Pagamento da OS
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/registrar-pagamento",
    status_code=200,
    summary="Registrar Pagamento da OS",
    responses={
        200: {"description": "Pagamento registrado com sucesso", "model": OrdemServicoDetalheResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS não encontrada", "model": ErrorResponse},
        409: {"description": "Pagamento já registrado", "model": ErrorResponse},
        422: {"description": "Dados inválidos ou status inválido", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def registrar_pagamento(
    ordem_servico_id: UUID,
    dto: RegistrarPagamentoOrdemServicoRequest,
    usecase: RegistrarPagamentoDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(str(ordem_servico_id), dto)
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except OrdemServicoPagamentoJaRegistradoError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (
        OrdemServicoTransicaoInvalidaError,
        ValorPagamentoInvalidoError,
        ValorPagamentoMenorQueOrcamentoError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ---------------------------------------------------------------------------
# Entregar OS
# ---------------------------------------------------------------------------


@router.patch(
    "/{ordem_servico_id}/entregar",
    status_code=200,
    summary="Entregar OS",
    responses={
        200: {"description": "OS entregue ao cliente com sucesso", "model": OrdemServicoDetalheResponse},
        **_RESPONSES_AUTH,
        404: {"description": "OS ou item de estoque não encontrado", "model": ErrorResponse},
        422: {"description": "Status inválido, pagamento não registrado ou inconsistência de itens", "model": ErrorResponse},
    },
    dependencies=[_ADMIN_ATENDENTE],
)
async def entregar_ordem_servico(
    ordem_servico_id: UUID,
    usecase: EntregarOrdemServicoDep,
) -> OrdemServicoDetalheResponse:
    try:
        return await usecase.execute(str(ordem_servico_id))
    except OrdemServicoNaoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ItemEstoqueNaoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (
        OrdemServicoTransicaoInvalidaError,
        OrdemServicoPagamentoNaoRegistradoError,
        OrdemServicoPossuiItemPendenteError,
        OrdemServicoPossuiItemReservadoError,
        EstoqueReservadoInsuficienteError,
        ItemOrdemServicoStatusInvalidoError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InvalidIDError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
