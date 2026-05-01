from datetime import UTC, datetime

import pytest

from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.exceptions import ClienteInvalidoError
from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj
from app.modules.clientes.domain.value_objects.telefone import Telefone
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID


# --- Helpers ---

def _make_cliente(**kwargs) -> Cliente:
    defaults = dict(
        id=ID.generate(),
        tipo_pessoa=TipoPessoa.PF,
        nome_razao_social="João Silva",
        cpf_cnpj=CpfCnpj("12345678901"),
        telefone=Telefone("11999998888"),
        email=Email("joao@example.com"),
        cep=None,
        logradouro=None,
        numero=None,
        complemento=None,
        bairro=None,
        cidade=None,
        uf=None,
        ativo=True,
        criado_em=datetime.now(UTC),
        atualizado_em=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Cliente(**defaults)


# --- Criação válida ---

def test_cliente_pf_criado_com_sucesso():
    cliente = _make_cliente()
    assert cliente.tipo_pessoa == TipoPessoa.PF
    assert cliente.cpf_cnpj.value == "12345678901"
    assert cliente.ativo is True


def test_cliente_pj_criado_com_sucesso():
    cliente = _make_cliente(
        tipo_pessoa=TipoPessoa.PJ,
        cpf_cnpj=CpfCnpj("12345678000199"),
    )
    assert cliente.tipo_pessoa == TipoPessoa.PJ
    assert len(cliente.cpf_cnpj.value) == 14


def test_cliente_sem_email_aceita_none():
    cliente = _make_cliente(email=None)
    assert cliente.email is None


def test_cliente_campos_endereco_opcionais_none():
    cliente = _make_cliente(
        cep=None, logradouro=None, numero=None,
        complemento=None, bairro=None, cidade=None, uf=None,
    )
    assert cliente.cep is None
    assert cliente.logradouro is None


def test_cliente_com_endereco_completo():
    cliente = _make_cliente(
        cep="01310100",
        logradouro="Avenida Paulista",
        numero="1000",
        complemento="Apto 42",
        bairro="Bela Vista",
        cidade="São Paulo",
        uf="SP",
    )
    assert cliente.cidade == "São Paulo"
    assert cliente.uf == "SP"


# --- Validações __post_init__ ---

def test_cliente_nome_vazio_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="nome/razão social"):
        _make_cliente(nome_razao_social="")


def test_cliente_nome_espacos_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="nome/razão social"):
        _make_cliente(nome_razao_social="   ")


def test_cliente_pf_com_cnpj_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="CPF deve conter exatamente 11"):
        _make_cliente(
            tipo_pessoa=TipoPessoa.PF,
            cpf_cnpj=CpfCnpj("12345678000199"),  # CNPJ com 14 dígitos
        )


def test_cliente_pj_com_cpf_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="CNPJ deve conter exatamente 14"):
        _make_cliente(
            tipo_pessoa=TipoPessoa.PJ,
            cpf_cnpj=CpfCnpj("12345678901"),  # CPF com 11 dígitos
        )


def test_cliente_uf_tamanho_invalido_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="UF deve ter exatamente 2"):
        _make_cliente(uf="SPP")


def test_cliente_cep_tamanho_invalido_lanca_erro():
    with pytest.raises(ClienteInvalidoError, match="CEP deve ter exatamente 8"):
        _make_cliente(cep="0131010")
