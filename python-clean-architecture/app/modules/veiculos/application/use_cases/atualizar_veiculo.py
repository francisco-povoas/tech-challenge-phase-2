from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.veiculos.application.dtos.veiculo import AtualizarVeiculo, VeiculoResponse
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.exceptions import (
    VeiculoInvalidoError,
    VeiculoNaoEncontradoError,
)
from app.modules.veiculos.domain.ports.veiculo_uow import VeiculoUnitOfWork
from app.modules.veiculos.domain.value_objects.placa import Placa

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtualizarVeiculoUseCase:
    uow: VeiculoUnitOfWork

    async def execute(self, veiculo_id: str, dto: AtualizarVeiculo) -> VeiculoResponse:
        """Atualiza os dados de um veículo existente (PATCH — preserva campos não informados).

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            VeiculoNaoEncontradoError: Se o veículo não for encontrado.
            VeiculoInvalidoError: Se os novos dados forem inválidos.
        """
        id_value = ID.from_string(veiculo_id)

        async with self.uow:
            existente = await self.uow.veiculo_repo.obter_por_id(id_value)
            if not existente:
                raise VeiculoNaoEncontradoError(
                    f"Veículo com ID {veiculo_id} não encontrado."
                )

            agora = datetime.now(UTC)

            atualizado = await self.uow.veiculo_repo.atualizar(
                Veiculo(
                    id=existente.id,
                    cliente_id=existente.cliente_id,
                    placa=existente.placa,
                    marca=dto.marca if dto.marca is not None else existente.marca,
                    modelo=dto.modelo if dto.modelo is not None else existente.modelo,
                    ano_fabricacao=dto.ano_fabricacao if dto.ano_fabricacao is not None else existente.ano_fabricacao,
                    ano_modelo=dto.ano_modelo if dto.ano_modelo is not None else existente.ano_modelo,
                    cor=dto.cor if dto.cor is not None else existente.cor,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise VeiculoNaoEncontradoError(
                    f"Veículo com ID {veiculo_id} não encontrado."
                )

            logger.info(f"Veículo {veiculo_id} atualizado com sucesso")
            return VeiculoResponse(
                id=str(atualizado.id),
                cliente_id=str(atualizado.cliente_id),
                placa=atualizado.placa.value,
                marca=atualizado.marca,
                modelo=atualizado.modelo,
                ano_fabricacao=atualizado.ano_fabricacao,
                ano_modelo=atualizado.ano_modelo,
                cor=atualizado.cor,
            )
