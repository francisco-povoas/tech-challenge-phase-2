import pytest

from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj, CpfCnpjInvalidoError
from app.modules.clientes.domain.value_objects.telefone import Telefone, TelefoneInvalidoError
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa, TipoPessoaInvalidoError


# --- TipoPessoa ---

def test_tipo_pessoa_pf():
    assert TipoPessoa("PF") == TipoPessoa.PF


def test_tipo_pessoa_pj():
    assert TipoPessoa("PJ") == TipoPessoa.PJ


def test_tipo_pessoa_tipos_retorna_lista():
    tipos = TipoPessoa.tipos()
    assert "PF" in tipos
    assert "PJ" in tipos


def test_tipo_pessoa_invalido_lanca_erro():
    with pytest.raises(ValueError):
        TipoPessoa("INVALIDO")


# --- CpfCnpj ---

def test_cpf_valido_11_digitos():
    cpf = CpfCnpj("12345678901")
    assert cpf.value == "12345678901"
    assert len(cpf.value) == 11


def test_cnpj_valido_14_digitos():
    cnpj = CpfCnpj("12345678000199")
    assert cnpj.value == "12345678000199"
    assert len(cnpj.value) == 14


def test_cpf_com_mascara_normalizado():
    cpf = CpfCnpj("123.456.789-01")
    assert cpf.value == "12345678901"


def test_cnpj_com_mascara_normalizado():
    cnpj = CpfCnpj("12.345.678/0001-99")
    assert cnpj.value == "12345678000199"


def test_cpf_cnpj_tamanho_invalido_lanca_erro():
    with pytest.raises(CpfCnpjInvalidoError):
        CpfCnpj("12345")


def test_cpf_cnpj_vazio_lanca_erro():
    with pytest.raises(CpfCnpjInvalidoError):
        CpfCnpj("")


def test_cpf_cnpj_12_digitos_lanca_erro():
    with pytest.raises(CpfCnpjInvalidoError):
        CpfCnpj("123456789012")


def test_cpf_cnpj_so_letras_lanca_erro():
    with pytest.raises(CpfCnpjInvalidoError):
        CpfCnpj("abcdefghijk")


# --- Telefone ---

def test_telefone_valido():
    tel = Telefone("11999998888")
    assert tel.value == "11999998888"


def test_telefone_com_mascara_normalizado():
    tel = Telefone("(11) 99999-8888")
    assert tel.value == "11999998888"


def test_telefone_com_espacos_normalizado():
    tel = Telefone("11 9 9999 8888")
    assert tel.value == "11999998888"


def test_telefone_vazio_lanca_erro():
    with pytest.raises(TelefoneInvalidoError):
        Telefone("")


def test_telefone_so_caracteres_especiais_lanca_erro():
    with pytest.raises(TelefoneInvalidoError):
        Telefone("(-)  -")
