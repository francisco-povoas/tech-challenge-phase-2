import pytest

from app.shared.value_objects.email import Email, InvalidEmailError
from app.shared.value_objects.password import Password, InvalidPasswordError
from app.shared.value_objects.id import ID


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
