"""Testes unitários para os use cases do módulo Veículos."""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.veiculos.application.dtos.veiculo import (
    AtualizarVeiculo,
    CriarVeiculoRequest,
    VeiculoResponse,
)
from app.modules.veiculos.application.use_cases.atualizar_veiculo import AtualizarVeiculoUseCase
from app.modules.veiculos.application.use_cases.criar_veiculo import CriarVeiculoUseCase
from app.modules.veiculos.application.use_cases.listar_veiculos import ListarVeiculosUseCase
from app.modules.veiculos.application.use_cases.obter_veiculo_por_id import ObterVeiculoPorIdUseCase
from app.modules.veiculos.application.use_cases.obter_veiculo_por_placa import ObterVeiculoPorPlacaUseCase
from app.modules.veiculos.application.use_cases.remover_veiculo import RemoverVeiculoUseCase
from app.modules.veiculos.domain.entities.veiculo import Veiculo
from app.modules.veiculos.domain.exceptions import (
    PlacaJaCadastradaError,
    VeiculoInvalidoError,
    VeiculoNaoEncontradoError,
)
from app.modules.veiculos.domain.filters.veiculo import ListarVeiculosFiltro
from app.modules.veiculos.domain.value_objects.placa import Placa
from app.shared.value_objects.id import ID


# ---------------------------------------------------------------------------
# Helpers / builders
# ---------------------------------------------------------------------------

_CLIENTE_ID = str(uuid4())


def _veiculo_existente(**kwargs) -> Veiculo:
    defaults = dict(
        id=ID.generate(),
        cliente_id=uuid4(),
        placa=Placa("ABC1D23"),
        marca="Toyota",
        modelo="Corolla",
        ano_fabricacao=2020,
        ano_modelo=2021,
        cor="Prata",
        criado_em=datetime.now(UTC) - timedelta(days=1),
        atualizado_em=datetime.now(UTC) - timedelta(days=1),
    )
    defaults.update(kwargs)
    return Veiculo(**defaults)


def _criar_request(**kwargs) -> CriarVeiculoRequest:
    defaults = dict(
        cliente_id=_CLIENTE_ID,
        placa="ABC1D23",
        marca="Toyota",
        modelo="Corolla",
        ano_fabricacao=2020,
        ano_modelo=2021,
        cor="Prata",
    )
    defaults.update(kwargs)
    return CriarVeiculoRequest(**defaults)


def _cliente_ativo_mock():
    cliente = MagicMock()
    cliente.ativo = True
    return cliente


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_veiculo_repo():
    repo = MagicMock()
    repo.salvar = AsyncMock()
    repo.atualizar = AsyncMock(return_value=None)
    repo.remover = AsyncMock(return_value=True)
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.obter_por_placa = AsyncMock(return_value=None)
    repo.listar = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_cliente_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=_cliente_ativo_mock())
    return repo


@pytest.fixture
def mock_uow(mock_veiculo_repo):
    uow = MagicMock()
    uow.veiculo_repo = mock_veiculo_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


# ---------------------------------------------------------------------------
# CriarVeiculoUseCase
# ---------------------------------------------------------------------------

async def test_criar_veiculo_sucesso(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)
    resultado = await usecase.execute(_criar_request())

    assert isinstance(resultado, VeiculoResponse)
    assert resultado.placa == "ABC1D23"
    assert resultado.marca == "Toyota"
    mock_uow.veiculo_repo.salvar.assert_called_once()


async def test_criar_veiculo_placa_normalizada(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)
    resultado = await usecase.execute(_criar_request(placa="abc-1d23"))

    assert resultado.placa == "ABC1D23"


async def test_criar_veiculo_sem_campos_opcionais(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)
    resultado = await usecase.execute(
        _criar_request(ano_fabricacao=None, ano_modelo=None, cor=None)
    )

    assert resultado.ano_fabricacao is None
    assert resultado.ano_modelo is None
    assert resultado.cor is None


async def test_criar_veiculo_placa_invalida(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(VeiculoInvalidoError):
        await usecase.execute(_criar_request(placa="INVALIDA"))


async def test_criar_veiculo_placa_duplicada(mock_uow, mock_cliente_repo):
    mock_uow.veiculo_repo.obter_por_placa.return_value = _veiculo_existente()
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(PlacaJaCadastradaError):
        await usecase.execute(_criar_request())

    mock_uow.veiculo_repo.salvar.assert_not_called()


async def test_criar_veiculo_cliente_inexistente(mock_uow, mock_cliente_repo):
    mock_cliente_repo.obter_por_id.return_value = None
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(ClienteNaoEncontradoError):
        await usecase.execute(_criar_request())

    mock_uow.veiculo_repo.salvar.assert_not_called()


async def test_criar_veiculo_cliente_inativo(mock_uow, mock_cliente_repo):
    cliente_inativo = MagicMock()
    cliente_inativo.ativo = False
    mock_cliente_repo.obter_por_id.return_value = cliente_inativo
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(VeiculoInvalidoError, match="inativo"):
        await usecase.execute(_criar_request())

    mock_uow.veiculo_repo.salvar.assert_not_called()


async def test_criar_veiculo_cliente_id_invalido(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(VeiculoInvalidoError, match="cliente_id"):
        await usecase.execute(_criar_request(cliente_id="nao-eh-uuid"))


async def test_criar_veiculo_nao_chama_salvar_quando_placa_invalida(mock_uow, mock_cliente_repo):
    usecase = CriarVeiculoUseCase(uow=mock_uow, cliente_repo=mock_cliente_repo)

    with pytest.raises(VeiculoInvalidoError):
        await usecase.execute(_criar_request(placa="XYZ"))

    mock_uow.veiculo_repo.salvar.assert_not_called()


# ---------------------------------------------------------------------------
# ObterVeiculoPorIdUseCase
# ---------------------------------------------------------------------------

async def test_obter_veiculo_por_id_sucesso(mock_veiculo_repo):
    veiculo = _veiculo_existente()
    mock_veiculo_repo.obter_por_id.return_value = veiculo
    usecase = ObterVeiculoPorIdUseCase(veiculo_repo=mock_veiculo_repo)

    resultado = await usecase.execute(str(veiculo.id))

    assert isinstance(resultado, VeiculoResponse)
    assert resultado.id == str(veiculo.id)
    assert resultado.placa == veiculo.placa.value


async def test_obter_veiculo_por_id_nao_encontrado(mock_veiculo_repo):
    mock_veiculo_repo.obter_por_id.return_value = None
    usecase = ObterVeiculoPorIdUseCase(veiculo_repo=mock_veiculo_repo)

    with pytest.raises(VeiculoNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


# ---------------------------------------------------------------------------
# ObterVeiculoPorPlacaUseCase
# ---------------------------------------------------------------------------

async def test_obter_veiculo_por_placa_sucesso(mock_veiculo_repo):
    veiculo = _veiculo_existente()
    mock_veiculo_repo.obter_por_placa.return_value = veiculo
    usecase = ObterVeiculoPorPlacaUseCase(veiculo_repo=mock_veiculo_repo)

    resultado = await usecase.execute("ABC1D23")

    assert isinstance(resultado, VeiculoResponse)
    assert resultado.placa == "ABC1D23"


async def test_obter_veiculo_por_placa_normaliza_entrada(mock_veiculo_repo):
    veiculo = _veiculo_existente()
    mock_veiculo_repo.obter_por_placa.return_value = veiculo
    usecase = ObterVeiculoPorPlacaUseCase(veiculo_repo=mock_veiculo_repo)

    await usecase.execute("abc-1d23")

    mock_veiculo_repo.obter_por_placa.assert_called_once_with("ABC1D23")


async def test_obter_veiculo_por_placa_nao_encontrado(mock_veiculo_repo):
    mock_veiculo_repo.obter_por_placa.return_value = None
    usecase = ObterVeiculoPorPlacaUseCase(veiculo_repo=mock_veiculo_repo)

    with pytest.raises(VeiculoNaoEncontradoError):
        await usecase.execute("ABC1D23")


# ---------------------------------------------------------------------------
# ListarVeiculosUseCase
# ---------------------------------------------------------------------------

async def test_listar_veiculos_sem_filtros(mock_veiculo_repo):
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)
    filtros = ListarVeiculosFiltro()

    resultado = await usecase.execute(filtros)

    assert resultado == []
    mock_veiculo_repo.listar.assert_called_once_with(filtros)


async def test_listar_veiculos_retorna_lista(mock_veiculo_repo):
    veiculo = _veiculo_existente()
    mock_veiculo_repo.listar.return_value = [veiculo]
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)

    resultado = await usecase.execute(ListarVeiculosFiltro())

    assert len(resultado) == 1
    assert isinstance(resultado[0], VeiculoResponse)
    assert resultado[0].marca == "Toyota"


async def test_listar_veiculos_filtrar_por_cliente_id(mock_veiculo_repo):
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)
    cliente_id = uuid4()
    filtros = ListarVeiculosFiltro(cliente_id=cliente_id)

    await usecase.execute(filtros)

    mock_veiculo_repo.listar.assert_called_once_with(filtros)


async def test_listar_veiculos_filtrar_por_placa(mock_veiculo_repo):
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)
    filtros = ListarVeiculosFiltro(placa="ABC1D23")

    await usecase.execute(filtros)

    mock_veiculo_repo.listar.assert_called_once_with(filtros)


async def test_listar_veiculos_filtrar_por_marca(mock_veiculo_repo):
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)
    filtros = ListarVeiculosFiltro(marca="Toyota")

    await usecase.execute(filtros)

    mock_veiculo_repo.listar.assert_called_once_with(filtros)


async def test_listar_veiculos_filtrar_por_modelo(mock_veiculo_repo):
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)
    filtros = ListarVeiculosFiltro(modelo="Corolla")

    await usecase.execute(filtros)

    mock_veiculo_repo.listar.assert_called_once_with(filtros)


async def test_listar_veiculos_lista_vazia(mock_veiculo_repo):
    mock_veiculo_repo.listar.return_value = []
    usecase = ListarVeiculosUseCase(veiculo_repo=mock_veiculo_repo)

    resultado = await usecase.execute(ListarVeiculosFiltro())

    assert resultado == []


# ---------------------------------------------------------------------------
# AtualizarVeiculoUseCase
# ---------------------------------------------------------------------------

async def test_atualizar_veiculo_sucesso_marca(mock_uow):
    veiculo = _veiculo_existente()
    atualizado = _veiculo_existente(
        id=veiculo.id,
        cliente_id=veiculo.cliente_id,
        marca="Honda",
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.veiculo_repo.obter_por_id.return_value = veiculo
    mock_uow.veiculo_repo.atualizar.return_value = atualizado
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(veiculo.id), AtualizarVeiculo(marca="Honda"))

    assert isinstance(resultado, VeiculoResponse)
    assert resultado.marca == "Honda"
    mock_uow.veiculo_repo.atualizar.assert_called_once()


async def test_atualizar_veiculo_sucesso_cor(mock_uow):
    veiculo = _veiculo_existente()
    atualizado = _veiculo_existente(
        id=veiculo.id,
        cliente_id=veiculo.cliente_id,
        cor="Azul",
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.veiculo_repo.obter_por_id.return_value = veiculo
    mock_uow.veiculo_repo.atualizar.return_value = atualizado
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(veiculo.id), AtualizarVeiculo(cor="Azul"))

    assert resultado.cor == "Azul"


async def test_atualizar_veiculo_preserva_campos_nao_enviados(mock_uow):
    veiculo = _veiculo_existente(marca="Toyota", modelo="Corolla")
    atualizado = _veiculo_existente(
        id=veiculo.id,
        cliente_id=veiculo.cliente_id,
        marca="Toyota",
        modelo="Corolla",
        cor="Verde",
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.veiculo_repo.obter_por_id.return_value = veiculo
    mock_uow.veiculo_repo.atualizar.return_value = atualizado
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(veiculo.id), AtualizarVeiculo(cor="Verde"))

    assert resultado.marca == "Toyota"
    assert resultado.modelo == "Corolla"


async def test_atualizar_veiculo_nao_encontrado(mock_uow):
    mock_uow.veiculo_repo.obter_por_id.return_value = None
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    with pytest.raises(VeiculoNaoEncontradoError):
        await usecase.execute(str(ID.generate()), AtualizarVeiculo(marca="Honda"))


async def test_atualizar_veiculo_atualizar_retorna_none(mock_uow):
    veiculo = _veiculo_existente()
    mock_uow.veiculo_repo.obter_por_id.return_value = veiculo
    mock_uow.veiculo_repo.atualizar.return_value = None
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    with pytest.raises(VeiculoNaoEncontradoError):
        await usecase.execute(str(veiculo.id), AtualizarVeiculo(marca="Honda"))


async def test_atualizar_veiculo_dto_sem_campos_rejeitado():
    with pytest.raises(ValueError, match="Pelo menos um campo"):
        AtualizarVeiculo()


async def test_atualizar_veiculo_atualiza_atualizado_em(mock_uow):
    veiculo = _veiculo_existente(atualizado_em=datetime.now(UTC) - timedelta(days=1))
    atualizado = _veiculo_existente(
        id=veiculo.id,
        cliente_id=veiculo.cliente_id,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.veiculo_repo.obter_por_id.return_value = veiculo
    mock_uow.veiculo_repo.atualizar.return_value = atualizado
    usecase = AtualizarVeiculoUseCase(uow=mock_uow)

    await usecase.execute(str(veiculo.id), AtualizarVeiculo(marca="Honda"))

    # Verifica que atualizar foi chamado com atualizado_em diferente do original
    veiculo_passado = mock_uow.veiculo_repo.atualizar.call_args[0][0]
    assert isinstance(veiculo_passado.atualizado_em, datetime)
    assert veiculo_passado.atualizado_em > veiculo.atualizado_em


# ---------------------------------------------------------------------------
# RemoverVeiculoUseCase
# ---------------------------------------------------------------------------

async def test_remover_veiculo_sucesso(mock_uow):
    mock_uow.veiculo_repo.remover.return_value = True
    usecase = RemoverVeiculoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(ID.generate()))

    assert resultado is True
    mock_uow.veiculo_repo.remover.assert_called_once()


async def test_remover_veiculo_nao_encontrado_retorna_false(mock_uow):
    mock_uow.veiculo_repo.remover.return_value = False
    usecase = RemoverVeiculoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(ID.generate()))

    assert resultado is False
