from typing import Optional
from uuid import UUID

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.filters.veiculo import ListarVeiculosFiltro
from app.modules.veiculos.domain.value_objects.placa import Placa
from app.modules.veiculos.infrastructure.db.models.veiculo import VeiculoModel


class VeiculoRepo:
    """Implementação concreta do repositório de veículos (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, veiculo: Veiculo) -> None:
        model = VeiculoModel(
            id=veiculo.id.value,
            cliente_id=veiculo.cliente_id,
            placa=veiculo.placa.value,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano_fabricacao=veiculo.ano_fabricacao,
            ano_modelo=veiculo.ano_modelo,
            cor=veiculo.cor,
            criado_em=veiculo.criado_em,
            atualizado_em=veiculo.atualizado_em,
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

    async def atualizar(self, veiculo: Veiculo) -> Optional[Veiculo]:
        model = await self.session.get(VeiculoModel, veiculo.id.value)
        if not model:
            return None
        model.marca = veiculo.marca
        model.modelo = veiculo.modelo
        model.ano_fabricacao = veiculo.ano_fabricacao
        model.ano_modelo = veiculo.ano_modelo
        model.cor = veiculo.cor
        model.atualizado_em = veiculo.atualizado_em
        self.session.add(model)
        return veiculo

    async def remover(self, _id: ID) -> bool:
        model = await self.session.get(VeiculoModel, _id.value)
        if not model:
            return False
        await self.session.delete(model)
        return True

    async def listar(self, filtros: ListarVeiculosFiltro) -> list[Veiculo]:
        query = select(VeiculoModel)

        if filtros.cliente_id is not None:
            query = query.where(VeiculoModel.cliente_id == filtros.cliente_id)
        if filtros.placa:
            query = query.where(VeiculoModel.placa == filtros.placa.upper())
        if filtros.marca:
            query = query.where(VeiculoModel.marca.ilike(f"%{filtros.marca}%"))
        if filtros.modelo:
            query = query.where(VeiculoModel.modelo.ilike(f"%{filtros.modelo}%"))

        result = await self.session.exec(query)
        return [self._to_entity(model) for model in result.all()]

    @staticmethod
    def _to_entity(model: VeiculoModel) -> Veiculo:
        return Veiculo(
            id=ID.from_string(str(model.id)),
            cliente_id=model.cliente_id,
            placa=Placa(model.placa),
            marca=model.marca,
            modelo=model.modelo,
            ano_fabricacao=model.ano_fabricacao,
            ano_modelo=model.ano_modelo,
            cor=model.cor,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )
