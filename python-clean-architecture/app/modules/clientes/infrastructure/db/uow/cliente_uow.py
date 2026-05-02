from app.shared.infra.db import DBSession
from app.shared.infra.db.base_uow import BaseUnitOfWork
from app.modules.clientes.infrastructure.db.repositories.cliente_repo import ClienteRepo


class ClienteUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: DBSession) -> None:
        super().__init__(session)
        self.cliente_repo = ClienteRepo(session)


def cliente_uow_factory(session: DBSession) -> ClienteUnitOfWork:
    return ClienteUnitOfWork(session)
