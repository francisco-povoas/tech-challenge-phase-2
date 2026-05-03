"""Dependências de infraestrutura do módulo Ordens de Serviço para injeção via FastAPI."""

from typing import Annotated

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.shared.infra.notifications.mock_notifiers import MockWhatsAppNotifier, MockEmailNotifier
from app.modules.clientes.infrastructure.db.repositories.cliente_repo import ClienteRepo
from app.modules.veiculos.infrastructure.db.repositories.veiculo_repo import VeiculoRepo
from app.modules.servicos.infrastructure.db.repositories.servico_repo import ServicoRepo
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import (
    OrdemServicoRepo as OrdemServicoRepoProtocol,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import (
    OrdemServicoUnitOfWork as OrdemServicoUoWProtocol,
)
from app.modules.ordens_servico.infrastructure.db.repositories.ordem_servico_repo import (
    OrdemServicoRepo,
)
from app.modules.ordens_servico.infrastructure.db.uow.ordem_servico_uow import (
    ordem_servico_uow_factory,
)
from app.modules.ordens_servico.application.use_cases import (
    AdicionarItemNaOrdemServicoUseCase,
    AdicionarServicoNaOrdemServicoUseCase,
    ConcluirDiagnosticoOrdemServicoUseCase,
    CriarOrdemServicoUseCase,
    IniciarDiagnosticoOrdemServicoUseCase,
    ListarOrdensServicoUseCase,
    ObterOrdemServicoPorIdUseCase,
    RegistrarDiagnosticoOrdemServicoUseCase,
    RemoverItemDaOrdemServicoUseCase,
    RemoverServicoDaOrdemServicoUseCase,
    GerarOrcamentoUseCase,
    ObterOrcamentoPorOrdemServicoUseCase,
    ListarComunicacoesOrcamentoUseCase,
    AprovarOrcamentoUseCase,
    RecusarOrcamentoUseCase,
    ConfirmarRecebimentoItemDaOrdemServicoUseCase,
)


# ---------------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------------


async def get_ordem_servico_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> OrdemServicoRepoProtocol:
    return OrdemServicoRepo(session)  # type: ignore[return-value]


async def get_ordem_servico_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> OrdemServicoUoWProtocol:
    return ordem_servico_uow_factory(session)  # type: ignore[return-value]


async def get_cliente_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ClienteRepo:
    return ClienteRepo(session)


async def get_veiculo_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> VeiculoRepo:
    return VeiculoRepo(session)


async def get_servico_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ServicoRepo:
    return ServicoRepo(session)


_RepoDep = Annotated[OrdemServicoRepoProtocol, Depends(get_ordem_servico_repo)]
_UoWDep = Annotated[OrdemServicoUoWProtocol, Depends(get_ordem_servico_uow)]
_ClienteRepoDep = Annotated[ClienteRepo, Depends(get_cliente_repo)]
_VeiculoRepoDep = Annotated[VeiculoRepo, Depends(get_veiculo_repo)]
_ServicoRepoDep = Annotated[ServicoRepo, Depends(get_servico_repo)]


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------


def get_criar_ordem_servico(
    uow: _UoWDep,
    cliente_repo: _ClienteRepoDep,
    veiculo_repo: _VeiculoRepoDep,
) -> CriarOrdemServicoUseCase:
    return CriarOrdemServicoUseCase(
        uow=uow, cliente_repo=cliente_repo, veiculo_repo=veiculo_repo
    )


def get_listar_ordens_servico(repo: _RepoDep) -> ListarOrdensServicoUseCase:
    return ListarOrdensServicoUseCase(ordem_servico_repo=repo)


def get_obter_ordem_servico_por_id(repo: _RepoDep) -> ObterOrdemServicoPorIdUseCase:
    return ObterOrdemServicoPorIdUseCase(ordem_servico_repo=repo)


def get_iniciar_diagnostico(uow: _UoWDep) -> IniciarDiagnosticoOrdemServicoUseCase:
    return IniciarDiagnosticoOrdemServicoUseCase(uow=uow)


def get_registrar_diagnostico(uow: _UoWDep) -> RegistrarDiagnosticoOrdemServicoUseCase:
    return RegistrarDiagnosticoOrdemServicoUseCase(uow=uow)


def get_adicionar_servico(
    uow: _UoWDep, servico_repo: _ServicoRepoDep
) -> AdicionarServicoNaOrdemServicoUseCase:
    return AdicionarServicoNaOrdemServicoUseCase(uow=uow, servico_repo=servico_repo)


def get_remover_servico(uow: _UoWDep) -> RemoverServicoDaOrdemServicoUseCase:
    return RemoverServicoDaOrdemServicoUseCase(uow=uow)


def get_adicionar_item(uow: _UoWDep) -> AdicionarItemNaOrdemServicoUseCase:
    return AdicionarItemNaOrdemServicoUseCase(uow=uow)


def get_remover_item(uow: _UoWDep) -> RemoverItemDaOrdemServicoUseCase:
    return RemoverItemDaOrdemServicoUseCase(uow=uow)


def get_concluir_diagnostico(uow: _UoWDep) -> ConcluirDiagnosticoOrdemServicoUseCase:
    return ConcluirDiagnosticoOrdemServicoUseCase(uow=uow)


def get_gerar_orcamento(
    uow: _UoWDep,
    cliente_repo: _ClienteRepoDep,
) -> GerarOrcamentoUseCase:
    return GerarOrcamentoUseCase(
        uow=uow,
        cliente_repo=cliente_repo,
        whatsapp_notifier=MockWhatsAppNotifier(),
        email_notifier=MockEmailNotifier(),
    )


def get_obter_orcamento_por_ordem_servico(repo: _RepoDep) -> ObterOrcamentoPorOrdemServicoUseCase:
    return ObterOrcamentoPorOrdemServicoUseCase(ordem_servico_repo=repo)


def get_listar_comunicacoes_orcamento(repo: _RepoDep) -> ListarComunicacoesOrcamentoUseCase:
    return ListarComunicacoesOrcamentoUseCase(ordem_servico_repo=repo)


def get_aprovar_orcamento(uow: _UoWDep) -> AprovarOrcamentoUseCase:
    return AprovarOrcamentoUseCase(uow=uow)


def get_recusar_orcamento(uow: _UoWDep) -> RecusarOrcamentoUseCase:
    return RecusarOrcamentoUseCase(uow=uow)


def get_confirmar_recebimento_item(uow: _UoWDep) -> ConfirmarRecebimentoItemDaOrdemServicoUseCase:
    return ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=uow)


# ---------------------------------------------------------------------------
# Aliases Annotated para uso nos routers
# ---------------------------------------------------------------------------

CriarOrdemServicoDep = Annotated[CriarOrdemServicoUseCase, Depends(get_criar_ordem_servico)]
ListarOrdensServicoDep = Annotated[ListarOrdensServicoUseCase, Depends(get_listar_ordens_servico)]
ObterOrdemServicoPorIdDep = Annotated[ObterOrdemServicoPorIdUseCase, Depends(get_obter_ordem_servico_por_id)]
IniciarDiagnosticoDep = Annotated[IniciarDiagnosticoOrdemServicoUseCase, Depends(get_iniciar_diagnostico)]
RegistrarDiagnosticoDep = Annotated[RegistrarDiagnosticoOrdemServicoUseCase, Depends(get_registrar_diagnostico)]
AdicionarServicoDep = Annotated[AdicionarServicoNaOrdemServicoUseCase, Depends(get_adicionar_servico)]
RemoverServicoDep = Annotated[RemoverServicoDaOrdemServicoUseCase, Depends(get_remover_servico)]
AdicionarItemDep = Annotated[AdicionarItemNaOrdemServicoUseCase, Depends(get_adicionar_item)]
RemoverItemDep = Annotated[RemoverItemDaOrdemServicoUseCase, Depends(get_remover_item)]
ConcluirDiagnosticoDep = Annotated[ConcluirDiagnosticoOrdemServicoUseCase, Depends(get_concluir_diagnostico)]
GerarOrcamentoDep = Annotated[GerarOrcamentoUseCase, Depends(get_gerar_orcamento)]
ObterOrcamentoPorOSDep = Annotated[ObterOrcamentoPorOrdemServicoUseCase, Depends(get_obter_orcamento_por_ordem_servico)]
ListarComunicacoesDep = Annotated[ListarComunicacoesOrcamentoUseCase, Depends(get_listar_comunicacoes_orcamento)]
AprovarOrcamentoDep = Annotated[AprovarOrcamentoUseCase, Depends(get_aprovar_orcamento)]
RecusarOrcamentoDep = Annotated[RecusarOrcamentoUseCase, Depends(get_recusar_orcamento)]
ConfirmarRecebimentoItemDep = Annotated[ConfirmarRecebimentoItemDaOrdemServicoUseCase, Depends(get_confirmar_recebimento_item)]
