"""Testes unitários de application para a Fase 3 — Execução da OS.

Cobre:
  - IniciarExecucaoOrdemServicoUseCase
  - RegistrarTempoExecutadoServicoUseCase
  - FinalizarOrdemServicoUseCase
"""

import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.use_cases.iniciar_execucao_ordem_servico import (
    IniciarExecucaoOrdemServicoUseCase,
)
from app.modules.ordens_servico.application.use_cases.registrar_tempo_executado_servico import (
    RegistrarTempoExecutadoServicoUseCase,
)
from app.modules.ordens_servico.application.use_cases.finalizar_ordem_servico import (
    FinalizarOrdemServicoUseCase,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import (
    OrdemServico,
    StatusOrdemServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoServicoNaoEncontradoError,
    OrdemServicoServicoCanceladoError,
    OrdemServicoTransicaoInvalidaError,
    OrdemServicoPossuiItemAReceberError,
    OrdemServicoPossuiServicoSemTempoExecutadoError,
    TempoExecutadoInvalidoError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(
    status: StatusOrdemServico = StatusOrdemServico.APROVADA,
    os_id: _uuid.UUID | None = None,
) -> OrdemServico:
    agora = _agora()
    return OrdemServico(
        id=ID.from_string(str(os_id)) if os_id else ID.generate(),
        cliente_id=uuid4(),
        veiculo_id=uuid4(),
        status=status,
        queixa_inicial="Barulho no motor",
        diagnostico="Motor com desgaste",
        criado_em=agora,
        atualizado_em=agora,
        iniciado_diagnostico_em=agora,
        diagnostico_concluido_em=agora,
    )


def _osi_fake(
    os: OrdemServico,
    status: StatusItemNaOS = StatusItemNaOS.RESERVADO,
) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=_uuid.UUID(str(os.id)),
        item_estoque_id=uuid4(),
        nome_item="Filtro de óleo",
        tipo_item="PECA",
        quantidade=2,
        valor_unitario=Decimal("35.00"),
        status=status,
    )


def _oss_fake(
    os: OrdemServico,
    cancelado: bool = False,
    tempo_executado_minutos: int | None = None,
    servico_id: _uuid.UUID | None = None,
) -> OrdemServicoServico:
    return OrdemServicoServico(
        id=ID.generate(),
        ordem_servico_id=_uuid.UUID(str(os.id)),
        servico_id=servico_id or uuid4(),
        nome_servico="Troca de óleo",
        descricao_servico=None,
        valor_unitario=Decimal("120.00"),
        tempo_estimado_minutos=60,
        tempo_executado_minutos=tempo_executado_minutos,
        observacao=None,
        cancelado=cancelado,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_os_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.listar_itens_da_os = AsyncMock(return_value=[])
    repo.listar_servicos_da_os = AsyncMock(return_value=[])
    repo.obter_servico_por_id = AsyncMock(return_value=None)
    repo.atualizar = AsyncMock()
    repo.atualizar_item = AsyncMock()
    repo.atualizar_servico = AsyncMock()
    return repo


@pytest.fixture
def mock_item_estoque_repo():
    """Fake de estoque que falha se qualquer método for chamado (não deve ser usado na fase 3)."""
    repo = MagicMock()
    repo.obter_por_id_com_lock = AsyncMock(side_effect=AssertionError(
        "item_estoque_repo não deve ser chamado na fase de execução da OS"
    ))
    repo.atualizar = AsyncMock(side_effect=AssertionError(
        "item_estoque_repo não deve ser chamado na fase de execução da OS"
    ))
    return repo


@pytest.fixture
def mock_uow(mock_os_repo, mock_item_estoque_repo):
    uow = MagicMock()
    uow.ordem_servico_repo = mock_os_repo
    uow.item_estoque_repo = mock_item_estoque_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


# ---------------------------------------------------------------------------
# IniciarExecucaoOrdemServicoUseCase
# ---------------------------------------------------------------------------

class TestIniciarExecucaoOrdemServicoUseCase:
    async def test_deve_iniciar_execucao_de_os_aprovada(self, mock_uow):
        os = _os_fake(StatusOrdemServico.APROVADA)
        item_reservado = _osi_fake(os, StatusItemNaOS.RESERVADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item_reservado])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.EM_EXECUCAO.value
        mock_uow.commit.assert_called_once()

    async def test_deve_colocar_todos_itens_reservados_em_uso(self, mock_uow):
        os = _os_fake(StatusOrdemServico.APROVADA)
        item1 = _osi_fake(os, StatusItemNaOS.RESERVADO)
        item2 = _osi_fake(os, StatusItemNaOS.RESERVADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item1, item2])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id))

        # atualizar_item deve ter sido chamado duas vezes (um por item RESERVADO)
        assert mock_uow.ordem_servico_repo.atualizar_item.call_count == 2
        # verificar que os itens persistidos têm status EM_USO
        for mock_call in mock_uow.ordem_servico_repo.atualizar_item.call_args_list:
            item_persistido = mock_call.args[0]
            assert item_persistido.status == StatusItemNaOS.EM_USO

    async def test_deve_ignorar_itens_cancelados_ao_iniciar_execucao(self, mock_uow):
        os = _os_fake(StatusOrdemServico.APROVADA)
        item_reservado = _osi_fake(os, StatusItemNaOS.RESERVADO)
        item_cancelado = _osi_fake(os, StatusItemNaOS.CANCELADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_reservado, item_cancelado]
        )
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        # apenas o item RESERVADO deve ter sido atualizado
        assert mock_uow.ordem_servico_repo.atualizar_item.call_count == 1
        item_persistido = mock_uow.ordem_servico_repo.atualizar_item.call_args.args[0]
        assert item_persistido.status == StatusItemNaOS.EM_USO

        assert resultado.status == StatusOrdemServico.EM_EXECUCAO.value
        mock_uow.commit.assert_called_once()

    async def test_nao_deve_iniciar_execucao_de_os_inexistente(self, mock_uow):
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

        mock_uow.commit.assert_not_called()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.EM_EXECUCAO,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    async def test_nao_deve_iniciar_execucao_de_os_fora_de_aprovada(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_iniciar_execucao_com_item_a_receber_ativo(self, mock_uow):
        os = _os_fake(StatusOrdemServico.APROVADA)
        item_reservado = _osi_fake(os, StatusItemNaOS.RESERVADO)
        item_a_receber = _osi_fake(os, StatusItemNaOS.A_RECEBER)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_reservado, item_a_receber]
        )

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPossuiItemAReceberError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        mock_uow.ordem_servico_repo.atualizar_item.assert_not_called()
        mock_uow.ordem_servico_repo.atualizar.assert_not_called()

    async def test_iniciar_execucao_nao_deve_alterar_estoque(self, mock_uow):
        """item_estoque_repo não deve ser chamado ao iniciar execução."""
        os = _os_fake(StatusOrdemServico.APROVADA)
        item_reservado = _osi_fake(os, StatusItemNaOS.RESERVADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item_reservado])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        # Sobrescreve o mock de estoque com um que NÃO levanta erro, para verificar
        # que nenhum método foi invocado
        estoque_repo = MagicMock()
        estoque_repo.obter_por_id_com_lock = AsyncMock()
        estoque_repo.atualizar = AsyncMock()
        mock_uow.item_estoque_repo = estoque_repo

        uc = IniciarExecucaoOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id))

        estoque_repo.obter_por_id_com_lock.assert_not_called()
        estoque_repo.atualizar.assert_not_called()


# ---------------------------------------------------------------------------
# RegistrarTempoExecutadoServicoUseCase
# ---------------------------------------------------------------------------

class TestRegistrarTempoExecutadoServicoUseCase:
    async def test_deve_registrar_tempo_executado_em_servico_da_os(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, tempo_executado_minutos=None)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(
            ordem_servico_id=str(os.id),
            ordem_servico_servico_id=str(servico.id),
            tempo_executado_minutos=75,
        )

        assert resultado.tempo_executado_minutos == 75
        mock_uow.commit.assert_called_once()

    async def test_deve_sobrescrever_tempo_executado(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, tempo_executado_minutos=60)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(
            ordem_servico_id=str(os.id),
            ordem_servico_servico_id=str(servico.id),
            tempo_executado_minutos=90,
        )

        assert resultado.tempo_executado_minutos == 90
        mock_uow.commit.assert_called_once()

    async def test_nao_deve_registrar_tempo_em_os_inexistente(self, mock_uow):
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(
                ordem_servico_id=str(uuid4()),
                ordem_servico_servico_id=str(uuid4()),
                tempo_executado_minutos=60,
            )

        mock_uow.commit.assert_not_called()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    async def test_nao_deve_registrar_tempo_em_os_fora_de_em_execucao(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(
                ordem_servico_id=str(os.id),
                ordem_servico_servico_id=str(uuid4()),
                tempo_executado_minutos=60,
            )

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_tempo_em_servico_inexistente(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=None)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoServicoNaoEncontradoError):
            await uc.execute(
                ordem_servico_id=str(os.id),
                ordem_servico_servico_id=str(uuid4()),
                tempo_executado_minutos=60,
            )

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_tempo_em_servico_de_outra_os(self, mock_uow):
        """Serviço pertence a OS diferente da informada → erro de pertencimento."""
        os_a = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        os_b = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico_de_b = _oss_fake(os_b)  # ordem_servico_id = os_b.id

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os_a)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico_de_b)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoServicoNaoEncontradoError):
            await uc.execute(
                ordem_servico_id=str(os_a.id),
                ordem_servico_servico_id=str(servico_de_b.id),
                tempo_executado_minutos=60,
            )

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_tempo_zero(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(TempoExecutadoInvalidoError):
            await uc.execute(
                ordem_servico_id=str(os.id),
                ordem_servico_servico_id=str(servico.id),
                tempo_executado_minutos=0,
            )

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_tempo_negativo(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(TempoExecutadoInvalidoError):
            await uc.execute(
                ordem_servico_id=str(os.id),
                ordem_servico_servico_id=str(servico.id),
                tempo_executado_minutos=-10,
            )

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_tempo_em_servico_cancelado(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, cancelado=True)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoServicoCanceladoError):
            await uc.execute(
                ordem_servico_id=str(os.id),
                ordem_servico_servico_id=str(servico.id),
                tempo_executado_minutos=30,
            )

        mock_uow.commit.assert_not_called()

    async def test_registrar_tempo_persiste_nova_instancia_do_servico(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, tempo_executado_minutos=None)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_servico_por_id = AsyncMock(return_value=servico)

        uc = RegistrarTempoExecutadoServicoUseCase(uow=mock_uow)
        await uc.execute(
            ordem_servico_id=str(os.id),
            ordem_servico_servico_id=str(servico.id),
            tempo_executado_minutos=45,
        )

        mock_uow.ordem_servico_repo.atualizar_servico.assert_called_once()
        servico_persistido = mock_uow.ordem_servico_repo.atualizar_servico.call_args.args[0]
        assert servico_persistido.tempo_executado_minutos == 45


# ---------------------------------------------------------------------------
# FinalizarOrdemServicoUseCase
# ---------------------------------------------------------------------------

class TestFinalizarOrdemServicoUseCase:
    async def test_deve_finalizar_os_em_execucao_com_todos_servicos_ativos_com_tempo(
        self, mock_uow
    ):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico1 = _oss_fake(os, tempo_executado_minutos=50)
        servico2 = _oss_fake(os, tempo_executado_minutos=40)
        item = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[servico1, servico2]
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.FINALIZADA.value
        mock_uow.commit.assert_called_once()

    async def test_deve_ignorar_servico_cancelado_sem_tempo_ao_finalizar(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico_ativo = _oss_fake(os, tempo_executado_minutos=50)
        servico_cancelado = _oss_fake(os, cancelado=True, tempo_executado_minutos=None)
        item = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[servico_ativo, servico_cancelado]
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.FINALIZADA.value
        mock_uow.commit.assert_called_once()

    async def test_nao_deve_finalizar_os_inexistente(self, mock_uow):
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

        mock_uow.commit.assert_not_called()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    async def test_nao_deve_finalizar_os_fora_de_em_execucao(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_finalizar_com_servico_ativo_sem_tempo(self, mock_uow):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico_com_tempo = _oss_fake(os, tempo_executado_minutos=50)
        servico_sem_tempo = _oss_fake(os, tempo_executado_minutos=None)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[servico_com_tempo, servico_sem_tempo]
        )

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPossuiServicoSemTempoExecutadoError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        mock_uow.ordem_servico_repo.atualizar.assert_not_called()

    async def test_finalizar_nao_deve_consumir_itens(self, mock_uow):
        """Itens EM_USO permanecem EM_USO — não viram CONSUMIDO nesta fase."""
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, tempo_executado_minutos=60)
        item = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[servico])
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.FINALIZADA.value
        # item não deve ter sido atualizado (permanece EM_USO sem alteração)
        mock_uow.ordem_servico_repo.atualizar_item.assert_not_called()
        # validar que no response o item ainda aparece com status EM_USO
        assert resultado.itens[0].status == StatusItemNaOS.EM_USO.value

    async def test_finalizar_nao_deve_alterar_estoque(self, mock_uow):
        """item_estoque_repo não deve ser chamado ao finalizar OS."""
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico = _oss_fake(os, tempo_executado_minutos=60)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[servico])
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])

        # Sobrescreve o mock de estoque com um que NÃO levanta erro
        estoque_repo = MagicMock()
        estoque_repo.obter_por_id_com_lock = AsyncMock()
        estoque_repo.atualizar = AsyncMock()
        mock_uow.item_estoque_repo = estoque_repo

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id))

        estoque_repo.obter_por_id_com_lock.assert_not_called()
        estoque_repo.atualizar.assert_not_called()

    async def test_finalizar_os_sem_servicos_ativos(self, mock_uow):
        """OS sem serviços ativos (todos cancelados ou sem serviços) pode ser finalizada."""
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)
        servico_cancelado = _oss_fake(os, cancelado=True, tempo_executado_minutos=None)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[servico_cancelado]
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])

        uc = FinalizarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.FINALIZADA.value
        mock_uow.commit.assert_called_once()
