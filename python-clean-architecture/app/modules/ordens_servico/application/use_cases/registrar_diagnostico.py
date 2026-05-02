"""Use case: Registrar Diagnóstico em uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    OrdemServicoResumoResponse,
    RegistrarDiagnosticoRequest,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoInvalidaError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RegistrarDiagnosticoOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self, ordem_servico_id: str, dto: RegistrarDiagnosticoRequest
    ) -> OrdemServicoResumoResponse:
        _id = ID.from_string(ordem_servico_id)

        if not dto.diagnostico or not dto.diagnostico.strip():
            raise OrdemServicoInvalidaError("O diagnóstico não pode ser vazio.")

        async with self.uow:
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            if os.status != StatusOrdemServico.EM_DIAGNOSTICO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível registrar diagnóstico em OS com status "
                    f"'EM_DIAGNOSTICO'. Status atual: '{os.status.value}'."
                )

            agora = datetime.now(UTC)
            os_atualizada = OrdemServico(
                id=os.id,
                cliente_id=os.cliente_id,
                veiculo_id=os.veiculo_id,
                status=os.status,
                queixa_inicial=os.queixa_inicial,
                diagnostico=dto.diagnostico,
                criado_em=os.criado_em,
                atualizado_em=agora,
                iniciado_diagnostico_em=os.iniciado_diagnostico_em,
                diagnostico_concluido_em=os.diagnostico_concluido_em,
            )

            await self.uow.ordem_servico_repo.atualizar(os_atualizada)
            logger.info(f"Diagnóstico registrado para OS '{ordem_servico_id}'")

        return _to_resumo(os_atualizada)


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
