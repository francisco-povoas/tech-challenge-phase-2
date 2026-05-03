"""Use case: Obter Estatística de Tempo de Execução de um Serviço do Catálogo."""

from dataclasses import dataclass
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.infrastructure.db.repositories.servico_repo import ServicoRepo
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    EstatisticaTempoExecucaoServicoResponse,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterEstatisticaTempoExecucaoServicoUseCase:
    """Retorna a estatística agregada de tempo executado para um serviço do catálogo.

    Considera apenas OS FINALIZADA/ENTREGUE, serviços não cancelados e com
    tempo_executado_minutos preenchido.
    """

    ordem_servico_repo: OrdemServicoRepo
    servico_repo: ServicoRepo

    async def execute(self, servico_id: str) -> EstatisticaTempoExecucaoServicoResponse:
        _id = ID.from_string(servico_id)

        # 1. Verificar se o serviço do catálogo existe
        servico = await self.servico_repo.obter_por_id(_id)
        if not servico:
            raise ServicoNaoEncontradoError("Serviço não encontrado.")

        # 2. Buscar estatística das execuções (somente leitura — sem commit)
        stats = await self.ordem_servico_repo.obter_estatistica_tempo_execucao_servico(
            UUID(servico_id)
        )

        logger.info(
            "Estatística de tempo de execução obtida para servico_id=%s: %s",
            servico_id,
            stats,
        )

        return EstatisticaTempoExecucaoServicoResponse(
            servico_id=servico_id,
            nome_servico=servico.nome,
            tempo_estimado_minutos=servico.tempo_medio_minutos,
            quantidade_ordens_servico=stats["quantidade"],
            tempo_medio_minutos=stats["media"],
            menor_tempo_minutos=stats["menor"],
            maior_tempo_minutos=stats["maior"],
        )
