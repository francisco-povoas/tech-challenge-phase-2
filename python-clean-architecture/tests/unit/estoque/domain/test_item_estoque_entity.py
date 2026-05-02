from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.estoque.domain.entities.item_estoque import ItemEstoque, TipoItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueInvalidoError
from app.modules.estoque.domain.filters.item_estoque import ListarItensEstoqueFiltro
from app.shared.value_objects.id import ID


# --- Helper ---

def item_valido(**kwargs) -> ItemEstoque:
    """Retorna ItemEstoque com dados válidos, permitindo overrides."""
    agora = datetime.now(UTC)
    defaults = dict(
        id=ID.generate(),
        tipo=TipoItemEstoque.PECA,
        nome="Filtro de óleo",
        descricao="Filtro de óleo do motor",
        codigo="FO-001",
        quantidade_disponivel=10,
        quantidade_reservada=0,
        quantidade_minima=2,
        valor_unitario=Decimal("35.00"),
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )
    defaults.update(kwargs)
    return ItemEstoque(**defaults)


# ============================================================
# Criação válida
# ============================================================

def test_criar_item_estoque_peca_valido():
    item = item_valido()
    assert item.nome == "Filtro de óleo"
    assert item.tipo == TipoItemEstoque.PECA
    assert item.ativo is True
    assert item.quantidade_reservada == 0


def test_criar_item_estoque_insumo_valido():
    item = item_valido(tipo=TipoItemEstoque.INSUMO, nome="Óleo 5W30")
    assert item.tipo == TipoItemEstoque.INSUMO


def test_criar_item_sem_descricao():
    item = item_valido(descricao=None)
    assert item.descricao is None


def test_criar_item_sem_codigo():
    item = item_valido(codigo=None)
    assert item.codigo is None


def test_criar_item_inativo():
    item = item_valido(ativo=False)
    assert item.ativo is False


def test_criar_item_quantidade_zero():
    item = item_valido(quantidade_disponivel=0, quantidade_minima=0)
    assert item.quantidade_disponivel == 0
    assert item.quantidade_minima == 0


def test_criar_item_valor_unitario_zero():
    item = item_valido(valor_unitario=Decimal("0"))
    assert item.valor_unitario == Decimal("0")


def test_criar_item_nome_com_100_caracteres():
    item = item_valido(nome="X" * 100)
    assert len(item.nome) == 100


def test_criar_item_descricao_com_255_caracteres():
    item = item_valido(descricao="D" * 255)
    assert len(item.descricao) == 255


def test_criar_item_codigo_com_50_caracteres():
    item = item_valido(codigo="C" * 50)
    assert len(item.codigo) == 50


# ============================================================
# Validações de nome
# ============================================================

def test_nome_vazio_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="nome"):
        item_valido(nome="")


def test_nome_apenas_espacos_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="nome"):
        item_valido(nome="   ")


def test_nome_acima_de_100_caracteres_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="100"):
        item_valido(nome="X" * 101)


# ============================================================
# Validações de descrição
# ============================================================

def test_descricao_acima_de_255_caracteres_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="255"):
        item_valido(descricao="D" * 256)


# ============================================================
# Validações de código
# ============================================================

def test_codigo_acima_de_50_caracteres_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="50"):
        item_valido(codigo="C" * 51)


# ============================================================
# Validações de quantidades
# ============================================================

def test_quantidade_disponivel_negativa_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="disponível"):
        item_valido(quantidade_disponivel=-1)


def test_quantidade_reservada_negativa_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="reservada"):
        item_valido(quantidade_reservada=-1)


def test_quantidade_minima_negativa_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="mínima"):
        item_valido(quantidade_minima=-1)


# ============================================================
# Validações de valor unitário
# ============================================================

def test_valor_unitario_negativo_lanca_erro():
    with pytest.raises(ItemEstoqueInvalidoError, match="negativo"):
        item_valido(valor_unitario=Decimal("-0.01"))


# ============================================================
# TipoItemEstoque
# ============================================================

def test_tipo_peca_valor():
    assert TipoItemEstoque.PECA.value == "PECA"


def test_tipo_insumo_valor():
    assert TipoItemEstoque.INSUMO.value == "INSUMO"


# ============================================================
# DTOs
# ============================================================

def test_dto_atualizar_sem_campos_lanca_erro():
    from app.modules.estoque.application.dtos.item_estoque import AtualizarItemEstoque
    with pytest.raises(ValueError, match="Pelo menos um campo"):
        AtualizarItemEstoque()


def test_dto_atualizar_com_nome():
    from app.modules.estoque.application.dtos.item_estoque import AtualizarItemEstoque
    dto = AtualizarItemEstoque(nome="Novo nome")
    assert dto.nome == "Novo nome"


def test_dto_atualizar_com_valor_unitario():
    from app.modules.estoque.application.dtos.item_estoque import AtualizarItemEstoque
    dto = AtualizarItemEstoque(valor_unitario=Decimal("99.90"))
    assert dto.valor_unitario == Decimal("99.90")


def test_dto_atualizar_com_tipo():
    from app.modules.estoque.application.dtos.item_estoque import AtualizarItemEstoque
    dto = AtualizarItemEstoque(tipo=TipoItemEstoque.INSUMO)
    assert dto.tipo == TipoItemEstoque.INSUMO


# ============================================================
# Filtros
# ============================================================

def test_filtro_defaults():
    filtro = ListarItensEstoqueFiltro()
    assert filtro.tipo is None
    assert filtro.nome is None
    assert filtro.codigo is None
    assert filtro.ativo is None
    assert filtro.baixo_estoque is None


def test_filtro_com_valores():
    filtro = ListarItensEstoqueFiltro(
        tipo=TipoItemEstoque.PECA,
        nome="Filtro",
        codigo="FO-001",
        ativo=True,
        baixo_estoque=False,
    )
    assert filtro.tipo == TipoItemEstoque.PECA
    assert filtro.nome == "Filtro"
    assert filtro.codigo == "FO-001"
    assert filtro.ativo is True
    assert filtro.baixo_estoque is False
