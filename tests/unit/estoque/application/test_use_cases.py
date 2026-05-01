from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.estoque.application.dtos.item_estoque import (
    AtualizarItemEstoque,
    CriarItemEstoqueRequest,
    ItemEstoqueResponse,
)
from app.modules.estoque.application.use_cases.ativar_item_estoque import AtivarItemEstoqueUseCase
from app.modules.estoque.application.use_cases.atualizar_item_estoque import AtualizarItemEstoqueUseCase
from app.modules.estoque.application.use_cases.criar_item_estoque import CriarItemEstoqueUseCase
from app.modules.estoque.application.use_cases.desativar_item_estoque import DesativarItemEstoqueUseCase
from app.modules.estoque.application.use_cases.listar_itens_estoque import ListarItensEstoqueUseCase
from app.modules.estoque.application.use_cases.obter_item_estoque_por_id import ObterItemEstoquePorIdUseCase
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque, TipoItemEstoque
from app.modules.estoque.domain.exceptions import (
    CodigoItemEstoqueJaCadastradoError,
    ItemEstoqueInvalidoError,
    ItemEstoqueNaoEncontradoError,
)
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro
from app.shared.value_objects.id import ID


# --- Helper ---

def _item_fake(nome="Filtro de óleo", ativo=True, codigo="FO-001") -> ItemEstoque:
    agora = datetime.now(UTC)
    return ItemEstoque(
        id=ID.generate(),
        tipo=TipoItemEstoque.PECA,
        nome=nome,
        descricao="Descrição do item",
        codigo=codigo,
        quantidade_disponivel=10,
        quantidade_reservada=0,
        quantidade_minima=2,
        valor_unitario=Decimal("35.00"),
        ativo=ativo,
        criado_em=agora,
        atualizado_em=agora,
    )


# --- Fixtures ---

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.obter_por_codigo = AsyncMock(return_value=None)
    repo.listar = AsyncMock(return_value=[])
    repo.salvar = AsyncMock()
    repo.atualizar = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_uow(mock_repo):
    uow = MagicMock()
    uow.item_estoque_repo = mock_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def item_existente() -> ItemEstoque:
    return _item_fake()


# ============================================================
# CriarItemEstoqueUseCase
# ============================================================

async def test_criar_item_estoque_sucesso(mock_uow):
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="Vela de ignição",
        descricao="Vela NGK",
        codigo="VG-001",
        quantidade_disponivel=5,
        quantidade_minima=1,
        valor_unitario=Decimal("22.50"),
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert isinstance(resultado, ItemEstoqueResponse)
    assert resultado.nome == "Vela de ignição"
    assert resultado.tipo == TipoItemEstoque.PECA.value
    assert resultado.ativo is True
    assert resultado.quantidade_reservada == 0
    mock_uow.item_estoque_repo.salvar.assert_called_once()


async def test_criar_item_estoque_insumo_sucesso(mock_uow):
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.INSUMO,
        nome="Óleo 5W30",
        valor_unitario=Decimal("45.00"),
        quantidade_disponivel=20,
        quantidade_minima=5,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert resultado.tipo == TipoItemEstoque.INSUMO.value
    mock_uow.item_estoque_repo.salvar.assert_called_once()


async def test_criar_item_sem_codigo_nao_verifica_duplicidade(mock_uow):
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="Item sem código",
        codigo=None,
        valor_unitario=Decimal("10.00"),
        quantidade_disponivel=3,
        quantidade_minima=1,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert resultado.codigo is None
    mock_uow.item_estoque_repo.obter_por_codigo.assert_not_called()
    mock_uow.item_estoque_repo.salvar.assert_called_once()


async def test_criar_item_codigo_duplicado_lanca_erro(mock_uow, item_existente):
    mock_uow.item_estoque_repo.obter_por_codigo.return_value = item_existente
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="Outro item",
        codigo=item_existente.codigo,
        valor_unitario=Decimal("50.00"),
        quantidade_disponivel=1,
        quantidade_minima=0,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(CodigoItemEstoqueJaCadastradoError):
        await usecase.execute(dto)

    mock_uow.item_estoque_repo.salvar.assert_not_called()


async def test_criar_item_invalido_nao_salva(mock_uow):
    """Nome vazio deve levantar ItemEstoqueInvalidoError antes de salvar."""
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="",
        valor_unitario=Decimal("10.00"),
        quantidade_disponivel=1,
        quantidade_minima=0,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueInvalidoError):
        await usecase.execute(dto)

    mock_uow.item_estoque_repo.salvar.assert_not_called()


async def test_criar_item_valor_negativo_nao_salva(mock_uow):
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="Item válido",
        valor_unitario=Decimal("-1.00"),
        quantidade_disponivel=1,
        quantidade_minima=0,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueInvalidoError):
        await usecase.execute(dto)

    mock_uow.item_estoque_repo.salvar.assert_not_called()


async def test_criar_item_quantidade_negativa_nao_salva(mock_uow):
    dto = CriarItemEstoqueRequest(
        tipo=TipoItemEstoque.PECA,
        nome="Item válido",
        valor_unitario=Decimal("10.00"),
        quantidade_disponivel=-1,
        quantidade_minima=0,
    )
    usecase = CriarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueInvalidoError):
        await usecase.execute(dto)

    mock_uow.item_estoque_repo.salvar.assert_not_called()


# ============================================================
# ObterItemEstoquePorIdUseCase
# ============================================================

async def test_obter_item_por_id_sucesso(mock_repo, item_existente):
    mock_repo.obter_por_id.return_value = item_existente
    usecase = ObterItemEstoquePorIdUseCase(item_estoque_repo=mock_repo)

    resultado = await usecase.execute(str(item_existente.id))

    assert isinstance(resultado, ItemEstoqueResponse)
    assert resultado.id == str(item_existente.id)
    assert resultado.nome == item_existente.nome


async def test_obter_item_por_id_nao_encontrado(mock_repo):
    mock_repo.obter_por_id.return_value = None
    usecase = ObterItemEstoquePorIdUseCase(item_estoque_repo=mock_repo)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_obter_item_por_id_invalido_lanca_erro(mock_repo):
    usecase = ObterItemEstoquePorIdUseCase(item_estoque_repo=mock_repo)

    with pytest.raises(Exception):
        await usecase.execute("id-invalido")


# ============================================================
# ListarItensEstoqueUseCase
# ============================================================

async def test_listar_itens_sem_filtros_retorna_lista_vazia(mock_repo):
    mock_repo.listar.return_value = []
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    resultado = await usecase.execute(ListarItensEstoqueFiltro())

    assert resultado == []
    mock_repo.listar.assert_called_once()


async def test_listar_itens_retorna_lista_com_itens(mock_repo):
    itens = [_item_fake("Filtro de óleo"), _item_fake("Vela de ignição", codigo="VG-001")]
    mock_repo.listar.return_value = itens
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    resultado = await usecase.execute(ListarItensEstoqueFiltro())

    assert len(resultado) == 2
    assert all(isinstance(r, ItemEstoqueResponse) for r in resultado)


async def test_listar_itens_filtrando_por_nome(mock_repo, item_existente):
    mock_repo.listar.return_value = [item_existente]
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(nome="Filtro")
    resultado = await usecase.execute(filtro)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_itens_filtrando_por_tipo(mock_repo, item_existente):
    mock_repo.listar.return_value = [item_existente]
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(tipo=TipoItemEstoque.PECA)
    resultado = await usecase.execute(filtro)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_itens_filtrando_por_codigo(mock_repo, item_existente):
    mock_repo.listar.return_value = [item_existente]
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(codigo="FO-001")
    resultado = await usecase.execute(filtro)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_itens_filtrando_por_ativo(mock_repo, item_existente):
    mock_repo.listar.return_value = [item_existente]
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(ativo=True)
    resultado = await usecase.execute(filtro)

    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_itens_filtrando_por_baixo_estoque(mock_repo, item_existente):
    mock_repo.listar.return_value = [item_existente]
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(baixo_estoque=True)
    resultado = await usecase.execute(filtro)

    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_itens_repassa_todos_filtros(mock_repo):
    mock_repo.listar.return_value = []
    usecase = ListarItensEstoqueUseCase(item_estoque_repo=mock_repo)

    filtro = ListarItensEstoqueFiltro(
        tipo=TipoItemEstoque.INSUMO,
        nome="Óleo",
        codigo="OL-001",
        ativo=True,
        baixo_estoque=False,
    )
    await usecase.execute(filtro)

    mock_repo.listar.assert_called_once_with(filtro)


# ============================================================
# AtualizarItemEstoqueUseCase
# ============================================================

async def test_atualizar_item_nome_com_sucesso(mock_uow, item_existente):
    item_atualizado = ItemEstoque(
        id=item_existente.id,
        tipo=item_existente.tipo,
        nome="Novo nome",
        descricao=item_existente.descricao,
        codigo=item_existente.codigo,
        quantidade_disponivel=item_existente.quantidade_disponivel,
        quantidade_reservada=item_existente.quantidade_reservada,
        quantidade_minima=item_existente.quantidade_minima,
        valor_unitario=item_existente.valor_unitario,
        ativo=item_existente.ativo,
        criado_em=item_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = item_atualizado

    dto = AtualizarItemEstoque(nome="Novo nome")
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(item_existente.id), dto)

    assert isinstance(resultado, ItemEstoqueResponse)
    assert resultado.nome == "Novo nome"
    mock_uow.item_estoque_repo.atualizar.assert_called_once()


async def test_atualizar_item_valor_unitario(mock_uow, item_existente):
    item_atualizado = ItemEstoque(
        id=item_existente.id,
        tipo=item_existente.tipo,
        nome=item_existente.nome,
        descricao=item_existente.descricao,
        codigo=item_existente.codigo,
        quantidade_disponivel=item_existente.quantidade_disponivel,
        quantidade_reservada=item_existente.quantidade_reservada,
        quantidade_minima=item_existente.quantidade_minima,
        valor_unitario=Decimal("99.90"),
        ativo=item_existente.ativo,
        criado_em=item_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = item_atualizado

    dto = AtualizarItemEstoque(valor_unitario=Decimal("99.90"))
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(item_existente.id), dto)

    assert resultado.valor_unitario == Decimal("99.90")


async def test_atualizar_item_tipo(mock_uow, item_existente):
    item_atualizado = ItemEstoque(
        id=item_existente.id,
        tipo=TipoItemEstoque.INSUMO,
        nome=item_existente.nome,
        descricao=item_existente.descricao,
        codigo=item_existente.codigo,
        quantidade_disponivel=item_existente.quantidade_disponivel,
        quantidade_reservada=item_existente.quantidade_reservada,
        quantidade_minima=item_existente.quantidade_minima,
        valor_unitario=item_existente.valor_unitario,
        ativo=item_existente.ativo,
        criado_em=item_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = item_atualizado

    dto = AtualizarItemEstoque(tipo=TipoItemEstoque.INSUMO)
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(item_existente.id), dto)

    assert resultado.tipo == TipoItemEstoque.INSUMO.value


async def test_atualizar_item_preserva_campos_nao_informados(mock_uow, item_existente):
    """Atualizar apenas quantidade_minima deve preservar nome, valor e tipo."""
    item_atualizado = ItemEstoque(
        id=item_existente.id,
        tipo=item_existente.tipo,
        nome=item_existente.nome,
        descricao=item_existente.descricao,
        codigo=item_existente.codigo,
        quantidade_disponivel=item_existente.quantidade_disponivel,
        quantidade_reservada=item_existente.quantidade_reservada,
        quantidade_minima=5,
        valor_unitario=item_existente.valor_unitario,
        ativo=item_existente.ativo,
        criado_em=item_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = item_atualizado

    dto = AtualizarItemEstoque(quantidade_minima=5)
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(item_existente.id), dto)

    assert resultado.nome == item_existente.nome
    assert resultado.valor_unitario == item_existente.valor_unitario
    assert resultado.quantidade_minima == 5


async def test_atualizar_item_codigo_duplicado_lanca_erro(mock_uow, item_existente):
    outro_item = _item_fake(nome="Outro item", codigo="OUTRO-001")
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.obter_por_codigo.return_value = outro_item

    dto = AtualizarItemEstoque(codigo="OUTRO-001")
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(CodigoItemEstoqueJaCadastradoError):
        await usecase.execute(str(item_existente.id), dto)

    mock_uow.item_estoque_repo.atualizar.assert_not_called()


async def test_atualizar_item_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.item_estoque_repo.obter_por_id.return_value = None
    dto = AtualizarItemEstoque(nome="Qualquer")
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(ID.generate()), dto)


async def test_atualizar_item_retorna_none_lanca_erro(mock_uow, item_existente):
    """Cobre o caso em que repo.atualizar retorna None."""
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = None

    dto = AtualizarItemEstoque(nome="Qualquer")
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(item_existente.id), dto)


async def test_atualizar_item_dados_invalidos_lanca_erro(mock_uow, item_existente):
    """Nome vazio deve levantar ItemEstoqueInvalidoError ao montar a entidade."""
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente

    dto = AtualizarItemEstoque(nome="")
    usecase = AtualizarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueInvalidoError):
        await usecase.execute(str(item_existente.id), dto)


# ============================================================
# AtivarItemEstoqueUseCase
# ============================================================

async def test_ativar_item_sucesso(mock_uow):
    item_inativo = _item_fake(ativo=False)
    item_ativado = ItemEstoque(
        id=item_inativo.id,
        tipo=item_inativo.tipo,
        nome=item_inativo.nome,
        descricao=item_inativo.descricao,
        codigo=item_inativo.codigo,
        quantidade_disponivel=item_inativo.quantidade_disponivel,
        quantidade_reservada=item_inativo.quantidade_reservada,
        quantidade_minima=item_inativo.quantidade_minima,
        valor_unitario=item_inativo.valor_unitario,
        ativo=True,
        criado_em=item_inativo.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_inativo
    mock_uow.item_estoque_repo.atualizar.return_value = item_ativado

    usecase = AtivarItemEstoqueUseCase(uow=mock_uow)
    resultado = await usecase.execute(str(item_inativo.id))

    assert isinstance(resultado, ItemEstoqueResponse)
    assert resultado.ativo is True
    mock_uow.item_estoque_repo.atualizar.assert_called_once()


async def test_ativar_item_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.item_estoque_repo.obter_por_id.return_value = None
    usecase = AtivarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_ativar_item_atualizar_retorna_none_lanca_erro(mock_uow, item_existente):
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = None
    usecase = AtivarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(item_existente.id))


# ============================================================
# DesativarItemEstoqueUseCase
# ============================================================

async def test_desativar_item_sucesso(mock_uow, item_existente):
    item_desativado = ItemEstoque(
        id=item_existente.id,
        tipo=item_existente.tipo,
        nome=item_existente.nome,
        descricao=item_existente.descricao,
        codigo=item_existente.codigo,
        quantidade_disponivel=item_existente.quantidade_disponivel,
        quantidade_reservada=item_existente.quantidade_reservada,
        quantidade_minima=item_existente.quantidade_minima,
        valor_unitario=item_existente.valor_unitario,
        ativo=False,
        criado_em=item_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = item_desativado

    usecase = DesativarItemEstoqueUseCase(uow=mock_uow)
    resultado = await usecase.execute(str(item_existente.id))

    assert isinstance(resultado, ItemEstoqueResponse)
    assert resultado.ativo is False
    mock_uow.item_estoque_repo.atualizar.assert_called_once()


async def test_desativar_item_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.item_estoque_repo.obter_por_id.return_value = None
    usecase = DesativarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_desativar_item_atualizar_retorna_none_lanca_erro(mock_uow, item_existente):
    mock_uow.item_estoque_repo.obter_por_id.return_value = item_existente
    mock_uow.item_estoque_repo.atualizar.return_value = None
    usecase = DesativarItemEstoqueUseCase(uow=mock_uow)

    with pytest.raises(ItemEstoqueNaoEncontradoError):
        await usecase.execute(str(item_existente.id))
