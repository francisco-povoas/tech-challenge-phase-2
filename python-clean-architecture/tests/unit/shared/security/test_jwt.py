import time
from uuid import uuid4

import pytest

from app.shared.infra.security.jwt import InvalidToken, JWTProvider


# --- Fixtures ---

SECRET = "segredo-de-teste-super-secreto"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30


@pytest.fixture
def provider() -> JWTProvider:
    return JWTProvider(
        secret_key=SECRET,
        expire_minutes=EXPIRE_MINUTES,
        algorithm=ALGORITHM,
    )


@pytest.fixture
def usuario_id() -> str:
    return str(uuid4())


# --- create_access_token ---

def test_create_access_token_retorna_dict_com_chaves_esperadas(provider, usuario_id):
    resultado = provider.create_access_token({"sub": usuario_id, "perfis": ["Atendente"]})
    assert "access_token" in resultado
    assert "expire" in resultado
    assert "token_type" in resultado


def test_create_access_token_token_type_bearer(provider, usuario_id):
    resultado = provider.create_access_token({"sub": usuario_id})
    assert resultado["token_type"] == "bearer"


def test_create_access_token_expire_e_float(provider, usuario_id):
    resultado = provider.create_access_token({"sub": usuario_id})
    assert isinstance(resultado["expire"], float)


def test_create_access_token_expire_e_futuro(provider, usuario_id):
    resultado = provider.create_access_token({"sub": usuario_id})
    assert resultado["expire"] > time.time()


def test_create_access_token_access_token_e_string_nao_vazia(provider, usuario_id):
    resultado = provider.create_access_token({"sub": usuario_id})
    assert isinstance(resultado["access_token"], str)
    assert len(resultado["access_token"]) > 0


# --- decode ---

def test_decode_token_valido_retorna_payload(provider, usuario_id):
    token_data = provider.create_access_token({"sub": usuario_id, "perfis": ["Administrador"]})
    payload = provider.decode(token_data["access_token"])
    assert payload["sub"] == usuario_id
    assert payload["perfis"] == ["Administrador"]


def test_decode_token_invalido_lanca_invalid_token(provider):
    with pytest.raises(InvalidToken):
        provider.decode("token.invalido.aqui")


def test_decode_token_assinado_com_chave_errada_lanca_invalid_token(provider, usuario_id):
    outro_provider = JWTProvider(
        secret_key="outra-chave-diferente",
        expire_minutes=EXPIRE_MINUTES,
        algorithm=ALGORITHM,
    )
    token_data = outro_provider.create_access_token({"sub": usuario_id})
    with pytest.raises(InvalidToken):
        provider.decode(token_data["access_token"])


def test_decode_token_expirado_lanca_invalid_token(usuario_id):
    provider_expirado = JWTProvider(
        secret_key=SECRET,
        expire_minutes=-1,  # já expirado
        algorithm=ALGORITHM,
    )
    token_data = provider_expirado.create_access_token({"sub": usuario_id})
    with pytest.raises(InvalidToken):
        provider_expirado.decode(token_data["access_token"])


# --- get_sub ---

def test_get_sub_retorna_uuid_e_perfis(provider, usuario_id):
    token_data = provider.create_access_token({"sub": usuario_id, "perfis": ["Mecanico"]})
    sub, perfis = provider.get_sub(token_data["access_token"])
    assert sub == usuario_id
    assert perfis == ["Mecanico"]


def test_get_sub_sem_perfis_retorna_lista_vazia(provider, usuario_id):
    token_data = provider.create_access_token({"sub": usuario_id})
    sub, perfis = provider.get_sub(token_data["access_token"])
    assert sub == usuario_id
    assert perfis == []


def test_get_sub_formato_legado_user_id_prefixo(provider, usuario_id):
    """Compatibilidade com formato legado 'user_id:<uuid>'."""
    token_data = provider.create_access_token({"sub": f"user_id:{usuario_id}"})
    sub, _ = provider.get_sub(token_data["access_token"])
    assert sub == usuario_id


def test_get_sub_token_invalido_lanca_invalid_token(provider):
    with pytest.raises(InvalidToken):
        provider.get_sub("token.invalido")


def test_get_sub_sub_nao_uuid_lanca_invalid_token(provider):
    token_data = provider.create_access_token({"sub": "nao-e-um-uuid"})
    with pytest.raises(InvalidToken):
        provider.get_sub(token_data["access_token"])


def test_get_sub_sub_vazio_lanca_invalid_token(provider):
    token_data = provider.create_access_token({"sub": ""})
    with pytest.raises(InvalidToken):
        provider.get_sub(token_data["access_token"])
