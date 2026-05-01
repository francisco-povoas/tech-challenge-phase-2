import pytest

from app.shared.value_objects.id import ID, InvalidIDError
from app.shared.value_objects.password import Password, InvalidPasswordError
from app.shared.value_objects.email import Email, InvalidEmailError


# --- Email ---

def test_email_valido():
    email = Email("test@example.com")
    assert email.value == "test@example.com"


@pytest.mark.parametrize("email_invalido", [
    "invalid", "@", "@.com", "bla.com", "@bla.com", "test@", "",
])
def test_email_invalido_lanca_erro(email_invalido):
    with pytest.raises(InvalidEmailError):
        Email(email_invalido)


def test_email_formatos_validos():
    validos = [
        "user@example.com",
        "test.email@domain.co.uk",
        "user123@test-domain.org",
        "user+tag@example.com",
        "user_name@example.com",
    ]
    for e in validos:
        assert Email(e).value == e


# --- Password ---

def test_senha_muito_curta_lanca_erro():
    with pytest.raises(InvalidPasswordError):
        Password("abc")


def test_senha_muito_longa_lanca_erro():
    with pytest.raises(InvalidPasswordError):
        Password("p" * 101)


def test_senha_valida():
    pwd = Password("senha1234")
    assert pwd.value == "senha1234"


# --- ID ---

def test_id_gerado_e_unico():
    id1 = ID.generate()
    id2 = ID.generate()
    assert id1 != id2


def test_id_from_string_valido():
    original = ID.generate()
    recuperado = ID.from_string(str(original))
    assert original == recuperado



# --- ID:

def test_id_from_string_invalido_lanca_invalid_id_error():
    with pytest.raises(InvalidIDError):
        ID.from_string("isso-nao-e-uuid")


def test_id_from_string_string_vazia_lanca_invalid_id_error():
    with pytest.raises(InvalidIDError):
        ID.from_string("")


def test_id_from_string_nao_aceita_none():
    with pytest.raises((InvalidIDError, TypeError)):
        ID.from_string(None)  # type: ignore


def test_id_str_retorna_representacao_uuid():
    id_obj = ID.generate()
    assert str(id_obj) == str(id_obj.value)


def test_id_igualdade_mesmo_valor():
    from uuid import UUID
    uuid_val = UUID("12345678-1234-5678-1234-567812345678")
    assert ID(uuid_val) == ID(uuid_val)


def test_id_desigualdade_valores_diferentes():
    assert ID.generate() != ID.generate()


# --- Password: limites exatos não cobertos pelo arquivo existente ---

def test_password_exatamente_8_caracteres_aceita():
    pwd = Password("12345678")
    assert len(pwd.value) == 8


def test_password_exatamente_100_caracteres_aceita():
    pwd = Password("p" * 100)
    assert len(pwd.value) == 100


def test_password_7_caracteres_lanca_erro():
    with pytest.raises(InvalidPasswordError):
        Password("1234567")


def test_password_101_caracteres_lanca_erro():
    with pytest.raises(InvalidPasswordError):
        Password("p" * 101)


def test_password_value_preserva_valor_original():
    senha = "minha_senha_valida"
    assert Password(senha).value == senha
