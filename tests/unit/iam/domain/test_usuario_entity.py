import pytest
from datetime import datetime, UTC, timedelta
from app.modules.iam.domain.entities.usuario import Usuario, InvalidUsuarioError
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.shared.value_objects.password import Password, InvalidPasswordError


@pytest.fixture
def dados_validos():
    return {
        "nome": "João Silva",
        "email": Email("joao@example.com"),
        "senha": Password("senha1234"),
        "criado_em": datetime.now(UTC) - timedelta(days=3),
        "atualizado_em": datetime.now(UTC) - timedelta(days=1),
        "ativo": True,
    }

def test_usuario_ids_unicos(dados_validos):
    u1 = Usuario(**dados_validos, id=ID.generate())
    u2 = Usuario(**dados_validos, id=ID.generate())
    assert u1.id != u2.id


def test_usuario_nome_vazio_lanca_erro(dados_validos):
    dados_validos["nome"] = "   "
    with pytest.raises(InvalidUsuarioError):
        Usuario(**dados_validos, id=ID.generate())


def test_usuario_nome_none_lanca_erro(dados_validos):
    dados_validos["nome"] = ""
    with pytest.raises(InvalidUsuarioError):
        Usuario(**dados_validos, id=ID.generate())
