"""Use case: Remover (cancelar) Serviço de uma Ordem de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoInvalidaError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoServicoNaoEncontradoError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RemoverServicoDaOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self, ordem_servico_id: str, ordem_servico_servico_id: str
    ) -> None:
        os_id = ID.from_string(ordem_servico_id)
        oss_id = ID.from_string(ordem_servico_servico_id)

        async with self.uow:
            os = await self.uow.ordem_servico_repo.obter_por_id(os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            if os.status != StatusOrdemServico.EM_DIAGNOSTICO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível remover serviços em OS com status "
                    f"'EM_DIAGNOSTICO'. Status atual: '{os.status.value}'."
                )

            os_servico = await self.uow.ordem_servico_repo.obter_servico_por_id(oss_id)
            if not os_servico:
                raise OrdemServicoServicoNaoEncontradoError(
                    f"Serviço com ID {ordem_servico_servico_id} não encontrado na OS."
                )

            if str(os_servico.ordem_servico_id) != ordem_servico_id:
                raise OrdemServicoServicoNaoEncontradoError(
                    f"Serviço com ID {ordem_servico_servico_id} não pertence à OS {ordem_servico_id}."
                )

            if os_servico.cancelado:
                raise OrdemServicoInvalidaError("O serviço já foi cancelado.")

            # Marcar como cancelado (soft delete)
            os_servico_cancelado = OrdemServicoServico(
                id=os_servico.id,
                ordem_servico_id=os_servico.ordem_servico_id,
                servico_id=os_servico.servico_id,
                nome_servico=os_servico.nome_servico,
                descricao_servico=os_servico.descricao_servico,
                valor_unitario=os_servico.valor_unitario,
                tempo_estimado_minutos=os_servico.tempo_estimado_minutos,
                tempo_executado_minutos=os_servico.tempo_executado_minutos,
                observacao=os_servico.observacao,
                cancelado=True,
            )

            await self.uow.ordem_servico_repo.atualizar_servico(os_servico_cancelado)
            logger.info(
                f"Serviço '{ordem_servico_servico_id}' cancelado da OS '{ordem_servico_id}'"
            )
