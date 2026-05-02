"""Use case: Criar Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo
from app.modules.veiculos.domain.exceptions import VeiculoNaoEncontradoError
from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    CriarOrdemServicoRequest,
    OrdemServicoResumoResponse,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.exceptions import OrdemServicoInvalidaError
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class CriarOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork
    cliente_repo: ClienteRepo
    veiculo_repo: VeiculoRepo

    async def execute(self, dto: CriarOrdemServicoRequest) -> OrdemServicoResumoResponse:
        cliente_id = ID.from_string(dto.cliente_id)
        veiculo_id = ID.from_string(dto.veiculo_id)

        # Validar cliente
        cliente = await self.cliente_repo.obter_por_id(cliente_id)
        if not cliente:
            raise ClienteNaoEncontradoError(
                f"Cliente com ID {dto.cliente_id} não encontrado."
            )

        # Validar veículo
        veiculo = await self.veiculo_repo.obter_por_id(veiculo_id)
        if not veiculo:
            raise VeiculoNaoEncontradoError(
                f"Veículo com ID {dto.veiculo_id} não encontrado."
            )

        # Validar pertencimento do veículo ao cliente
        if str(veiculo.cliente_id) != dto.cliente_id:
            raise OrdemServicoInvalidaError(
                "O veículo informado não pertence ao cliente informado."
            )

        agora = datetime.now(UTC)
        os = OrdemServico(
            id=ID.generate(),
            cliente_id=UUID(dto.cliente_id),
            veiculo_id=UUID(dto.veiculo_id),
            status=StatusOrdemServico.RECEBIDA,
            queixa_inicial=dto.queixa_inicial,
            diagnostico=None,
            criado_em=agora,
            atualizado_em=agora,
            iniciado_diagnostico_em=None,
            diagnostico_concluido_em=None,
        )

        async with self.uow:
            await self.uow.ordem_servico_repo.salvar(os)
            logger.info(f"OS '{os.id}' criada para cliente '{dto.cliente_id}'")

        return _to_resumo(os)


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
