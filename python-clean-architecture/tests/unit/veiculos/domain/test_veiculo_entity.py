"""Testes unitários para a entidade Veiculo."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.exceptions import VeiculoInvalidoError
from app.modules.veiculos.domain.value_objects.placa import Placa
from app.shared.value_objects.id import ID


# ---------------------------------------------------------------------------
# Fixture de apoio
# ---------------------------------------------------------------------------

def _veiculo_valido(**kwargs) -> Veiculo:
    defaults = dict(
        id=ID.generate(),
        cliente_id=uuid4(),
        placa=Placa("ABC1D23"),
        marca="Toyota",
        modelo="Corolla",
        ano_fabricacao=2020,
        ano_modelo=2021,
        cor="Prata",
        criado_em=datetime.now(UTC),
        atualizado_em=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Veiculo(**defaults)


# ---------------------------------------------------------------------------
# Criação válida
# ---------------------------------------------------------------------------

def test_veiculo_criado_com_sucesso():
    v = _veiculo_valido()
    assert v.marca == "Toyota"
    assert v.modelo == "Corolla"
    assert v.placa.value == "ABC1D23"


def test_veiculo_campos_opcionais_none():
    v = _veiculo_valido(ano_fabricacao=None, ano_modelo=None, cor=None)
    assert v.ano_fabricacao is None
    assert v.ano_modelo is None
    assert v.cor is None


def test_veiculo_placa_normalizada_na_criacao():
    v = _veiculo_valido(placa=Placa("abc-1d23"))
    assert v.placa.value == "ABC1D23"


# ---------------------------------------------------------------------------
# Validação de marca
# ---------------------------------------------------------------------------

def test_veiculo_marca_vazia_rejeitada():
    with pytest.raises(VeiculoInvalidoError, match="marca"):
        _veiculo_valido(marca="")


def test_veiculo_marca_so_espacos_rejeitada():
    with pytest.raises(VeiculoInvalidoError, match="marca"):
        _veiculo_valido(marca="   ")


def test_veiculo_marca_muito_longa_rejeitada():
    with pytest.raises(VeiculoInvalidoError, match="marca"):
        _veiculo_valido(marca="M" * 61)


# ---------------------------------------------------------------------------
# Validação de modelo
# ---------------------------------------------------------------------------

def test_veiculo_modelo_vazio_rejeitado():
    with pytest.raises(VeiculoInvalidoError, match="modelo"):
        _veiculo_valido(modelo="")


def test_veiculo_modelo_so_espacos_rejeitado():
    with pytest.raises(VeiculoInvalidoError, match="modelo"):
        _veiculo_valido(modelo="   ")


def test_veiculo_modelo_muito_longo_rejeitado():
    with pytest.raises(VeiculoInvalidoError, match="modelo"):
        _veiculo_valido(modelo="X" * 61)


# ---------------------------------------------------------------------------
# Validação de cor
# ---------------------------------------------------------------------------

def test_veiculo_cor_muito_longa_rejeitada():
    with pytest.raises(VeiculoInvalidoError, match="cor"):
        _veiculo_valido(cor="A" * 31)


def test_veiculo_cor_no_limite_aceita():
    v = _veiculo_valido(cor="A" * 30)
    assert v.cor == "A" * 30


# ---------------------------------------------------------------------------
# Validação de ano_fabricacao
# ---------------------------------------------------------------------------

def test_veiculo_ano_fabricacao_abaixo_minimo_rejeitado():
    with pytest.raises(VeiculoInvalidoError, match="fabricação"):
        _veiculo_valido(ano_fabricacao=1899)


def test_veiculo_ano_fabricacao_minimo_aceito():
    v = _veiculo_valido(ano_fabricacao=1900)
    assert v.ano_fabricacao == 1900


def test_veiculo_ano_fabricacao_none_aceito():
    v = _veiculo_valido(ano_fabricacao=None)
    assert v.ano_fabricacao is None


# ---------------------------------------------------------------------------
# Validação de ano_modelo
# ---------------------------------------------------------------------------

def test_veiculo_ano_modelo_abaixo_minimo_rejeitado():
    with pytest.raises(VeiculoInvalidoError, match="modelo"):
        _veiculo_valido(ano_modelo=1899)


def test_veiculo_ano_modelo_minimo_aceito():
    v = _veiculo_valido(ano_modelo=1900)
    assert v.ano_modelo == 1900


def test_veiculo_ano_modelo_none_aceito():
    v = _veiculo_valido(ano_modelo=None)
    assert v.ano_modelo is None
