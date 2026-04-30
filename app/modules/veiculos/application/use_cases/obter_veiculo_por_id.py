from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.veiculos.application.dtos.veiculo import VeiculoResponse
from app.modules.veiculos.domain.exceptions import VeiculoNaoEncontradoError
from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterVeiculoPorIdUseCase:
    veiculo_repo: VeiculoRepo

    async def execute(self, veiculo_id: str) -> VeiculoResponse:
        """Retorna os dados de um veículo pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            VeiculoNaoEncontradoError: Se o veículo não for encontrado.
        """
        id_value = ID.from_string(veiculo_id)
        veiculo = await self.veiculo_repo.obter_por_id(id_value)

        if not veiculo:
            raise VeiculoNaoEncontradoError(f"Veículo com ID {veiculo_id} não encontrado.")

        logger.info(f"Veículo {veiculo_id} obtido com sucesso")
        return VeiculoResponse(
            id=str(veiculo.id),
            cliente_id=str(veiculo.cliente_id),
            placa=veiculo.placa.value,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano_fabricacao=veiculo.ano_fabricacao,
            ano_modelo=veiculo.ano_modelo,
            cor=veiculo.cor,
        )
