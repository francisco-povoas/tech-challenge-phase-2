from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.clientes.application.dtos.cliente import (
    AtualizarCliente,
    ClienteResponse,
    CriarClienteRequest,
)
from app.modules.clientes.application.use_cases.ativar_cliente import AtivarClienteUseCase
from app.modules.clientes.application.use_cases.atualizar_cliente import AtualizarClienteUseCase
from app.modules.clientes.application.use_cases.criar_cliente import CriarClienteUseCase
from app.modules.clientes.application.use_cases.desativar_cliente import DesativarClienteUseCase
from app.modules.clientes.application.use_cases.listar_clientes import ListarClientesUseCase
from app.modules.clientes.application.use_cases.obter_cliente_por_cpf_cnpj import ObterClientePorCpfCnpjUseCase
from app.modules.clientes.application.use_cases.obter_cliente_por_id import ObterClientePorIdUseCase
from app.modules.clientes.application.use_cases.remover_cliente import RemoverClienteUseCase
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.exceptions import (
    ClienteInvalidoError,
    ClienteNaoEncontradoError,
    CpfCnpjJaCadastradoError,
)
from app.modules.clientes.domain.filters.cliente import ListarClientesFiltro
from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj
from app.modules.clientes.domain.value_objects.telefone import Telefone
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.salvar = AsyncMock()
    repo.atualizar = AsyncMock(return_value=None)
    repo.remover = AsyncMock(return_value=True)
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.obter_por_cpf_cnpj = AsyncMock(return_value=None)
    repo.listar = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_uow(mock_repo):
    uow = MagicMock()
    uow.cliente_repo = mock_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def cliente_pf():
    agora = datetime.now(UTC)
    return Cliente(
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
        criado_em=agora - timedelta(days=3),
        atualizado_em=agora - timedelta(days=1),
    )


@pytest.fixture
def cliente_pj():
    agora = datetime.now(UTC)
    return Cliente(
        id=ID.generate(),
        tipo_pessoa=TipoPessoa.PJ,
        nome_razao_social="Empresa LTDA",
        cpf_cnpj=CpfCnpj("12345678000199"),
        telefone=Telefone("1133334444"),
        email=None,
        cep=None,
        logradouro=None,
        numero=None,
        complemento=None,
        bairro=None,
        cidade=None,
        uf=None,
        ativo=True,
        criado_em=agora - timedelta(days=5),
        atualizado_em=agora - timedelta(days=2),
    )


# ---------------------------------------------------------------------------
# CriarClienteUseCase
# ---------------------------------------------------------------------------

async def test_criar_cliente_pf_sucesso(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="João Silva",
        cpf_cnpj="12345678901",
        telefone="11999998888",
        email="joao@example.com",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert isinstance(resultado, ClienteResponse)
    assert resultado.tipo_pessoa == "PF"
    assert resultado.cpf_cnpj == "12345678901"
    assert resultado.ativo is True
    mock_uow.cliente_repo.salvar.assert_called_once()


async def test_criar_cliente_pj_sucesso(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PJ",
        nome_razao_social="Empresa LTDA",
        cpf_cnpj="12345678000199",
        telefone="1133334444",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert resultado.tipo_pessoa == "PJ"
    assert resultado.cpf_cnpj == "12345678000199"
    assert resultado.email is None


async def test_criar_cliente_sem_email_aceita_none(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="Maria",
        cpf_cnpj="12345678901",
        telefone="11999998888",
        email=None,
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    resultado = await usecase.execute(dto)
    assert resultado.email is None


async def test_criar_cliente_tipo_pessoa_invalido(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="XX",
        nome_razao_social="Teste",
        cpf_cnpj="12345678901",
        telefone="11999998888",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    with pytest.raises(ClienteInvalidoError, match="Tipo de pessoa inválido"):
        await usecase.execute(dto)
    mock_uow.cliente_repo.salvar.assert_not_called()


async def test_criar_cliente_cpf_cnpj_invalido(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="Teste",
        cpf_cnpj="123",
        telefone="11999998888",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    with pytest.raises(ClienteInvalidoError):
        await usecase.execute(dto)
    mock_uow.cliente_repo.salvar.assert_not_called()


async def test_criar_cliente_telefone_invalido(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="Teste",
        cpf_cnpj="12345678901",
        telefone="",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    with pytest.raises(ClienteInvalidoError):
        await usecase.execute(dto)
    mock_uow.cliente_repo.salvar.assert_not_called()


async def test_criar_cliente_email_invalido(mock_uow):
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="Teste",
        cpf_cnpj="12345678901",
        telefone="11999998888",
        email="nao-e-um-email",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    with pytest.raises(ClienteInvalidoError):
        await usecase.execute(dto)
    mock_uow.cliente_repo.salvar.assert_not_called()


async def test_criar_cliente_cpf_cnpj_duplicado(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_cpf_cnpj.return_value = cliente_pf
    dto = CriarClienteRequest(
        tipo_pessoa="PF",
        nome_razao_social="Outro",
        cpf_cnpj="12345678901",
        telefone="11999998888",
    )
    usecase = CriarClienteUseCase(uow=mock_uow)
    with pytest.raises(CpfCnpjJaCadastradoError):
        await usecase.execute(dto)
    mock_uow.cliente_repo.salvar.assert_not_called()


# ---------------------------------------------------------------------------
# ObterClientePorIdUseCase
# ---------------------------------------------------------------------------

async def test_obter_cliente_por_id_sucesso(mock_repo, cliente_pf):
    mock_repo.obter_por_id.return_value = cliente_pf
    usecase = ObterClientePorIdUseCase(cliente_repo=mock_repo)

    resultado = await usecase.execute(str(cliente_pf.id))

    assert isinstance(resultado, ClienteResponse)
    assert resultado.id == str(cliente_pf.id)
    assert resultado.cpf_cnpj == "12345678901"


async def test_obter_cliente_por_id_nao_encontrado(mock_repo):
    mock_repo.obter_por_id.return_value = None
    usecase = ObterClientePorIdUseCase(cliente_repo=mock_repo)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


# ---------------------------------------------------------------------------
# ObterClientePorCpfCnpjUseCase
# ---------------------------------------------------------------------------

async def test_obter_cliente_por_cpf_cnpj_sucesso(mock_repo, cliente_pf):
    mock_repo.obter_por_cpf_cnpj.return_value = cliente_pf
    usecase = ObterClientePorCpfCnpjUseCase(cliente_repo=mock_repo)

    resultado = await usecase.execute("12345678901")

    assert isinstance(resultado, ClienteResponse)
    assert resultado.cpf_cnpj == "12345678901"


async def test_obter_cliente_por_cpf_cnpj_normaliza_mascara(mock_repo, cliente_pf):
    mock_repo.obter_por_cpf_cnpj.return_value = cliente_pf
    usecase = ObterClientePorCpfCnpjUseCase(cliente_repo=mock_repo)

    await usecase.execute("123.456.789-01")

    mock_repo.obter_por_cpf_cnpj.assert_called_once_with("12345678901")


async def test_obter_cliente_por_cpf_cnpj_nao_encontrado(mock_repo):
    mock_repo.obter_por_cpf_cnpj.return_value = None
    usecase = ObterClientePorCpfCnpjUseCase(cliente_repo=mock_repo)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute("12345678901")


# ---------------------------------------------------------------------------
# ListarClientesUseCase
# ---------------------------------------------------------------------------

async def test_listar_clientes_sem_filtros(mock_repo, cliente_pf):
    mock_repo.listar.return_value = [cliente_pf]
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    resultado = await usecase.execute(ListarClientesFiltro())

    assert len(resultado) == 1
    assert isinstance(resultado[0], ClienteResponse)
    mock_repo.listar.assert_called_once_with(ListarClientesFiltro())


async def test_listar_clientes_filtrar_por_nome(mock_repo, cliente_pf):
    mock_repo.listar.return_value = [cliente_pf]
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    filtros = ListarClientesFiltro(nome="João")
    resultado = await usecase.execute(filtros)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtros)


async def test_listar_clientes_filtrar_por_cpf_cnpj(mock_repo, cliente_pf):
    mock_repo.listar.return_value = [cliente_pf]
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    filtros = ListarClientesFiltro(cpf_cnpj="12345678901")
    resultado = await usecase.execute(filtros)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtros)


async def test_listar_clientes_filtrar_por_ativo(mock_repo, cliente_pf):
    mock_repo.listar.return_value = [cliente_pf]
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    filtros = ListarClientesFiltro(ativo=True)
    resultado = await usecase.execute(filtros)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtros)


async def test_listar_clientes_retorna_lista_vazia(mock_repo):
    mock_repo.listar.return_value = []
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    resultado = await usecase.execute(ListarClientesFiltro())

    assert resultado == []


async def test_listar_clientes_sem_email_retorna_none(mock_repo, cliente_pj):
    mock_repo.listar.return_value = [cliente_pj]
    usecase = ListarClientesUseCase(cliente_repo=mock_repo)

    resultado = await usecase.execute(ListarClientesFiltro())

    assert resultado[0].email is None


# ---------------------------------------------------------------------------
# AtualizarClienteUseCase
# ---------------------------------------------------------------------------

async def test_atualizar_cliente_sucesso_nome(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    cliente_atualizado = Cliente(
        id=cliente_pf.id,
        tipo_pessoa=cliente_pf.tipo_pessoa,
        nome_razao_social="João Atualizado",
        cpf_cnpj=cliente_pf.cpf_cnpj,
        telefone=cliente_pf.telefone,
        email=cliente_pf.email,
        cep=None, logradouro=None, numero=None, complemento=None,
        bairro=None, cidade=None, uf=None,
        ativo=True,
        criado_em=cliente_pf.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=cliente_atualizado)
    dto = AtualizarCliente(nome_razao_social="João Atualizado")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(cliente_pf.id), dto)

    assert isinstance(resultado, ClienteResponse)
    assert resultado.nome_razao_social == "João Atualizado"
    mock_uow.cliente_repo.atualizar.assert_called_once()


async def test_atualizar_cliente_sucesso_telefone(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    cliente_atualizado = Cliente(
        id=cliente_pf.id,
        tipo_pessoa=cliente_pf.tipo_pessoa,
        nome_razao_social=cliente_pf.nome_razao_social,
        cpf_cnpj=cliente_pf.cpf_cnpj,
        telefone=Telefone("11888887777"),
        email=cliente_pf.email,
        cep=None, logradouro=None, numero=None, complemento=None,
        bairro=None, cidade=None, uf=None,
        ativo=True,
        criado_em=cliente_pf.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=cliente_atualizado)
    dto = AtualizarCliente(telefone="11888887777")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(cliente_pf.id), dto)

    assert resultado.telefone == "11888887777"


async def test_atualizar_cliente_nao_encontrado(mock_uow):
    mock_uow.cliente_repo.obter_por_id.return_value = None
    dto = AtualizarCliente(nome_razao_social="Qualquer")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(ID.generate()), dto)


async def test_atualizar_cliente_retorna_none_lanca_erro(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=None)
    dto = AtualizarCliente(nome_razao_social="Teste")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(cliente_pf.id), dto)


async def test_atualizar_cliente_telefone_invalido(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    dto = AtualizarCliente(telefone="")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteInvalidoError):
        await usecase.execute(str(cliente_pf.id), dto)


async def test_atualizar_cliente_email_invalido(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    dto = AtualizarCliente(email="nao-e-email")
    usecase = AtualizarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteInvalidoError):
        await usecase.execute(str(cliente_pf.id), dto)


# ---------------------------------------------------------------------------
# AtivarClienteUseCase
# ---------------------------------------------------------------------------

async def test_ativar_cliente_sucesso(mock_uow, cliente_pf):
    cliente_inativo = Cliente(
        id=cliente_pf.id,
        tipo_pessoa=cliente_pf.tipo_pessoa,
        nome_razao_social=cliente_pf.nome_razao_social,
        cpf_cnpj=cliente_pf.cpf_cnpj,
        telefone=cliente_pf.telefone,
        email=cliente_pf.email,
        cep=None, logradouro=None, numero=None, complemento=None,
        bairro=None, cidade=None, uf=None,
        ativo=False,
        criado_em=cliente_pf.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    cliente_reativado = Cliente(
        id=cliente_pf.id,
        tipo_pessoa=cliente_pf.tipo_pessoa,
        nome_razao_social=cliente_pf.nome_razao_social,
        cpf_cnpj=cliente_pf.cpf_cnpj,
        telefone=cliente_pf.telefone,
        email=cliente_pf.email,
        cep=None, logradouro=None, numero=None, complemento=None,
        bairro=None, cidade=None, uf=None,
        ativo=True,
        criado_em=cliente_pf.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_inativo
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=cliente_reativado)
    usecase = AtivarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(cliente_pf.id))

    assert resultado.ativo is True


async def test_ativar_cliente_nao_encontrado(mock_uow):
    mock_uow.cliente_repo.obter_por_id.return_value = None
    usecase = AtivarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_ativar_cliente_atualizar_retorna_none(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=None)
    usecase = AtivarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(cliente_pf.id))


# ---------------------------------------------------------------------------
# DesativarClienteUseCase
# ---------------------------------------------------------------------------

async def test_desativar_cliente_sucesso(mock_uow, cliente_pf):
    cliente_desativado = Cliente(
        id=cliente_pf.id,
        tipo_pessoa=cliente_pf.tipo_pessoa,
        nome_razao_social=cliente_pf.nome_razao_social,
        cpf_cnpj=cliente_pf.cpf_cnpj,
        telefone=cliente_pf.telefone,
        email=cliente_pf.email,
        cep=None, logradouro=None, numero=None, complemento=None,
        bairro=None, cidade=None, uf=None,
        ativo=False,
        criado_em=cliente_pf.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=cliente_desativado)
    usecase = DesativarClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(cliente_pf.id))

    assert resultado.ativo is False


async def test_desativar_cliente_nao_encontrado(mock_uow):
    mock_uow.cliente_repo.obter_por_id.return_value = None
    usecase = DesativarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_desativar_cliente_atualizar_retorna_none(mock_uow, cliente_pf):
    mock_uow.cliente_repo.obter_por_id.return_value = cliente_pf
    mock_uow.cliente_repo.atualizar = AsyncMock(return_value=None)
    usecase = DesativarClienteUseCase(uow=mock_uow)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(str(cliente_pf.id))


# ---------------------------------------------------------------------------
# RemoverClienteUseCase
# ---------------------------------------------------------------------------

async def test_remover_cliente_sucesso(mock_uow):
    mock_uow.cliente_repo.remover.return_value = True
    usecase = RemoverClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(ID.generate()))

    assert resultado is True
    mock_uow.cliente_repo.remover.assert_called_once()


async def test_remover_cliente_nao_encontrado_retorna_false(mock_uow):
    mock_uow.cliente_repo.remover.return_value = False
    usecase = RemoverClienteUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(ID.generate()))

    assert resultado is False


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

def test_dto_atualizar_cliente_sem_campos_lanca_erro():
    with pytest.raises(ValueError):
        AtualizarCliente()
