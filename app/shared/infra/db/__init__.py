from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings

DBSession = AsyncSession

# Module-level cache for engine and session factory (initialized on first call)
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """
    Factory function for lazy initialization of async engine.
    
    This function ensures the engine is only created when actually needed,
    not during module import. This allows unit tests to import application
    modules without requiring a configured database.
    
    Returns:
        AsyncEngine instance (cached after first call)
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.DB_URL, echo=False)
    return _engine


def get_session_factory() -> async_sessionmaker:
    """
    Create async session factory bound to the given engine.
    
    Returns:
        async_sessionmaker configured for use with the engine
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=DBSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[DBSession, None]:
    """
    Dependency function to provide a database session for FastAPI routes.
    
    Lazily initializes engine and session factory on first call.
    This is the primary injection point for all modules.
    
    Usage in dependencies:
        async def get_usuario_repo(
            session: Annotated[DBSession, Depends(get_db_session)]
        ) -> UsuarioRepo:
            return UsuarioRepo(session)
    
    Yields:
        AsyncSession instance for the duration of the request
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """
    Dispose the cached engine (if initialized) and clear DB caches.

    This is the public API for application shutdown cleanup.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def reset_engine() -> None:
    """
    Reset the cached engine and session factory. Useful for testing.
    This should be called after dispose() to allow re-initialization.
    """
    global _engine, _session_factory
    _engine = None
    _session_factory = None
