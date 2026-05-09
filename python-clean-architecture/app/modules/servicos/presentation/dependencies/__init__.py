"""Dependências de infraestrutura do módulo Serviços para injeção via FastAPI."""
from typing import Annotated

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.modules.servicos.domain.ports.servico_repo import ServicoRepo as ServicoRepoProtocol
from app.modules.servicos.domain.ports.servico_uow import ServicoUnitOfWork as ServicoUoWProtocol
from app.modules.servicos.infrastructure.db.repositories.servico_repo import ServicoRepo
from app.modules.servicos.infrastructure.db.uow.servico_uow import servico_uow_factory
from app.modules.servicos.application.use_cases import (
    CriarServicoUseCase,
    ObterServicoPorIdUseCase,
    ObterServicoPorNomeUseCase,
    ListarServicosUseCase,
    AtualizarServicoUseCase,
    AtivarServicoUseCase,
    DesativarServicoUseCase,
)


# --- Infraestrutura ---

def get_servico_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ServicoRepoProtocol:
    return ServicoRepo(session)


def get_servico_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ServicoUoWProtocol:
    return servico_uow_factory(session)  # type: ignore[misc]


_RepoDep = Annotated[ServicoRepoProtocol, Depends(get_servico_repo)]
_UoWDep = Annotated[ServicoUoWProtocol, Depends(get_servico_uow)]


# --- Use Cases ---

def get_criar_servico(uow: _UoWDep) -> CriarServicoUseCase:
    return CriarServicoUseCase(uow=uow)


def get_obter_servico_por_id(repo: _RepoDep) -> ObterServicoPorIdUseCase:
    return ObterServicoPorIdUseCase(servico_repo=repo)


def get_obter_servico_por_nome(repo: _RepoDep) -> ObterServicoPorNomeUseCase:
    return ObterServicoPorNomeUseCase(servico_repo=repo)


def get_listar_servicos(repo: _RepoDep) -> ListarServicosUseCase:
    return ListarServicosUseCase(servico_repo=repo)


def get_atualizar_servico(uow: _UoWDep) -> AtualizarServicoUseCase:
    return AtualizarServicoUseCase(uow=uow)


def get_ativar_servico(uow: _UoWDep) -> AtivarServicoUseCase:
    return AtivarServicoUseCase(uow=uow)


def get_desativar_servico(uow: _UoWDep) -> DesativarServicoUseCase:
    return DesativarServicoUseCase(uow=uow)


CriarServico = Annotated[CriarServicoUseCase, Depends(get_criar_servico)]
ObterServicoPorId = Annotated[ObterServicoPorIdUseCase, Depends(get_obter_servico_por_id)]
ObterServicoPorNome = Annotated[ObterServicoPorNomeUseCase, Depends(get_obter_servico_por_nome)]
ListarServicos = Annotated[ListarServicosUseCase, Depends(get_listar_servicos)]
AtualizarServicoDep = Annotated[AtualizarServicoUseCase, Depends(get_atualizar_servico)]
AtivarServicoDep = Annotated[AtivarServicoUseCase, Depends(get_ativar_servico)]
DesativarServicoDep = Annotated[DesativarServicoUseCase, Depends(get_desativar_servico)]
