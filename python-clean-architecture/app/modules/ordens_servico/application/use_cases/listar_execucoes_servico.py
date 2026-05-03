"""Use case: Listar Execuções de um Serviço do Catálogo."""

from dataclasses import dataclass
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.infrastructure.db.repositories.servico_repo import ServicoRepo
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    ExecucaoServicoResponse,
    ListagemExecucoesServicoResponse,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarExecucoesServicoUseCase:
    """Lista todas as execuções concluídas de um serviço do catálogo em OS
    FINALIZADA/ENTREGUE, com serviços não cancelados e com tempo_executado_minutos.
    """

    ordem_servico_repo: OrdemServicoRepo
    servico_repo: ServicoRepo

    async def execute(self, servico_id: str) -> ListagemExecucoesServicoResponse:
        _id = ID.from_string(servico_id)

        # 1. Verificar se o serviço do catálogo existe
        servico = await self.servico_repo.obter_por_id(_id)
        if not servico:
            raise ServicoNaoEncontradoError("Serviço não encontrado.")

        # 2. Buscar execuções (somente leitura — sem commit)
        rows = await self.ordem_servico_repo.listar_execucoes_servico(UUID(servico_id))

        execucoes = [
            ExecucaoServicoResponse(
                ordem_servico_id=row["ordem_servico_id"],
                ordem_servico_servico_id=row["ordem_servico_servico_id"],
                tempo_executado_minutos=row["tempo_executado_minutos"],
                status_os=row["status_os"],
            )
            for row in rows
        ]

        logger.info(
            "Execuções listadas para servico_id=%s: %d registro(s)",
            servico_id,
            len(execucoes),
        )

        return ListagemExecucoesServicoResponse(
            servico_id=servico_id,
            nome_servico=servico.nome,
            tempo_estimado_minutos=servico.tempo_medio_minutos,
            quantidade_ordens_servico=len(execucoes),
            execucoes=execucoes,
        )
