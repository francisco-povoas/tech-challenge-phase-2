from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.servicos.application.dtos.servico import ServicoResponse
from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
from app.modules.servicos.domain.ports.servico_repo import ServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarServicosUseCase:
    servico_repo: ServicoRepo

    async def execute(self, filtros: ListarServicosFiltro) -> list[ServicoResponse]:
        """Lista serviços com filtros opcionais por nome e status ativo."""
        servicos = await self.servico_repo.listar(filtros)

        logger.info(
            "Listagem de serviços executada com filtros nome=%s ativo=%s",
            filtros.nome,
            filtros.ativo,
        )
        return [
            ServicoResponse(
                id=str(servico.id),
                nome=servico.nome,
                descricao=servico.descricao,
                valor_base=servico.valor_base,
                tempo_medio_minutos=servico.tempo_medio_minutos,
                ativo=servico.ativo,
            )
            for servico in servicos
        ]
