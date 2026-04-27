import os
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.shared.infra.db as db_module
from app.api.app import create_app
from app.config import get_settings

ROOT_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT_DIR / "alembic.ini"

_TEST_DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5436/app_test",
)


def _make_alembic_config(db_url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def integration_settings():
    os.environ["DB_URL"] = _TEST_DB_URL
    os.environ["ENV"] = "test"
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(integration_settings):
    config = _make_alembic_config(integration_settings.DB_URL)
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest_asyncio.fixture
async def test_engine(integration_settings):
    engine = create_async_engine(
        integration_settings.DB_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=db_module.DBSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
def override_db_module(test_engine, test_session_factory):
    previous_engine = db_module._engine
    previous_session_factory = db_module._session_factory

    db_module._engine = test_engine
    db_module._session_factory = test_session_factory

    yield

    db_module._engine = previous_engine
    db_module._session_factory = previous_session_factory


@pytest_asyncio.fixture(autouse=True)
async def clean_database(test_engine):
    async with test_engine.begin() as conn:
        rows = await conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'alembic_version'
                """
            )
        )
        tables = [f'"{row[0]}"' for row in rows]
        if tables:
            await conn.execute(text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE"))

    yield


@pytest.fixture
def integration_app(integration_settings):
    return create_app(integration_settings)


@pytest_asyncio.fixture
async def client(integration_app, integration_settings):
    async with LifespanManager(integration_app):
        async with AsyncClient(
            transport=ASGITransport(app=integration_app),
            base_url=f"http://{integration_settings.SERVER_HOST}:{integration_settings.SERVER_PORT}",
        ) as ac:
            yield ac
