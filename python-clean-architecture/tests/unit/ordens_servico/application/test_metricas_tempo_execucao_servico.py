"""Testes unitários de application — Etapa 4: Métricas de tempo de execução por serviço.

Cobre:
  - ObterEstatisticaTempoExecucaoServicoUseCase
  - ListarExecucoesServicoUseCase
"""

import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.ordens_servico.application.use_cases.obter_estatistica_tempo_execucao_servico import (
    ObterEstatisticaTempoExecucaoServicoUseCase,
)
from app.modules.ordens_servico.application.use_cases.listar_execucoes_servico import (
    ListarExecucoesServicoUseCase,
)
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    EstatisticaTempoExecucaoServicoResponse,
    ExecucaoServicoResponse,
    ListagemExecucoesServicoResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _servico_fake(
    servico_id: _uuid.UUID | None = None,
    nome: str = "Servico Metrica Troca Correia",
    tempo_medio_minutos: int = 60,
) -> Servico:
    agora = _agora()
    return Servico(
        id=ID.from_string(str(servico_id)) if servico_id else ID.generate(),
        nome=nome,
        descricao="Servico usado para validar metricas",
        valor_base=Decimal("180.00"),
        tempo_medio_minutos=tempo_medio_minutos,
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )


def _stats_fake(
    quantidade: int = 2,
    media: float | None = 67.5,
    menor: int | None = 60,
    maior: int | None = 75,
) -> dict:
    return {
        "quantidade": quantidade,
        "media": media,
        "menor": menor,
        "maior": maior,
    }


def _execucao_row(
    ordem_servico_id: _uuid.UUID | None = None,
    ordem_servico_servico_id: _uuid.UUID | None = None,
    tempo_executado_minutos: int = 60,
    status_os: str = "FINALIZADA",
) -> dict:
    return {
        "ordem_servico_id": str(ordem_servico_id or uuid4()),
        "ordem_servico_servico_id": str(ordem_servico_servico_id or uuid4()),
        "tempo_executado_minutos": tempo_executado_minutos,
        "status_os": status_os,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_os_repo():
    repo = MagicMock()
    repo.obter_estatistica_tempo_execucao_servico = AsyncMock(return_value=_stats_fake())
    repo.listar_execucoes_servico = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_servico_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    return repo


# ---------------------------------------------------------------------------
# ObterEstatisticaTempoExecucaoServicoUseCase
# ---------------------------------------------------------------------------

class TestObterEstatisticaTempoExecucaoServicoUseCase:

    async def test_deve_obter_estatistica_tempo_execucao_de_servico_com_execucoes(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id, tempo_medio_minutos=60)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake(quantidade=2, media=67.5, menor=60, maior=75)
        )

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert isinstance(resultado, EstatisticaTempoExecucaoServicoResponse)
        assert resultado.servico_id == str(servico_id)
        assert resultado.nome_servico == servico.nome
        assert resultado.tempo_estimado_minutos == 60
        assert resultado.quantidade_ordens_servico == 2
        assert resultado.tempo_medio_minutos == 67.5
        assert resultado.menor_tempo_minutos == 60
        assert resultado.maior_tempo_minutos == 75

    async def test_deve_retornar_estatistica_vazia_para_servico_existente_sem_execucoes(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id, tempo_medio_minutos=45)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake(quantidade=0, media=None, menor=None, maior=None)
        )

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert resultado.servico_id == str(servico_id)
        assert resultado.tempo_estimado_minutos == 45
        assert resultado.quantidade_ordens_servico == 0
        assert resultado.tempo_medio_minutos is None
        assert resultado.menor_tempo_minutos is None
        assert resultado.maior_tempo_minutos is None

    async def test_nao_deve_obter_estatistica_de_servico_inexistente(
        self, mock_os_repo, mock_servico_repo
    ):
        mock_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )

        with pytest.raises(ServicoNaoEncontradoError):
            await uc.execute(str(uuid4()))

        mock_os_repo.obter_estatistica_tempo_execucao_servico.assert_not_called()

    async def test_deve_mapear_tempo_medio_do_catalogo_para_tempo_estimado_minutos(
        self, mock_os_repo, mock_servico_repo
    ):
        """O campo tempo_medio_minutos do catálogo deve ser exposto como
        tempo_estimado_minutos no DTO de métricas."""
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id, tempo_medio_minutos=90)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake(quantidade=1, media=85.0, menor=85, maior=85)
        )

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        # Validar que o DTO usa tempo_estimado_minutos (não tempo_medio_minutos)
        assert hasattr(resultado, "tempo_estimado_minutos")
        assert resultado.tempo_estimado_minutos == 90

    async def test_deve_preservar_media_decimal_quando_nao_for_inteira(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake(quantidade=2, media=67.5, menor=60, maior=75)
        )

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        # Não deve arredondar 67.5 para 67 ou 68
        assert resultado.tempo_medio_minutos == 67.5
        assert resultado.tempo_medio_minutos != 67
        assert resultado.tempo_medio_minutos != 68

    async def test_estatistica_nao_deve_fazer_commit(
        self, mock_os_repo, mock_servico_repo
    ):
        """Use case de leitura: nenhum commit deve ser chamado."""
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake()
        )
        # O use case não usa UoW — nenhum commit deve ser disparado sobre o repo
        mock_os_repo.commit = AsyncMock()

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        await uc.execute(str(servico_id))

        mock_os_repo.commit.assert_not_called()

    async def test_deve_consultar_servico_antes_de_buscar_estatistica(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.obter_estatistica_tempo_execucao_servico = AsyncMock(
            return_value=_stats_fake()
        )

        uc = ObterEstatisticaTempoExecucaoServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        await uc.execute(str(servico_id))

        mock_servico_repo.obter_por_id.assert_called_once()
        mock_os_repo.obter_estatistica_tempo_execucao_servico.assert_called_once_with(
            servico_id
        )


# ---------------------------------------------------------------------------
# ListarExecucoesServicoUseCase
# ---------------------------------------------------------------------------

class TestListarExecucoesServicoUseCase:

    async def test_deve_listar_execucoes_de_servico_com_execucoes_finalizadas(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        os1_id = uuid4()
        os2_id = uuid4()
        oss1_id = uuid4()
        oss2_id = uuid4()

        servico = _servico_fake(servico_id=servico_id, tempo_medio_minutos=60)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[
            _execucao_row(os1_id, oss1_id, tempo_executado_minutos=60, status_os="FINALIZADA"),
            _execucao_row(os2_id, oss2_id, tempo_executado_minutos=75, status_os="FINALIZADA"),
        ])

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert isinstance(resultado, ListagemExecucoesServicoResponse)
        assert resultado.servico_id == str(servico_id)
        assert resultado.nome_servico == servico.nome
        assert resultado.tempo_estimado_minutos == 60
        assert resultado.quantidade_ordens_servico == 2
        assert len(resultado.execucoes) == 2

        tempos = {e.tempo_executado_minutos for e in resultado.execucoes}
        assert tempos == {60, 75}

        for execucao in resultado.execucoes:
            assert execucao.status_os == "FINALIZADA"

    async def test_deve_retornar_lista_vazia_para_servico_existente_sem_execucoes(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id, tempo_medio_minutos=45)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[])

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert resultado.servico_id == str(servico_id)
        assert resultado.nome_servico == servico.nome
        assert resultado.tempo_estimado_minutos == 45
        assert resultado.quantidade_ordens_servico == 0
        assert resultado.execucoes == []

    async def test_nao_deve_listar_execucoes_de_servico_inexistente(
        self, mock_os_repo, mock_servico_repo
    ):
        mock_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )

        with pytest.raises(ServicoNaoEncontradoError):
            await uc.execute(str(uuid4()))

        mock_os_repo.listar_execucoes_servico.assert_not_called()

    async def test_deve_mapear_execucoes_com_campos_minimos(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        os_id = uuid4()
        oss_id = uuid4()

        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[
            _execucao_row(os_id, oss_id, tempo_executado_minutos=60, status_os="FINALIZADA"),
        ])

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert len(resultado.execucoes) == 1
        execucao = resultado.execucoes[0]

        assert isinstance(execucao, ExecucaoServicoResponse)
        assert execucao.ordem_servico_id == str(os_id)
        assert execucao.ordem_servico_servico_id == str(oss_id)
        assert execucao.tempo_executado_minutos == 60
        assert execucao.status_os == "FINALIZADA"

    async def test_quantidade_ordens_servico_deve_igualar_tamanho_da_lista(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[
            _execucao_row(tempo_executado_minutos=40),
            _execucao_row(tempo_executado_minutos=50),
            _execucao_row(tempo_executado_minutos=70),
        ])

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        resultado = await uc.execute(str(servico_id))

        assert resultado.quantidade_ordens_servico == len(resultado.execucoes)
        assert resultado.quantidade_ordens_servico == 3

    async def test_execucoes_nao_deve_fazer_commit(
        self, mock_os_repo, mock_servico_repo
    ):
        """Use case de leitura: nenhum commit deve ser chamado."""
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[])
        mock_os_repo.commit = AsyncMock()

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        await uc.execute(str(servico_id))

        mock_os_repo.commit.assert_not_called()

    async def test_deve_consultar_servico_antes_de_listar_execucoes(
        self, mock_os_repo, mock_servico_repo
    ):
        servico_id = uuid4()
        servico = _servico_fake(servico_id=servico_id)
        mock_servico_repo.obter_por_id = AsyncMock(return_value=servico)
        mock_os_repo.listar_execucoes_servico = AsyncMock(return_value=[])

        uc = ListarExecucoesServicoUseCase(
            ordem_servico_repo=mock_os_repo,
            servico_repo=mock_servico_repo,
        )
        await uc.execute(str(servico_id))

        mock_servico_repo.obter_por_id.assert_called_once()
        mock_os_repo.listar_execucoes_servico.assert_called_once_with(servico_id)
