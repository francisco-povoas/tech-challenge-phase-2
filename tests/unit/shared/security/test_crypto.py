import pytest

from app.shared.infra.security.crypto import Hasher


# --- Fixtures ---

@pytest.fixture
def hasher() -> Hasher:
    return Hasher()


# --- hash ---

def test_hash_retorna_string(hasher):
    resultado = hasher.hash("minha_senha")
    assert isinstance(resultado, str)


def test_hash_nao_retorna_senha_em_texto_claro(hasher):
    senha = "minha_senha"
    resultado = hasher.hash(senha)
    assert resultado != senha


def test_hash_gera_valores_diferentes_para_mesma_senha(hasher):
    """bcrypt usa salt aleatório — dois hashes da mesma senha devem diferir."""
    h1 = hasher.hash("mesma_senha")
    h2 = hasher.hash("mesma_senha")
    assert h1 != h2


def test_hash_resultado_inicia_com_prefixo_bcrypt(hasher):
    resultado = hasher.hash("qualquer_senha")
    assert resultado.startswith("$2b$") or resultado.startswith("$2a$")


# --- verify ---

def test_verify_senha_correta_retorna_true(hasher):
    senha = "senha_valida_123"
    hashed = hasher.hash(senha)
    assert hasher.verify(senha, hashed) is True


def test_verify_senha_errada_retorna_false(hasher):
    senha = "senha_valida_123"
    hashed = hasher.hash(senha)
    assert hasher.verify("senha_errada", hashed) is False


def test_verify_senha_vazia_contra_hash_valido_retorna_false(hasher):
    hashed = hasher.hash("senha_qualquer")
    assert hasher.verify("", hashed) is False


def test_verify_diferenca_maiusculas_retorna_false(hasher):
    senha = "SenhaComMaiusculas"
    hashed = hasher.hash(senha)
    assert hasher.verify("senhacommaiusculas", hashed) is False


def test_verify_senha_com_espacos(hasher):
    senha = "senha com espacos"
    hashed = hasher.hash(senha)
    assert hasher.verify(senha, hashed) is True
