import re
from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.veiculos.application.dtos.veiculo import VeiculoResponse
from app.modules.veiculos.domain.exceptions import VeiculoNaoEncontradoError
from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterVeiculoPorPlacaUseCase:
    veiculo_repo: VeiculoRepo

    async def execute(self, placa: str) -> VeiculoResponse:
        """Retorna os dados de um veículo pela placa (normalizada).

        Raises:
            VeiculoNaoEncontradoError: Se o veículo não for encontrado.
        """
        normalized = re.sub(r"[\s\-]", "", placa).upper()
        veiculo = await self.veiculo_repo.obter_por_placa(normalized)

        if not veiculo:
            raise VeiculoNaoEncontradoError(
                f"Veículo com placa {normalized} não encontrado."
            )

        logger.info(f"Veículo com placa {normalized} obtido com sucesso")
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
