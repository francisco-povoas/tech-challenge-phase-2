"""Dependências de infraestrutura do módulo Estoque para injeção via FastAPI."""
from typing import Annotated

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.modules.estoque.domain.ports.item_estoque_repo import ItemEstoqueRepo as ItemEstoqueRepoProtocol
from app.modules.estoque.domain.ports.item_estoque_uow import ItemEstoqueUnitOfWork as ItemEstoqueUoWProtocol
from app.modules.estoque.infrastructure.db.repositories.item_estoque_repo import ItemEstoqueRepo
from app.modules.estoque.infrastructure.db.uow.item_estoque_uow import item_estoque_uow_factory
from app.modules.estoque.application.use_cases import (
    CriarItemEstoqueUseCase,
    ObterItemEstoquePorIdUseCase,
    ListarItensEstoqueUseCase,
    AtualizarItemEstoqueUseCase,
    AtivarItemEstoqueUseCase,
    DesativarItemEstoqueUseCase,
)


# --- Infraestrutura ---

async def get_item_estoque_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ItemEstoqueRepoProtocol:
    return ItemEstoqueRepo(session)


async def get_item_estoque_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ItemEstoqueUoWProtocol:
    return item_estoque_uow_factory(session)  # type: ignore[misc]


_RepoDep = Annotated[ItemEstoqueRepoProtocol, Depends(get_item_estoque_repo)]
_UoWDep = Annotated[ItemEstoqueUoWProtocol, Depends(get_item_estoque_uow)]


# --- Use Cases ---

def get_criar_item_estoque(uow: _UoWDep) -> CriarItemEstoqueUseCase:
    return CriarItemEstoqueUseCase(uow=uow)


def get_obter_item_estoque_por_id(repo: _RepoDep) -> ObterItemEstoquePorIdUseCase:
    return ObterItemEstoquePorIdUseCase(item_estoque_repo=repo)


def get_listar_itens_estoque(repo: _RepoDep) -> ListarItensEstoqueUseCase:
    return ListarItensEstoqueUseCase(item_estoque_repo=repo)


def get_atualizar_item_estoque(uow: _UoWDep) -> AtualizarItemEstoqueUseCase:
    return AtualizarItemEstoqueUseCase(uow=uow)


def get_ativar_item_estoque(uow: _UoWDep) -> AtivarItemEstoqueUseCase:
    return AtivarItemEstoqueUseCase(uow=uow)


def get_desativar_item_estoque(uow: _UoWDep) -> DesativarItemEstoqueUseCase:
    return DesativarItemEstoqueUseCase(uow=uow)


CriarItemEstoque = Annotated[CriarItemEstoqueUseCase, Depends(get_criar_item_estoque)]
ObterItemEstoquePorId = Annotated[ObterItemEstoquePorIdUseCase, Depends(get_obter_item_estoque_por_id)]
ListarItensEstoque = Annotated[ListarItensEstoqueUseCase, Depends(get_listar_itens_estoque)]
AtualizarItemEstoqueDep = Annotated[AtualizarItemEstoqueUseCase, Depends(get_atualizar_item_estoque)]
AtivarItemEstoqueDep = Annotated[AtivarItemEstoqueUseCase, Depends(get_ativar_item_estoque)]
DesativarItemEstoqueDep = Annotated[DesativarItemEstoqueUseCase, Depends(get_desativar_item_estoque)]
