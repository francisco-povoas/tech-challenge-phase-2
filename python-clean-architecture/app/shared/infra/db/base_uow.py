from typing import Protocol

from app.shared.infra.db import DBSession


class UnitOfWork(Protocol):
    """Protocolo do padrão Unit of Work.

    Garante que todas as operações dentro de uma unidade sejam confirmadas
    ou revertidas atomicamente.
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self): ...

    async def rollback(self): ...


class BaseUnitOfWork(UnitOfWork):
    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
