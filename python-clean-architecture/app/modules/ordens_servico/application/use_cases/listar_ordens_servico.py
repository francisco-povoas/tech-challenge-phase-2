"""Use case: Listar Ordens de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoResumoResponse
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico
from app.modules.ordens_servico.domain.filters.ordem_servico import ListarOrdensServicoFiltro
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarOrdensServicoUseCase:
    ordem_servico_repo: OrdemServicoRepo

    async def execute(
        self, filtros: ListarOrdensServicoFiltro
    ) -> list[OrdemServicoResumoResponse]:
        ordens = await self.ordem_servico_repo.listar(filtros)
        logger.debug(f"Listagem de OS retornou {len(ordens)} registro(s)")
        return [_to_resumo(os) for os in ordens]


def _to_resumo(os: OrdemServico) -> OrdemServicoResumoResponse:
    return OrdemServicoResumoResponse(
        id=str(os.id),
        cliente_id=str(os.cliente_id),
        veiculo_id=str(os.veiculo_id),
        status=os.status.value,
        queixa_inicial=os.queixa_inicial,
        diagnostico=os.diagnostico,
        criado_em=os.criado_em,
        atualizado_em=os.atualizado_em,
        iniciado_diagnostico_em=os.iniciado_diagnostico_em,
        diagnostico_concluido_em=os.diagnostico_concluido_em,
    )
