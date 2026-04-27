from app.shared.infra.db import DBSession
from app.shared.infra.db.base_uow import BaseUnitOfWork
from app.modules.veiculos.infrastructure.db.repositories.veiculo_repo import VeiculoRepo


class VeiculoUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: DBSession) -> None:
        super().__init__(session)
        self.veiculo_repo = VeiculoRepo(session)


def veiculo_uow_factory(session: DBSession) -> VeiculoUnitOfWork:
    return VeiculoUnitOfWork(session)
