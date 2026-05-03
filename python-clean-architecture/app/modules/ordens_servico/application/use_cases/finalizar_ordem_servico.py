"""Use case: Finalizar uma Ordem de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoDetalheResponse
from app.modules.ordens_servico.application.use_cases.obter_ordem_servico_por_id import _to_detalhe
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoPossuiServicoSemTempoExecutadoError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class FinalizarOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(self, ordem_servico_id: str) -> OrdemServicoDetalheResponse:
        _id = ID.from_string(ordem_servico_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Buscar serviços da OS
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_id)
            servicos_ativos = [s for s in servicos if not s.cancelado]

            # 3. Verificar se todos os serviços ativos têm tempo executado
            tem_tempo = [
                s.tempo_executado_minutos is not None and s.tempo_executado_minutos > 0
                for s in servicos_ativos
            ]

            # 4. Transitar OS: EM_EXECUCAO -> FINALIZADA (valida status e serviços sem tempo)
            os_finalizada = os.finalizar(servicos_ativos_com_tempo=tem_tempo)

            # 5. Persistir OS atualizada
            await self.uow.ordem_servico_repo.atualizar(os_finalizada)

            # 6. Commit
            await self.uow.commit()

            # 7. Buscar itens para montar resposta
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)

            logger.info(f"OS '{ordem_servico_id}' finalizada com sucesso.")
            return _to_detalhe(os_finalizada, servicos, itens)
