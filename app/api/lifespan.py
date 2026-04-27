from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings
from app.shared.infra.db import dispose_engine
from app.logger import setup_logger

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    
    Responsibilities:
    - Validate database configuration at startup
    - Log application lifecycle events
    - Clean up database connections at shutdown
    
    Note: Engine initialization is deferred to get_db_session() dependency
    to avoid creating connections before they're needed. The engine is only
    created on the first request that requires a database session.
    """
    settings = get_settings()
    
    # Validate DB_URL is set before application starts
    settings.validate_for_server_start()
    
    logger.info(f"Iniciando aplicação no ambiente {settings.ENV}")

    try:
        yield
    finally:
        try:
            await dispose_engine()
            logger.info("Conexão com o banco de dados encerrada")
        except Exception as e:
            logger.warning(f"Erro ao encerrar conexão com banco: {e}")
