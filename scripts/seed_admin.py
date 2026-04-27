"""
Seed script: cria o primeiro usuário administrador do sistema se ainda não existir.

Uso:
    python scripts/seed_admin.py

Variáveis de ambiente necessárias:
    DB_URL          - URL de conexão com o banco de dados
    ADMIN_NOME      - Nome do usuário administrador (padrão: Administrador)
    ADMIN_EMAIL     - E-mail do administrador (padrão: admin@example.com)
    ADMIN_PASSWORD  - Senha do administrador (obrigatória)

Comportamento idempotente: pode ser executado várias vezes sem duplicar o admin.
"""

import asyncio
import os
import sys
from datetime import UTC, datetime

# Garante que o diretório raiz do projeto esteja no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select

from app.modules.iam.domain.entities.perfil import PerfilTipos
from app.modules.iam.infrastructure.db.models.perfil import PerfilModel
from app.modules.iam.infrastructure.db.models.usuario import UsuarioModel
from app.modules.iam.infrastructure.db.models.usuario_perfil import UsuarioPerfilModel
from app.shared.infra.db import get_session_factory
from app.shared.infra.security.crypto import Hasher
from app.shared.value_objects.id import ID


async def seed_admin() -> None:
    admin_nome = os.environ.get("ADMIN_NOME", "Administrador")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")

    if not admin_password:
        print("[seed_admin] ERRO: variável de ambiente ADMIN_PASSWORD não definida.")
        sys.exit(1)

    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # 1. Busca o perfil ADMINISTRADOR
            result = await session.exec(
                select(PerfilModel).where(PerfilModel.nome == PerfilTipos.ADMINISTRADOR.value)
            )
            perfil = result.first()

            if perfil is None:
                print(
                    "[seed_admin] ERRO: Perfil ADMINISTRADOR não encontrado no banco. "
                    "Execute as migrations primeiro (alembic upgrade head)."
                )
                sys.exit(1)

            # 2. Verifica se já existe usuário ativo com perfil administrador
            result = await session.exec(
                select(UsuarioModel)
                .join(UsuarioPerfilModel, UsuarioPerfilModel.usuario_id == UsuarioModel.id)
                .where(UsuarioPerfilModel.perfil_id == perfil.id)
                .where(UsuarioModel.ativo == True)  # noqa: E712
            )
            admin_existente = result.first()

            if admin_existente is not None:
                print("[seed_admin] Admin já existe. Nenhuma alteração realizada.")
                return

            # 3. Cria o usuário administrador
            now = datetime.now(UTC)
            hasher = Hasher()
            senha_hash = hasher.hash(admin_password)

            novo_usuario = UsuarioModel(
                id=ID.generate().value,
                nome=admin_nome,
                email=admin_email,
                senha_hash=senha_hash,
                ativo=True,
                criado_em=now,
                atualizado_em=now,
            )
            session.add(novo_usuario)
            await session.flush()  # obtém o ID antes do commit

            # 4. Cria a relação usuario_perfil
            usuario_perfil = UsuarioPerfilModel(
                id=ID.generate().value,
                usuario_id=novo_usuario.id,
                perfil_id=perfil.id,
                criado_em=now,
            )
            session.add(usuario_perfil)

            await session.commit()
            print(f"[seed_admin] Admin criado com sucesso. E-mail: {admin_email}")

        except Exception as exc:
            await session.rollback()
            print(f"[seed_admin] ERRO ao criar admin: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_admin())
