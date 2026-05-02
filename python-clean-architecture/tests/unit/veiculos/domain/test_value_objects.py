"""Testes unitários para value objects do módulo Veículos."""
import pytest

from app.modules.veiculos.domain.value_objects.placa import Placa, PlacaInvalidaError


# ---------------------------------------------------------------------------
# Placa — formato antigo (ABC1234)
# ---------------------------------------------------------------------------

def test_placa_formato_antigo_valido():
    placa = Placa("ABC1234")
    assert placa.value == "ABC1234"


def test_placa_formato_antigo_minusculo_normalizado():
    placa = Placa("abc1234")
    assert placa.value == "ABC1234"


def test_placa_formato_antigo_com_hifen_normalizado():
    placa = Placa("ABC-1234")
    assert placa.value == "ABC1234"


def test_placa_formato_antigo_com_espaco_normalizado():
    placa = Placa("ABC 1234")
    assert placa.value == "ABC1234"


# ---------------------------------------------------------------------------
# Placa — formato Mercosul (ABC1D23)
# ---------------------------------------------------------------------------

def test_placa_mercosul_valido():
    placa = Placa("ABC1D23")
    assert placa.value == "ABC1D23"


def test_placa_mercosul_minusculo_normalizado():
    placa = Placa("abc1d23")
    assert placa.value == "ABC1D23"


def test_placa_mercosul_com_hifen_normalizado():
    placa = Placa("ABC-1D23")
    assert placa.value == "ABC1D23"


# ---------------------------------------------------------------------------
# Placa — rejeições
# ---------------------------------------------------------------------------

def test_placa_vazia_rejeitada():
    with pytest.raises(PlacaInvalidaError, match="não pode ser vazia"):
        Placa("")


def test_placa_so_espacos_rejeitada():
    with pytest.raises(PlacaInvalidaError, match="não pode ser vazia"):
        Placa("   ")


def test_placa_so_hifen_rejeitada():
    with pytest.raises(PlacaInvalidaError):
        Placa("---")


def test_placa_tamanho_curto_rejeitado():
    with pytest.raises(PlacaInvalidaError):
        Placa("ABC123")


def test_placa_tamanho_longo_rejeitado():
    with pytest.raises(PlacaInvalidaError):
        Placa("ABC12345")


def test_placa_formato_invalido_apenas_letras():
    with pytest.raises(PlacaInvalidaError):
        Placa("ABCDEFG")


def test_placa_formato_invalido_apenas_numeros():
    with pytest.raises(PlacaInvalidaError):
        Placa("1234567")


def test_placa_com_caractere_especial_rejeitada():
    with pytest.raises(PlacaInvalidaError):
        Placa("ABC@234")
