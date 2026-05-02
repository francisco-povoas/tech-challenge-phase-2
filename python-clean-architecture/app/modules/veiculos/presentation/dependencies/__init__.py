"""Dependências de infraestrutura do módulo Veículos para injeção via FastAPI."""
from typing import Annotated

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.modules.clientes.infrastructure.db.repositories.cliente_repo import ClienteRepo as ClienteRepoImpl
from app.modules.veiculos.domain.ports.veiculo_repo import VeiculoRepo as VeiculoRepoProtocol
from app.modules.veiculos.domain.ports.veiculo_uow import VeiculoUnitOfWork as VeiculoUoWProtocol
from app.modules.veiculos.infrastructure.db.repositories.veiculo_repo import VeiculoRepo
from app.modules.veiculos.infrastructure.db.uow.veiculo_uow import veiculo_uow_factory
from app.modules.veiculos.application.use_cases import (
    CriarVeiculoUseCase,
    ObterVeiculoPorIdUseCase,
    ObterVeiculoPorPlacaUseCase,
    ListarVeiculosUseCase,
    AtualizarVeiculoUseCase,
    RemoverVeiculoUseCase,
)


# --- Infraestrutura ---

async def get_veiculo_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> VeiculoRepoProtocol:
    return VeiculoRepo(session)


async def get_veiculo_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> VeiculoUoWProtocol:
    return veiculo_uow_factory(session)  # type: ignore[misc]


async def get_cliente_repo_for_veiculo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ClienteRepoImpl:
    return ClienteRepoImpl(session)


_RepoDep = Annotated[VeiculoRepoProtocol, Depends(get_veiculo_repo)]
_UoWDep = Annotated[VeiculoUoWProtocol, Depends(get_veiculo_uow)]
_ClienteRepoDep = Annotated[ClienteRepoImpl, Depends(get_cliente_repo_for_veiculo)]


# --- Use Cases ---

def get_criar_veiculo(uow: _UoWDep, cliente_repo: _ClienteRepoDep) -> CriarVeiculoUseCase:
    return CriarVeiculoUseCase(uow=uow, cliente_repo=cliente_repo)


def get_obter_veiculo_por_id(repo: _RepoDep) -> ObterVeiculoPorIdUseCase:
    return ObterVeiculoPorIdUseCase(veiculo_repo=repo)


def get_obter_veiculo_por_placa(repo: _RepoDep) -> ObterVeiculoPorPlacaUseCase:
    return ObterVeiculoPorPlacaUseCase(veiculo_repo=repo)


def get_listar_veiculos(repo: _RepoDep) -> ListarVeiculosUseCase:
    return ListarVeiculosUseCase(veiculo_repo=repo)


def get_atualizar_veiculo(uow: _UoWDep) -> AtualizarVeiculoUseCase:
    return AtualizarVeiculoUseCase(uow=uow)


def get_remover_veiculo(uow: _UoWDep) -> RemoverVeiculoUseCase:
    return RemoverVeiculoUseCase(uow=uow)


CriarVeiculo = Annotated[CriarVeiculoUseCase, Depends(get_criar_veiculo)]
ObterVeiculoPorId = Annotated[ObterVeiculoPorIdUseCase, Depends(get_obter_veiculo_por_id)]
ObterVeiculoPorPlaca = Annotated[ObterVeiculoPorPlacaUseCase, Depends(get_obter_veiculo_por_placa)]
ListarVeiculos = Annotated[ListarVeiculosUseCase, Depends(get_listar_veiculos)]
AtualizarVeiculoDep = Annotated[AtualizarVeiculoUseCase, Depends(get_atualizar_veiculo)]
RemoverVeiculoDep = Annotated[RemoverVeiculoUseCase, Depends(get_remover_veiculo)]
