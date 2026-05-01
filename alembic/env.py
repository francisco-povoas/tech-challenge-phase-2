from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from app.config import get_settings

# Importa modelos para registrar tabelas no metadata
from app.modules.iam.infrastructure.db.models.usuario import UsuarioModel  # noqa: F401
from app.modules.iam.infrastructure.db.models.perfil import PerfilModel  # noqa: F401
from app.modules.iam.infrastructure.db.models.usuario_perfil import UsuarioPerfilModel  # noqa: F401
from app.modules.clientes.infrastructure.db.models.cliente import ClienteModel  # noqa: F401
from app.modules.veiculos.infrastructure.db.models.veiculo import VeiculoModel  # noqa: F401
from app.modules.servicos.infrastructure.db.models.servico import ServicoModel  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Garante que a URL usada pelo Alembic vem do ambiente ativo (dev/test/prod)
config.set_main_option("sqlalchemy.url", get_settings().DB_URL)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
