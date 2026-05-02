import os
import uuid

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.main import create_app

_TEST_DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5437/app_test",
)

# Tabelas do seed inicial que NÃO devem ser truncadas
_IAM_SEED_TABLES = {"alembic_version", "usuario", "perfil", "usuario_perfil"}

# Perfis criados pelas migrations
_PERFIS_BASE = ("Administrador", "Atendente", "Mecanico")

# E-mail do admin criado pelo seed_admin.py
_ADMIN_EMAIL = "admin@example.com"


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def integration_settings():
    os.environ["DB_URL"] = _TEST_DB_URL
    os.environ["ENV"] = "test"
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def integration_app(integration_settings):
    return create_app(integration_settings)


@pytest_asyncio.fixture
async def client(integration_app):
    async with LifespanManager(integration_app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
        ) as ac:
            yield ac


@pytest_asyncio.fixture
async def admin_token(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": _ADMIN_EMAIL, "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, f"Falha ao autenticar admin: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def unique_email():
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


async def _reset_to_seed_state(db_url: str) -> None:
    """
    Restaura o banco ao estado pós-migration + seed_admin.py.

    1. Trunca todas as tabelas de domínio (fora do conjunto IAM/seed) com CASCADE.
    2. Remove vínculos usuario_perfil de usuários que não são o admin.
    3. Remove usuários que não são o admin.
    4. Remove perfis extras criados por testes.
    """
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            rows = await conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """))
            all_tables = [row[0] for row in rows]

            domain_tables = [
                f'"{t}"' for t in all_tables if t not in _IAM_SEED_TABLES
            ]
            if domain_tables:
                await conn.execute(text(
                    f"TRUNCATE TABLE {', '.join(domain_tables)} RESTART IDENTITY CASCADE"
                ))

            await conn.execute(text("""
                DELETE FROM usuario_perfil
                WHERE usuario_id IN (
                    SELECT id FROM usuario WHERE email <> :admin_email
                )
            """), {"admin_email": _ADMIN_EMAIL})

            await conn.execute(text("""
                DELETE FROM usuario WHERE email <> :admin_email
            """), {"admin_email": _ADMIN_EMAIL})

            perfis_placeholders = ", ".join(f":p{i}" for i in range(len(_PERFIS_BASE)))
            params = {f"p{i}": nome for i, nome in enumerate(_PERFIS_BASE)}
            await conn.execute(
                text(f"DELETE FROM perfil WHERE nome NOT IN ({perfis_placeholders})"),
                params,
            )
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def restore_database_each_test(integration_settings):
    """Garante estado seed antes e restaura após cada teste."""
    # print("[integration-test] reset database BEFORE test")
    await _reset_to_seed_state(integration_settings.DB_URL)

    yield

    # print("[integration-test] reset database to seed state AFTER test")
    await _reset_to_seed_state(integration_settings.DB_URL)
