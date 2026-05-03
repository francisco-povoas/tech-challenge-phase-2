"""Use case: Registrar Tempo Executado em Serviço de uma Ordem de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoServicoResponse
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoServicoNaoEncontradoError,
    OrdemServicoServicoCanceladoError,
    OrdemServicoTransicaoInvalidaError,
    TempoExecutadoInvalidoError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RegistrarTempoExecutadoServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self,
        ordem_servico_id: str,
        ordem_servico_servico_id: str,
        tempo_executado_minutos: int,
    ) -> OrdemServicoServicoResponse:
        _os_id = ID.from_string(ordem_servico_id)
        _servico_id = ID.from_string(ordem_servico_servico_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Validar status da OS
            if os.status != StatusOrdemServico.EM_EXECUCAO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível registrar tempo executado em OS com status 'EM_EXECUCAO'. "
                    f"Status atual: '{os.status.value}'."
                )

            # 3. Buscar serviço da OS
            servico = await self.uow.ordem_servico_repo.obter_servico_por_id(_servico_id)
            if not servico:
                raise OrdemServicoServicoNaoEncontradoError(
                    "Serviço da ordem de serviço não encontrado."
                )

            # 4. Validar que serviço pertence à OS informada
            if str(servico.ordem_servico_id) != ordem_servico_id:
                raise OrdemServicoServicoNaoEncontradoError(
                    "Serviço informado não pertence à ordem de serviço."
                )

            # 5. Registrar tempo via método de domínio (valida cancelado e tempo > 0)
            servico_atualizado = servico.registrar_tempo_executado(tempo_executado_minutos)

            # 6. Persistir
            await self.uow.ordem_servico_repo.atualizar_servico(servico_atualizado)

            # 7. Commit
            await self.uow.commit()

            logger.info(
                f"Tempo executado de {tempo_executado_minutos} min registrado no serviço "
                f"'{ordem_servico_servico_id}' da OS '{ordem_servico_id}'."
            )
            return OrdemServicoServicoResponse(
                id=str(servico_atualizado.id),
                servico_id=str(servico_atualizado.servico_id),
                nome_servico=servico_atualizado.nome_servico,
                descricao_servico=servico_atualizado.descricao_servico,
                valor_unitario=servico_atualizado.valor_unitario,
                tempo_estimado_minutos=servico_atualizado.tempo_estimado_minutos,
                tempo_executado_minutos=servico_atualizado.tempo_executado_minutos,
                observacao=servico_atualizado.observacao,
                cancelado=servico_atualizado.cancelado,
            )
