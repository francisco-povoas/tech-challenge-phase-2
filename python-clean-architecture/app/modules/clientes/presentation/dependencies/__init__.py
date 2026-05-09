"""Dependências de infraestrutura do módulo Clientes para injeção via FastAPI."""
from typing import Annotated

from fastapi import Depends

from app.shared.infra.db import get_db_session, DBSession
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo as ClienteRepoProtocol
from app.modules.clientes.domain.ports.cliente_uow import ClienteUnitOfWork as ClienteUoWProtocol
from app.modules.clientes.infrastructure.db.repositories.cliente_repo import ClienteRepo
from app.modules.clientes.infrastructure.db.uow.cliente_uow import cliente_uow_factory
from app.modules.clientes.application.use_cases import (
    CriarClienteUseCase,
    ObterClientePorIdUseCase,
    ObterClientePorCpfCnpjUseCase,
    ListarClientesUseCase,
    AtualizarClienteUseCase,
    AtivarClienteUseCase,
    DesativarClienteUseCase,
    RemoverClienteUseCase,
)


# --- Infraestrutura ---

def get_cliente_repo(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ClienteRepoProtocol:
    return ClienteRepo(session)


def get_cliente_uow(
    session: Annotated[DBSession, Depends(get_db_session)],
) -> ClienteUoWProtocol:
    return cliente_uow_factory(session)  # type: ignore[misc]


_RepoDep = Annotated[ClienteRepoProtocol, Depends(get_cliente_repo)]
_UoWDep = Annotated[ClienteUoWProtocol, Depends(get_cliente_uow)]


# --- Use Cases ---

def get_criar_cliente(uow: _UoWDep) -> CriarClienteUseCase:
    return CriarClienteUseCase(uow=uow)


def get_obter_cliente_por_id(repo: _RepoDep) -> ObterClientePorIdUseCase:
    return ObterClientePorIdUseCase(cliente_repo=repo)


def get_obter_cliente_por_cpf_cnpj(repo: _RepoDep) -> ObterClientePorCpfCnpjUseCase:
    return ObterClientePorCpfCnpjUseCase(cliente_repo=repo)


def get_listar_clientes(repo: _RepoDep) -> ListarClientesUseCase:
    return ListarClientesUseCase(cliente_repo=repo)


def get_atualizar_cliente(uow: _UoWDep) -> AtualizarClienteUseCase:
    return AtualizarClienteUseCase(uow=uow)


def get_ativar_cliente(uow: _UoWDep) -> AtivarClienteUseCase:
    return AtivarClienteUseCase(uow=uow)


def get_desativar_cliente(uow: _UoWDep) -> DesativarClienteUseCase:
    return DesativarClienteUseCase(uow=uow)


def get_remover_cliente(uow: _UoWDep) -> RemoverClienteUseCase:
    return RemoverClienteUseCase(uow=uow)


CriarCliente = Annotated[CriarClienteUseCase, Depends(get_criar_cliente)]
ObterClientePorId = Annotated[ObterClientePorIdUseCase, Depends(get_obter_cliente_por_id)]
ObterClientePorCpfCnpj = Annotated[ObterClientePorCpfCnpjUseCase, Depends(get_obter_cliente_por_cpf_cnpj)]
ListarClientes = Annotated[ListarClientesUseCase, Depends(get_listar_clientes)]
AtualizarClienteDep = Annotated[AtualizarClienteUseCase, Depends(get_atualizar_cliente)]
AtivarClienteDep = Annotated[AtivarClienteUseCase, Depends(get_ativar_cliente)]
DesativarClienteDep = Annotated[DesativarClienteUseCase, Depends(get_desativar_cliente)]
RemoverClienteDep = Annotated[RemoverClienteUseCase, Depends(get_remover_cliente)]
