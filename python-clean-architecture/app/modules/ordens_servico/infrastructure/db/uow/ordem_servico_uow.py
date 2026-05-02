"""Unit of Work concreto do módulo Ordens de Serviço."""

from app.shared.infra.db import DBSession
from app.shared.infra.db.base_uow import BaseUnitOfWork
from app.modules.estoque.infrastructure.db.repositories.item_estoque_repo import ItemEstoqueRepo
from app.modules.ordens_servico.infrastructure.db.repositories.ordem_servico_repo import OrdemServicoRepo


class OrdemServicoUnitOfWork(BaseUnitOfWork):
    """Gerencia a transação que envolve OS e estoque na mesma sessão."""

    def __init__(self, session: DBSession) -> None:
        super().__init__(session)
        self.ordem_servico_repo = OrdemServicoRepo(session)
        self.item_estoque_repo = ItemEstoqueRepo(session)


def ordem_servico_uow_factory(session: DBSession) -> OrdemServicoUnitOfWork:
    return OrdemServicoUnitOfWork(session)
