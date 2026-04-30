from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.veiculos.application.dtos.veiculo import VeiculoResponse
from app.modules.veiculos.domain.filters.veiculo import ListarVeiculosFiltro
from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarVeiculosUseCase:
    veiculo_repo: VeiculoRepo

    async def execute(self, filtros: ListarVeiculosFiltro) -> list[VeiculoResponse]:
        """Lista veículos com filtros opcionais."""
        veiculos = await self.veiculo_repo.listar(filtros)

        logger.info(
            "Listagem de veículos executada com filtros cliente_id=%s placa=%s marca=%s modelo=%s",
            filtros.cliente_id,
            filtros.placa,
            filtros.marca,
            filtros.modelo,
        )
        return [
            VeiculoResponse(
                id=str(v.id),
                cliente_id=str(v.cliente_id),
                placa=v.placa.value,
                marca=v.marca,
                modelo=v.modelo,
                ano_fabricacao=v.ano_fabricacao,
                ano_modelo=v.ano_modelo,
                cor=v.cor,
            )
            for v in veiculos
        ]
