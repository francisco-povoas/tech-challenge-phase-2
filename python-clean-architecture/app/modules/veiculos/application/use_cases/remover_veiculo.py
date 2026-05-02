from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.ports.veiculo_uow import VeiculoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RemoverVeiculoUseCase:
    uow: VeiculoUnitOfWork

    async def execute(self, veiculo_id: str) -> bool:
        """Remove um veículo pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
        """
        async with self.uow:
            id_value = ID.from_string(veiculo_id)
            resultado = await self.uow.veiculo_repo.remover(id_value)

            if resultado:
                logger.info(f"Veículo {veiculo_id} removido com sucesso")
            return resultado
