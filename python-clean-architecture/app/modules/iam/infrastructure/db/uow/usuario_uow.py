from app.shared.infra.db import DBSession
from app.shared.infra.db.base_uow import BaseUnitOfWork
from app.modules.iam.infrastructure.db.repositories.usuario_repo import UsuarioRepo
from app.modules.iam.infrastructure.db.repositories.perfil_repo import PerfilRepo

class UsuarioUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: DBSession) -> None:
        super().__init__(session)
        self.usuario_repo = UsuarioRepo(session)
        self.perfil_repo = PerfilRepo(session)

def usuario_uow_factory(session: DBSession) -> UsuarioUnitOfWork:
    return UsuarioUnitOfWork(session)
