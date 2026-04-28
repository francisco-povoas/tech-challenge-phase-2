from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.clientes.domain.ports.cliente_uow import ClienteUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RemoverClienteUseCase:
    uow: ClienteUnitOfWork

    async def execute(self, cliente_id: str) -> bool:
        """Remove um cliente pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
        """
        async with self.uow:
            id_value = ID.from_string(cliente_id)
            resultado = await self.uow.cliente_repo.remover(id_value)

            if resultado:
                logger.info(f"Cliente {cliente_id} removido com sucesso")
            return resultado
