from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import ServicoInvalidoError
from app.shared.value_objects.id import ID


# --- Fixtures ---

def servico_valido(**kwargs) -> Servico:
    """Retorna uma instância de Servico com dados válidos, permitindo overrides."""
    agora = datetime.now(UTC)
    defaults = dict(
        id=ID.generate(),
        nome="Troca de óleo",
        descricao="Troca de óleo do motor",
        valor_base=Decimal("150.00"),
        tempo_medio_minutos=30,
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )
    defaults.update(kwargs)
    return Servico(**defaults)


# --- Criação válida ---

def test_criar_servico_valido():
    servico = servico_valido()
    assert servico.nome == "Troca de óleo"
    assert servico.valor_base == Decimal("150.00")
    assert servico.tempo_medio_minutos == 30
    assert servico.ativo is True


def test_criar_servico_sem_descricao():
    servico = servico_valido(descricao=None)
    assert servico.descricao is None


def test_criar_servico_valor_base_zero():
    servico = servico_valido(valor_base=Decimal("0"))
    assert servico.valor_base == Decimal("0")


def test_criar_servico_inativo():
    servico = servico_valido(ativo=False)
    assert servico.ativo is False


def test_criar_servico_nome_com_100_caracteres():
    nome_longo = "A" * 100
    servico = servico_valido(nome=nome_longo)
    assert len(servico.nome) == 100


def test_criar_servico_descricao_com_255_caracteres():
    descricao_longa = "D" * 255
    servico = servico_valido(descricao=descricao_longa)
    assert len(servico.descricao) == 255


# --- Validações de nome ---

def test_criar_servico_nome_vazio_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="nome"):
        servico_valido(nome="")


def test_criar_servico_nome_apenas_espacos_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="nome"):
        servico_valido(nome="   ")


def test_criar_servico_nome_acima_de_100_caracteres_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="100"):
        servico_valido(nome="A" * 101)


# --- Validações de descrição ---

def test_criar_servico_descricao_acima_de_255_caracteres_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="255"):
        servico_valido(descricao="D" * 256)


# --- Validações de valor_base ---

def test_criar_servico_valor_base_negativo_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="negativo"):
        servico_valido(valor_base=Decimal("-0.01"))


# --- Validações de tempo_medio_minutos ---

def test_criar_servico_tempo_medio_zero_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="maior que zero"):
        servico_valido(tempo_medio_minutos=0)


def test_criar_servico_tempo_medio_negativo_lanca_erro():
    with pytest.raises(ServicoInvalidoError, match="maior que zero"):
        servico_valido(tempo_medio_minutos=-10)


# --- DTOs ---

def test_dto_atualizar_servico_sem_campos_lanca_erro():
    from app.modules.servicos.application.dtos.servico import AtualizarServico
    with pytest.raises(ValueError, match="Pelo menos um campo"):
        AtualizarServico()


def test_dto_atualizar_servico_com_nome_valido():
    from app.modules.servicos.application.dtos.servico import AtualizarServico
    dto = AtualizarServico(nome="Novo nome")
    assert dto.nome == "Novo nome"


def test_dto_atualizar_servico_com_valor_base():
    from app.modules.servicos.application.dtos.servico import AtualizarServico
    dto = AtualizarServico(valor_base=Decimal("200.00"))
    assert dto.valor_base == Decimal("200.00")


def test_dto_filtro_servico_defaults():
    from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
    filtro = ListarServicosFiltro()
    assert filtro.nome is None
    assert filtro.ativo is None


def test_dto_filtro_servico_com_valores():
    from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
    filtro = ListarServicosFiltro(nome="Troca", ativo=True)
    assert filtro.nome == "Troca"
    assert filtro.ativo is True
