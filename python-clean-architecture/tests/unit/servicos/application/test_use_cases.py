from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.servicos.application.dtos.servico import (
    AtualizarServico,
    CriarServicoRequest,
    ServicoResponse,
)
from app.modules.servicos.application.use_cases.ativar_servico import AtivarServicoUseCase
from app.modules.servicos.application.use_cases.atualizar_servico import AtualizarServicoUseCase
from app.modules.servicos.application.use_cases.criar_servico import CriarServicoUseCase
from app.modules.servicos.application.use_cases.desativar_servico import DesativarServicoUseCase
from app.modules.servicos.application.use_cases.listar_servicos import ListarServicosUseCase
from app.modules.servicos.application.use_cases.obter_servico_por_id import ObterServicoPorIdUseCase
from app.modules.servicos.application.use_cases.obter_servico_por_nome import ObterServicoPorNomeUseCase
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import (
    NomeServicoJaCadastradoError,
    ServicoInvalidoError,
    ServicoNaoEncontradoError,
)
from app.modules.servicos.domain.filters.servico import ListarServicosFiltro
from app.shared.value_objects.id import ID


# --- Helpers ---

def _servico_fake(nome="Troca de óleo", ativo=True) -> Servico:
    agora = datetime.now(UTC)
    return Servico(
        id=ID.generate(),
        nome=nome,
        descricao="Descrição do serviço",
        valor_base=Decimal("150.00"),
        tempo_medio_minutos=30,
        ativo=ativo,
        criado_em=agora,
        atualizado_em=agora,
    )


# --- Fixtures ---

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.obter_por_nome = AsyncMock(return_value=None)
    repo.listar = AsyncMock(return_value=[])
    repo.salvar = AsyncMock()
    repo.atualizar = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_uow(mock_repo):
    uow = MagicMock()
    uow.servico_repo = mock_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def servico_existente() -> Servico:
    return _servico_fake()


# ============================================================
# CriarServicoUseCase
# ============================================================

async def test_criar_servico_sucesso(mock_uow):
    dto = CriarServicoRequest(
        nome="Alinhamento",
        descricao="Alinhamento de rodas",
        valor_base=Decimal("80.00"),
        tempo_medio_minutos=45,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert isinstance(resultado, ServicoResponse)
    assert resultado.nome == "Alinhamento"
    assert resultado.valor_base == Decimal("80.00")
    assert resultado.ativo is True
    mock_uow.servico_repo.salvar.assert_called_once()


async def test_criar_servico_sem_descricao(mock_uow):
    dto = CriarServicoRequest(
        nome="Balanceamento",
        descricao=None,
        valor_base=Decimal("60.00"),
        tempo_medio_minutos=20,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(dto)

    assert resultado.descricao is None
    mock_uow.servico_repo.salvar.assert_called_once()


async def test_criar_servico_nome_duplicado_lanca_erro(mock_uow, servico_existente):
    mock_uow.servico_repo.obter_por_nome.return_value = servico_existente
    dto = CriarServicoRequest(
        nome=servico_existente.nome,
        valor_base=Decimal("100.00"),
        tempo_medio_minutos=30,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    with pytest.raises(NomeServicoJaCadastradoError):
        await usecase.execute(dto)

    mock_uow.servico_repo.salvar.assert_not_called()


async def test_criar_servico_invalido_nao_salva(mock_uow):
    """Nome vazio deve levantar ServicoInvalidoError antes de salvar."""
    dto = CriarServicoRequest(
        nome="",
        valor_base=Decimal("50.00"),
        tempo_medio_minutos=15,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoInvalidoError):
        await usecase.execute(dto)

    mock_uow.servico_repo.salvar.assert_not_called()


async def test_criar_servico_valor_negativo_nao_salva(mock_uow):
    dto = CriarServicoRequest(
        nome="Serviço válido",
        valor_base=Decimal("-1.00"),
        tempo_medio_minutos=15,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoInvalidoError):
        await usecase.execute(dto)

    mock_uow.servico_repo.salvar.assert_not_called()


async def test_criar_servico_tempo_zero_nao_salva(mock_uow):
    dto = CriarServicoRequest(
        nome="Serviço válido",
        valor_base=Decimal("50.00"),
        tempo_medio_minutos=0,
    )
    usecase = CriarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoInvalidoError):
        await usecase.execute(dto)

    mock_uow.servico_repo.salvar.assert_not_called()


# ============================================================
# ObterServicoPorIdUseCase
# ============================================================

async def test_obter_servico_por_id_sucesso(mock_repo, servico_existente):
    mock_repo.obter_por_id.return_value = servico_existente
    usecase = ObterServicoPorIdUseCase(servico_repo=mock_repo)

    resultado = await usecase.execute(str(servico_existente.id))

    assert isinstance(resultado, ServicoResponse)
    assert resultado.id == str(servico_existente.id)
    assert resultado.nome == servico_existente.nome


async def test_obter_servico_por_id_nao_encontrado(mock_repo):
    mock_repo.obter_por_id.return_value = None
    usecase = ObterServicoPorIdUseCase(servico_repo=mock_repo)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_obter_servico_por_id_invalido_lanca_erro(mock_repo):
    usecase = ObterServicoPorIdUseCase(servico_repo=mock_repo)

    with pytest.raises(Exception):
        await usecase.execute("id-invalido")


# ============================================================
# ObterServicoPorNomeUseCase
# ============================================================

async def test_obter_servico_por_nome_sucesso(mock_repo, servico_existente):
    mock_repo.obter_por_nome.return_value = servico_existente
    usecase = ObterServicoPorNomeUseCase(servico_repo=mock_repo)

    resultado = await usecase.execute(servico_existente.nome)

    assert isinstance(resultado, ServicoResponse)
    assert resultado.nome == servico_existente.nome


async def test_obter_servico_por_nome_nao_encontrado(mock_repo):
    mock_repo.obter_por_nome.return_value = None
    usecase = ObterServicoPorNomeUseCase(servico_repo=mock_repo)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute("Serviço Inexistente")


# ============================================================
# ListarServicosUseCase
# ============================================================

async def test_listar_servicos_sem_filtros_retorna_lista_vazia(mock_repo):
    mock_repo.listar.return_value = []
    usecase = ListarServicosUseCase(servico_repo=mock_repo)

    resultado = await usecase.execute(ListarServicosFiltro())

    assert resultado == []
    mock_repo.listar.assert_called_once()


async def test_listar_servicos_retorna_lista_com_itens(mock_repo):
    servicos = [_servico_fake("Troca de óleo"), _servico_fake("Alinhamento")]
    mock_repo.listar.return_value = servicos
    usecase = ListarServicosUseCase(servico_repo=mock_repo)

    resultado = await usecase.execute(ListarServicosFiltro())

    assert len(resultado) == 2
    assert all(isinstance(r, ServicoResponse) for r in resultado)


async def test_listar_servicos_filtrando_por_nome(mock_repo, servico_existente):
    mock_repo.listar.return_value = [servico_existente]
    usecase = ListarServicosUseCase(servico_repo=mock_repo)

    filtro = ListarServicosFiltro(nome="Troca")
    resultado = await usecase.execute(filtro)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_servicos_filtrando_por_ativo(mock_repo, servico_existente):
    mock_repo.listar.return_value = [servico_existente]
    usecase = ListarServicosUseCase(servico_repo=mock_repo)

    filtro = ListarServicosFiltro(ativo=True)
    resultado = await usecase.execute(filtro)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtro)


async def test_listar_servicos_repassa_filtros_corretamente(mock_repo):
    mock_repo.listar.return_value = []
    usecase = ListarServicosUseCase(servico_repo=mock_repo)

    filtro = ListarServicosFiltro(nome="Balanceamento", ativo=False)
    await usecase.execute(filtro)

    mock_repo.listar.assert_called_once_with(filtro)


# ============================================================
# AtualizarServicoUseCase
# ============================================================

async def test_atualizar_servico_nome_com_sucesso(mock_uow, servico_existente):
    servico_atualizado = Servico(
        id=servico_existente.id,
        nome="Novo Nome",
        descricao=servico_existente.descricao,
        valor_base=servico_existente.valor_base,
        tempo_medio_minutos=servico_existente.tempo_medio_minutos,
        ativo=servico_existente.ativo,
        criado_em=servico_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = servico_atualizado
    dto = AtualizarServico(nome="Novo Nome")
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_existente.id), dto)

    assert isinstance(resultado, ServicoResponse)
    assert resultado.nome == "Novo Nome"
    mock_uow.servico_repo.atualizar.assert_called_once()


async def test_atualizar_servico_valor_base_com_sucesso(mock_uow, servico_existente):
    servico_atualizado = Servico(
        id=servico_existente.id,
        nome=servico_existente.nome,
        descricao=servico_existente.descricao,
        valor_base=Decimal("200.00"),
        tempo_medio_minutos=servico_existente.tempo_medio_minutos,
        ativo=servico_existente.ativo,
        criado_em=servico_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = servico_atualizado
    dto = AtualizarServico(valor_base=Decimal("200.00"))
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_existente.id), dto)

    assert resultado.valor_base == Decimal("200.00")


async def test_atualizar_servico_tempo_com_sucesso(mock_uow, servico_existente):
    servico_atualizado = Servico(
        id=servico_existente.id,
        nome=servico_existente.nome,
        descricao=servico_existente.descricao,
        valor_base=servico_existente.valor_base,
        tempo_medio_minutos=90,
        ativo=servico_existente.ativo,
        criado_em=servico_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = servico_atualizado
    dto = AtualizarServico(tempo_medio_minutos=90)
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_existente.id), dto)

    assert resultado.tempo_medio_minutos == 90


async def test_atualizar_servico_preserva_campos_nao_informados(mock_uow, servico_existente):
    """Atualizar apenas descricao deve preservar nome, valor e tempo."""
    servico_atualizado = Servico(
        id=servico_existente.id,
        nome=servico_existente.nome,
        descricao="Nova descrição",
        valor_base=servico_existente.valor_base,
        tempo_medio_minutos=servico_existente.tempo_medio_minutos,
        ativo=servico_existente.ativo,
        criado_em=servico_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = servico_atualizado
    dto = AtualizarServico(descricao="Nova descrição")
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_existente.id), dto)

    assert resultado.nome == servico_existente.nome
    assert resultado.valor_base == servico_existente.valor_base


async def test_atualizar_servico_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.servico_repo.obter_por_id.return_value = None
    dto = AtualizarServico(nome="Qualquer")
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(ID.generate()), dto)


async def test_atualizar_servico_atualizar_retorna_none_lanca_erro(mock_uow, servico_existente):
    """Cobre o caso em que repo.atualizar retorna None."""
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = None
    dto = AtualizarServico(nome="Teste")
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(servico_existente.id), dto)


async def test_atualizar_servico_dados_invalidos_lanca_erro(mock_uow, servico_existente):
    """Nome vazio deve levantar ServicoInvalidoError ao montar a entidade."""
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    dto = AtualizarServico(nome="")
    usecase = AtualizarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoInvalidoError):
        await usecase.execute(str(servico_existente.id), dto)


# ============================================================
# AtivarServicoUseCase
# ============================================================

async def test_ativar_servico_sucesso(mock_uow):
    servico_inativo = _servico_fake(ativo=False)
    servico_ativado = Servico(
        id=servico_inativo.id,
        nome=servico_inativo.nome,
        descricao=servico_inativo.descricao,
        valor_base=servico_inativo.valor_base,
        tempo_medio_minutos=servico_inativo.tempo_medio_minutos,
        ativo=True,
        criado_em=servico_inativo.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_inativo
    mock_uow.servico_repo.atualizar.return_value = servico_ativado
    usecase = AtivarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_inativo.id))

    assert isinstance(resultado, ServicoResponse)
    assert resultado.ativo is True
    mock_uow.servico_repo.atualizar.assert_called_once()


async def test_ativar_servico_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.servico_repo.obter_por_id.return_value = None
    usecase = AtivarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_ativar_servico_atualizar_retorna_none_lanca_erro(mock_uow, servico_existente):
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = None
    usecase = AtivarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(servico_existente.id))


# ============================================================
# DesativarServicoUseCase
# ============================================================

async def test_desativar_servico_sucesso(mock_uow, servico_existente):
    servico_desativado = Servico(
        id=servico_existente.id,
        nome=servico_existente.nome,
        descricao=servico_existente.descricao,
        valor_base=servico_existente.valor_base,
        tempo_medio_minutos=servico_existente.tempo_medio_minutos,
        ativo=False,
        criado_em=servico_existente.criado_em,
        atualizado_em=datetime.now(UTC),
    )
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = servico_desativado
    usecase = DesativarServicoUseCase(uow=mock_uow)

    resultado = await usecase.execute(str(servico_existente.id))

    assert isinstance(resultado, ServicoResponse)
    assert resultado.ativo is False
    mock_uow.servico_repo.atualizar.assert_called_once()


async def test_desativar_servico_nao_encontrado_lanca_erro(mock_uow):
    mock_uow.servico_repo.obter_por_id.return_value = None
    usecase = DesativarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


async def test_desativar_servico_atualizar_retorna_none_lanca_erro(mock_uow, servico_existente):
    mock_uow.servico_repo.obter_por_id.return_value = servico_existente
    mock_uow.servico_repo.atualizar.return_value = None
    usecase = DesativarServicoUseCase(uow=mock_uow)

    with pytest.raises(ServicoNaoEncontradoError):
        await usecase.execute(str(servico_existente.id))
