"""Use case: Adicionar Serviço a uma Ordem de Serviço."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.servicos.domain.ports.servico_repo import ServicoRepo
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    AdicionarServicoNaOSRequest,
    OrdemServicoServicoResponse,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
    ServicoJaAdicionadoNaOrdemServicoError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AdicionarServicoNaOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork
    servico_repo: ServicoRepo

    async def execute(
        self, ordem_servico_id: str, dto: AdicionarServicoNaOSRequest
    ) -> OrdemServicoServicoResponse:
        os_id = ID.from_string(ordem_servico_id)
        servico_id = ID.from_string(dto.servico_id)

        # Validar serviço antes da transação
        servico = await self.servico_repo.obter_por_id(servico_id)
        if not servico:
            raise ServicoNaoEncontradoError(
                f"Serviço com ID {dto.servico_id} não encontrado."
            )

        async with self.uow:
            os = await self.uow.ordem_servico_repo.obter_por_id(os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            if os.status != StatusOrdemServico.EM_DIAGNOSTICO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível adicionar serviços em OS com status "
                    f"'EM_DIAGNOSTICO'. Status atual: '{os.status.value}'."
                )

            # Verificar duplicidade ativa
            existente = await self.uow.ordem_servico_repo.obter_servico_ativo_por_servico_id(
                os_id, servico_id
            )
            if existente:
                raise ServicoJaAdicionadoNaOrdemServicoError(
                    "Serviço já foi adicionado a esta ordem de serviço."
                )

            os_servico = OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=UUID(ordem_servico_id),
                servico_id=UUID(dto.servico_id),
                nome_servico=servico.nome,
                descricao_servico=servico.descricao,
                valor_unitario=Decimal(str(servico.valor_base)),
                tempo_estimado_minutos=servico.tempo_medio_minutos,
                tempo_executado_minutos=None,
                observacao=dto.observacao,
                cancelado=False,
            )

            await self.uow.ordem_servico_repo.salvar_servico(os_servico)
            logger.info(
                f"Serviço '{dto.servico_id}' adicionado à OS '{ordem_servico_id}'"
            )

        return OrdemServicoServicoResponse(
            id=str(os_servico.id),
            servico_id=str(os_servico.servico_id),
            nome_servico=os_servico.nome_servico,
            descricao_servico=os_servico.descricao_servico,
            valor_unitario=os_servico.valor_unitario,
            tempo_estimado_minutos=os_servico.tempo_estimado_minutos,
            tempo_executado_minutos=os_servico.tempo_executado_minutos,
            observacao=os_servico.observacao,
            cancelado=os_servico.cancelado,
        )
