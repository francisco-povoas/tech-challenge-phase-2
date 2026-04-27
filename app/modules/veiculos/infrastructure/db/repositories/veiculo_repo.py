from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.infrastructure.db.models.veiculo import VeiculoModel


class VeiculoRepo:
    """Implementação concreta do repositório de veículos."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, veiculo: Veiculo) -> None:
        model = VeiculoModel(
            id=veiculo.id.value,
            placa=veiculo.placa,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano=veiculo.ano,
            cliente_id=veiculo.cliente_id,
        )
        self.session.add(model)

    async def obter_por_id(self, _id: ID) -> Optional[Veiculo]:
        model = await self.session.get(VeiculoModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_placa(self, placa: str) -> Optional[Veiculo]:
        result = await self.session.exec(
            select(VeiculoModel).where(VeiculoModel.placa == placa)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def listar_por_cliente(self, cliente_id: str) -> list[Veiculo]:
        result = await self.session.exec(
            select(VeiculoModel).where(VeiculoModel.cliente_id == cliente_id)
        )
        return [self._to_entity(m) for m in result.all()]

    async def remover(self, _id: ID) -> bool:
        model = await self.session.get(VeiculoModel, _id.value)
        if not model:
            return False
        await self.session.delete(model)
        return True

    @staticmethod
    def _to_entity(model: VeiculoModel) -> Veiculo:
        return Veiculo(
            id=ID.from_string(str(model.id)),
            placa=model.placa,
            marca=model.marca,
            modelo=model.modelo,
            ano=model.ano,
            cliente_id=model.cliente_id,
        )
