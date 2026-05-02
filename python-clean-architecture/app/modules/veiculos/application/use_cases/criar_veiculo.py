from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo
from app.modules.veiculos.application.dtos.veiculo import CriarVeiculoRequest, VeiculoResponse
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.exceptions import (
    PlacaJaCadastradaError,
    VeiculoInvalidoError,
)
from app.modules.veiculos.domain.ports.veiculo_uow import VeiculoUnitOfWork
from app.modules.veiculos.domain.value_objects.placa import Placa, PlacaInvalidaError

logger = setup_logger(__name__)


@dataclass(frozen=True)
class CriarVeiculoUseCase:
    uow: VeiculoUnitOfWork
    cliente_repo: ClienteRepo

    async def execute(self, dto: CriarVeiculoRequest) -> VeiculoResponse:
        """Cria um novo veículo validando existência e status do cliente.

        Raises:
            VeiculoInvalidoError: Se os dados fornecidos forem inválidos.
            PlacaJaCadastradaError: Se já existir veículo com a mesma placa.
            ClienteNaoEncontradoError: Se o cliente informado não existir.
        """
        try:
            cliente_id_value = ID.from_string(dto.cliente_id)
        except Exception:
            raise VeiculoInvalidoError(f"cliente_id inválido: '{dto.cliente_id}'.")

        try:
            placa = Placa(dto.placa)
        except PlacaInvalidaError as e:
            raise VeiculoInvalidoError(str(e))

        # Valida existência e status do cliente sem alterar o módulo de Cliente
        cliente = await self.cliente_repo.obter_por_id(cliente_id_value)
        if not cliente:
            raise ClienteNaoEncontradoError(
                f"Cliente com ID {dto.cliente_id} não encontrado."
            )
        if not cliente.ativo:
            raise VeiculoInvalidoError(
                f"O cliente com ID {dto.cliente_id} está inativo e não pode ter veículos cadastrados."
            )

        async with self.uow:
            if await self.uow.veiculo_repo.obter_por_placa(placa.value):
                logger.warning(f"Placa {placa.value} já cadastrada")
                raise PlacaJaCadastradaError(
                    f"Já existe um veículo com a placa {placa.value}."
                )

            agora = datetime.now(UTC)

            veiculo = Veiculo(
                id=ID.generate(),
                cliente_id=cliente_id_value.value,
                placa=placa,
                marca=dto.marca,
                modelo=dto.modelo,
                ano_fabricacao=dto.ano_fabricacao,
                ano_modelo=dto.ano_modelo,
                cor=dto.cor,
                criado_em=agora,
                atualizado_em=agora,
            )

            await self.uow.veiculo_repo.salvar(veiculo)
            logger.info(f"Veículo {placa.value} criado com sucesso")

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
