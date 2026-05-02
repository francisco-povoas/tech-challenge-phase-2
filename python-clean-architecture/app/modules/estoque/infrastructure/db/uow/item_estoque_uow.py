from app.shared.infra.db import DBSession
from app.shared.infra.db.base_uow import BaseUnitOfWork
from app.modules.estoque.infrastructure.db.repositories.item_estoque_repo import ItemEstoqueRepo


class ItemEstoqueUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: DBSession) -> None:
        super().__init__(session)
        self.item_estoque_repo = ItemEstoqueRepo(session)


def item_estoque_uow_factory(session: DBSession) -> ItemEstoqueUnitOfWork:
    return ItemEstoqueUnitOfWork(session)
