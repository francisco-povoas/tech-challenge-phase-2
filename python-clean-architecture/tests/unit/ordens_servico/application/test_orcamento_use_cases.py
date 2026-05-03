"""Testes unitários para os use cases de orçamento do módulo ordens_servico."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.use_cases.gerar_orcamento import (
    GerarOrcamentoUseCase,
)
from app.modules.ordens_servico.application.use_cases.obter_orcamento_por_ordem_servico import (
    ObterOrcamentoPorOrdemServicoUseCase,
)
from app.modules.ordens_servico.application.use_cases.listar_comunicacoes_orcamento import (
    ListarComunicacoesOrcamentoUseCase,
)
from app.modules.ordens_servico.application.dtos.ordem_servico import GerarOrcamentoRequest
from app.modules.ordens_servico.domain.entities.ordem_servico import (
    OrdemServico,
    StatusOrdemServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento, StatusOrcamento
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import (
    CanalComunicacaoOrcamento,
    OrcamentoComunicacao,
)
from app.modules.ordens_servico.domain.exceptions import (
    ClienteSemContatoParaOrcamentoError,
    OrcamentoJaExisteParaOrdemServicoError,
    OrcamentoNaoEncontradoError,
    OrdemServicoInvalidaError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.shared.infra.notifications.notifier import ResultadoNotificacao


# ---------------------------------------------------------------------------
# Helpers / Fakes
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(
    status: StatusOrdemServico = StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
    cliente_id: str | None = None,
) -> OrdemServico:
    agora = _agora()
    return OrdemServico(
        id=ID.generate(),
        cliente_id=uuid4() if cliente_id is None else __import__("uuid").UUID(cliente_id),
        veiculo_id=uuid4(),
        status=status,
        queixa_inicial="Barulho no freio",
        diagnostico="Pastilhas desgastadas",
        criado_em=agora,
        atualizado_em=agora,
        iniciado_diagnostico_em=agora,
        diagnostico_concluido_em=agora,
    )


def _cliente_fake(
    email: str = "cliente@example.com",
    telefone: str = "11991234567",
) -> MagicMock:
    cliente = MagicMock()
    cliente.email = MagicMock()
    cliente.email.value = email
    cliente.telefone = MagicMock()
    cliente.telefone.value = telefone
    return cliente


def _os_servico_fake(
    ordem_servico_id: str | None = None,
    valor_unitario: Decimal = Decimal("180.00"),
    cancelado: bool = False,
) -> OrdemServicoServico:
    return OrdemServicoServico(
        id=ID.generate(),
        ordem_servico_id=uuid4() if ordem_servico_id is None else __import__("uuid").UUID(ordem_servico_id),
        servico_id=uuid4(),
        nome_servico="Alinhamento",
        descricao_servico=None,
        valor_unitario=valor_unitario,
        tempo_estimado_minutos=60,
        tempo_executado_minutos=None,
        observacao=None,
        cancelado=cancelado,
    )


def _os_item_fake(
    ordem_servico_id: str | None = None,
    status: StatusItemNaOS = StatusItemNaOS.RESERVADO,
    quantidade: int = 2,
    valor_unitario: Decimal = Decimal("85.00"),
) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=uuid4() if ordem_servico_id is None else __import__("uuid").UUID(ordem_servico_id),
        item_estoque_id=uuid4(),
        nome_item="Filtro de óleo",
        tipo_item="PECA",
        quantidade=quantidade,
        valor_unitario=valor_unitario,
        status=status,
    )


def _orcamento_fake(
    ordem_servico_id: str | None = None,
    status: StatusOrcamento = StatusOrcamento.COMUNICADO,
) -> Orcamento:
    agora = _agora()
    os_id = uuid4() if ordem_servico_id is None else __import__("uuid").UUID(ordem_servico_id)
    return Orcamento(
        id=ID.generate(),
        ordem_servico_id=os_id,
        status=status,
        total_servicos=Decimal("180.00"),
        total_itens=Decimal("390.00"),
        total_geral=Decimal("570.00"),
        criado_em=agora,
        atualizado_em=agora,
        comunicado_em=agora if status == StatusOrcamento.COMUNICADO else None,
        observacao=None,
    )


def _comunicacao_fake(
    canal: CanalComunicacaoOrcamento = CanalComunicacaoOrcamento.WHATSAPP,
    destino: str = "11991234567",
) -> OrcamentoComunicacao:
    agora = _agora()
    return OrcamentoComunicacao(
        id=ID.generate(),
        orcamento_id=uuid4(),
        ordem_servico_id=uuid4(),
        canal=canal,
        destino=destino,
        sucesso=True,
        mensagem="WhatsApp enviado" if canal == CanalComunicacaoOrcamento.WHATSAPP else "E-mail enviado",
        provedor="mock",
        referencia_externa=None,
        enviado_em=agora,
        criado_em=agora,
    )


def _resultado_notificacao_fake(canal: str = "WHATSAPP") -> ResultadoNotificacao:
    return ResultadoNotificacao(
        canal=canal,
        sucesso=True,
        mensagem="WhatsApp enviado" if canal == "WHATSAPP" else "E-mail enviado",
        enviado_em=_agora(),
        provedor="mock",
        referencia_externa=None,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_os_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.atualizar = AsyncMock()
    repo.listar_servicos_da_os = AsyncMock(return_value=[])
    repo.listar_itens_da_os = AsyncMock(return_value=[])
    repo.orcamento_existe_para_os = AsyncMock(return_value=False)
    repo.salvar_orcamento = AsyncMock()
    repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=None)
    repo.atualizar_orcamento = AsyncMock()
    repo.salvar_comunicacao = AsyncMock()
    repo.listar_comunicacoes_por_ordem_servico_id = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_item_estoque_repo():
    repo = MagicMock()
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


@pytest.fixture
def mock_cliente_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=_cliente_fake())
    return repo


@pytest.fixture
def mock_whatsapp_notifier():
    notifier = MagicMock()
    notifier.enviar_orcamento = AsyncMock(return_value=_resultado_notificacao_fake("WHATSAPP"))
    return notifier


@pytest.fixture
def mock_email_notifier():
    notifier = MagicMock()
    notifier.enviar_orcamento = AsyncMock(return_value=_resultado_notificacao_fake("EMAIL"))
    return notifier


def _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier):
    return GerarOrcamentoUseCase(
        uow=mock_uow,
        cliente_repo=mock_cliente_repo,
        whatsapp_notifier=mock_whatsapp_notifier,
        email_notifier=mock_email_notifier,
    )


# ---------------------------------------------------------------------------
# GerarOrcamentoUseCase
# ---------------------------------------------------------------------------

class TestGerarOrcamentoUseCase:
    async def test_deve_gerar_orcamento_com_sucesso(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        servico = _os_servico_fake(valor_unitario=Decimal("180.00"))
        item_reservado = _os_item_fake(
            status=StatusItemNaOS.RESERVADO,
            quantidade=2,
            valor_unitario=Decimal("85.00"),
        )
        item_a_receber = _os_item_fake(
            status=StatusItemNaOS.A_RECEBER,
            quantidade=1,
            valor_unitario=Decimal("220.00"),
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[servico])
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_reservado, item_a_receber]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrcamento.COMUNICADO.value
        assert resultado.total_servicos == Decimal("180.00")
        assert resultado.total_itens == Decimal("390.00")   # 2*85 + 1*220
        assert resultado.total_geral == Decimal("570.00")
        assert resultado.comunicado_em is not None
        assert len(resultado.comunicacoes) == 2

        canais = {c.canal for c in resultado.comunicacoes}
        assert CanalComunicacaoOrcamento.WHATSAPP.value in canais
        assert CanalComunicacaoOrcamento.EMAIL.value in canais

        mock_uow.ordem_servico_repo.salvar_orcamento.assert_called_once()
        mock_uow.ordem_servico_repo.atualizar.assert_called_once()
        mock_whatsapp_notifier.enviar_orcamento.assert_called_once()
        mock_email_notifier.enviar_orcamento.assert_called_once()

    async def test_deve_ignorar_servicos_cancelados_no_total(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        servico_ativo = _os_servico_fake(valor_unitario=Decimal("180.00"), cancelado=False)
        servico_cancelado = _os_servico_fake(valor_unitario=Decimal("999.00"), cancelado=True)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[servico_ativo, servico_cancelado]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        assert resultado.total_servicos == Decimal("180.00")
        assert resultado.total_geral == Decimal("180.00")

    async def test_deve_ignorar_itens_cancelados_no_total(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        servico = _os_servico_fake(valor_unitario=Decimal("0.00"))
        item_ativo = _os_item_fake(
            status=StatusItemNaOS.RESERVADO,
            quantidade=2,
            valor_unitario=Decimal("85.00"),
        )
        item_cancelado = _os_item_fake(
            status=StatusItemNaOS.CANCELADO,
            quantidade=1,
            valor_unitario=Decimal("999.00"),
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[servico])
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_ativo, item_cancelado]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        assert resultado.total_itens == Decimal("170.00")   # 2*85, cancelado ignorado

    async def test_deve_considerar_item_a_receber_no_total(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        servico = _os_servico_fake(valor_unitario=Decimal("0.00"))
        item_a_receber = _os_item_fake(
            status=StatusItemNaOS.A_RECEBER,
            quantidade=1,
            valor_unitario=Decimal("220.00"),
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[servico])
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item_a_receber])

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        assert resultado.total_itens == Decimal("220.00")

    async def test_nao_deve_gerar_orcamento_para_os_inexistente(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

        mock_whatsapp_notifier.enviar_orcamento.assert_not_called()
        mock_email_notifier.enviar_orcamento.assert_not_called()
        mock_uow.ordem_servico_repo.salvar_orcamento.assert_not_called()

    @pytest.mark.parametrize("status_invalido", [
        StatusOrdemServico.RECEBIDA,
        StatusOrdemServico.EM_DIAGNOSTICO,
        StatusOrdemServico.AGUARDANDO_APROVACAO,
        StatusOrdemServico.APROVADA,
    ])
    async def test_nao_deve_gerar_orcamento_com_status_invalido(
        self,
        status_invalido,
        mock_uow,
        mock_cliente_repo,
        mock_whatsapp_notifier,
        mock_email_notifier,
    ):
        os = _os_fake(status=status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id))

        mock_whatsapp_notifier.enviar_orcamento.assert_not_called()
        mock_uow.ordem_servico_repo.salvar_orcamento.assert_not_called()

    async def test_nao_deve_gerar_orcamento_se_ja_existir_orcamento(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.orcamento_existe_para_os = AsyncMock(return_value=True)

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(OrcamentoJaExisteParaOrdemServicoError):
            await uc.execute(str(os.id))

        mock_whatsapp_notifier.enviar_orcamento.assert_not_called()
        mock_email_notifier.enviar_orcamento.assert_not_called()
        mock_uow.ordem_servico_repo.salvar_orcamento.assert_not_called()

    async def test_nao_deve_gerar_orcamento_sem_cliente(
        self, mock_uow, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        cliente_repo = MagicMock()
        cliente_repo.obter_por_id = AsyncMock(return_value=None)

        uc = _uc_gerar(mock_uow, cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(OrdemServicoInvalidaError):
            await uc.execute(str(os.id))

        mock_whatsapp_notifier.enviar_orcamento.assert_not_called()

    async def test_nao_deve_gerar_orcamento_se_cliente_nao_tem_email(
        self, mock_uow, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        cliente_sem_email = MagicMock()
        cliente_sem_email.email = None
        cliente_sem_email.telefone = MagicMock()
        cliente_sem_email.telefone.value = "11999999999"
        cliente_repo = MagicMock()
        cliente_repo.obter_por_id = AsyncMock(return_value=cliente_sem_email)

        uc = _uc_gerar(mock_uow, cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(ClienteSemContatoParaOrcamentoError):
            await uc.execute(str(os.id))

        mock_whatsapp_notifier.enviar_orcamento.assert_not_called()

    async def test_nao_deve_gerar_orcamento_se_cliente_nao_tem_telefone(
        self, mock_uow, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        cliente_sem_telefone = MagicMock()
        cliente_sem_telefone.email = MagicMock()
        cliente_sem_telefone.email.value = "user@example.com"
        cliente_sem_telefone.telefone = None
        cliente_repo = MagicMock()
        cliente_repo.obter_por_id = AsyncMock(return_value=cliente_sem_telefone)

        uc = _uc_gerar(mock_uow, cliente_repo, mock_whatsapp_notifier, mock_email_notifier)

        with pytest.raises(ClienteSemContatoParaOrcamentoError):
            await uc.execute(str(os.id))

        mock_email_notifier.enviar_orcamento.assert_not_called()

    async def test_deve_registrar_comunicacao_whatsapp_com_destino_telefone(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        com_whatsapp = next(
            c for c in resultado.comunicacoes if c.canal == CanalComunicacaoOrcamento.WHATSAPP.value
        )
        assert com_whatsapp.destino == "11991234567"

    async def test_deve_registrar_comunicacao_email_com_destino_email(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        com_email = next(
            c for c in resultado.comunicacoes if c.canal == CanalComunicacaoOrcamento.EMAIL.value
        )
        assert com_email.destino == "cliente@example.com"

    async def test_nao_deve_alterar_os_se_whatsapp_falhar(
        self, mock_uow, mock_cliente_repo, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        whatsapp_falhou = MagicMock()
        whatsapp_falhou.enviar_orcamento = AsyncMock(
            return_value=ResultadoNotificacao(
                canal="WHATSAPP",
                sucesso=False,
                mensagem="Erro ao enviar",
                enviado_em=_agora(),
                provedor="mock",
                referencia_externa=None,
            )
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, whatsapp_falhou, mock_email_notifier)
        resultado = await uc.execute(str(os.id))

        # OS não deve ter sido atualizada para AGUARDANDO_APROVACAO
        mock_uow.ordem_servico_repo.atualizar.assert_not_called()
        # orçamento deve ter sido salvo mas não como COMUNICADO
        assert resultado.status == StatusOrcamento.GERADO.value
        assert resultado.comunicado_em is None

    async def test_nao_deve_alterar_os_se_email_falhar(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        email_falhou = MagicMock()
        email_falhou.enviar_orcamento = AsyncMock(
            return_value=ResultadoNotificacao(
                canal="EMAIL",
                sucesso=False,
                mensagem="Erro ao enviar",
                enviado_em=_agora(),
                provedor="mock",
                referencia_externa=None,
            )
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, email_falhou)
        resultado = await uc.execute(str(os.id))

        mock_uow.ordem_servico_repo.atualizar.assert_not_called()
        assert resultado.status == StatusOrcamento.GERADO.value

    async def test_deve_persistir_orcamento_antes_das_comunicacoes(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        """Garante que salvar_orcamento é chamado antes de salvar_comunicacao."""
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        call_order: list[str] = []

        async def salvar_orcamento_spy(orc):
            call_order.append("salvar_orcamento")

        async def salvar_comunicacao_spy(com):
            call_order.append("salvar_comunicacao")

        mock_uow.ordem_servico_repo.salvar_orcamento = salvar_orcamento_spy
        mock_uow.ordem_servico_repo.salvar_comunicacao = salvar_comunicacao_spy

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        await uc.execute(str(os.id))

        assert call_order[0] == "salvar_orcamento"
        assert call_order.count("salvar_comunicacao") == 2

    async def test_deve_gerar_orcamento_com_observacao(
        self, mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier
    ):
        os = _os_fake()
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(
            return_value=[_os_servico_fake()]
        )

        uc = _uc_gerar(mock_uow, mock_cliente_repo, mock_whatsapp_notifier, mock_email_notifier)
        dto = GerarOrcamentoRequest(observacao="Observação de teste")
        resultado = await uc.execute(str(os.id), dto)

        assert resultado.observacao == "Observação de teste"


# ---------------------------------------------------------------------------
# ObterOrcamentoPorOrdemServicoUseCase
# ---------------------------------------------------------------------------

class TestObterOrcamentoPorOrdemServicoUseCase:
    async def test_deve_obter_orcamento_por_ordem_servico(self, mock_os_repo):
        os = _os_fake()
        orc = _orcamento_fake(ordem_servico_id=str(os.id.value))
        comunicacoes = [
            _comunicacao_fake(CanalComunicacaoOrcamento.WHATSAPP),
            _comunicacao_fake(CanalComunicacaoOrcamento.EMAIL, destino="user@example.com"),
        ]
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=orc)
        mock_os_repo.listar_comunicacoes_por_ordem_servico_id = AsyncMock(return_value=comunicacoes)

        uc = ObterOrcamentoPorOrdemServicoUseCase(ordem_servico_repo=mock_os_repo)
        resultado = await uc.execute(str(os.id))

        assert resultado.id == str(orc.id)
        assert resultado.ordem_servico_id == str(orc.ordem_servico_id)
        assert resultado.status == StatusOrcamento.COMUNICADO.value
        assert resultado.total_servicos == Decimal("180.00")
        assert resultado.total_itens == Decimal("390.00")
        assert resultado.total_geral == Decimal("570.00")
        assert resultado.comunicado_em is not None
        assert len(resultado.comunicacoes) == 2

    async def test_deve_retornar_erro_quando_os_nao_existe(self, mock_os_repo):
        uc = ObterOrcamentoPorOrdemServicoUseCase(ordem_servico_repo=mock_os_repo)
        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

    async def test_deve_retornar_erro_quando_orcamento_nao_existe(self, mock_os_repo):
        os = _os_fake()
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=None)

        uc = ObterOrcamentoPorOrdemServicoUseCase(ordem_servico_repo=mock_os_repo)
        with pytest.raises(OrcamentoNaoEncontradoError):
            await uc.execute(str(os.id))

    async def test_deve_incluir_comunicacoes_no_retorno(self, mock_os_repo):
        os = _os_fake()
        orc = _orcamento_fake()
        comunicacoes = [
            _comunicacao_fake(CanalComunicacaoOrcamento.WHATSAPP),
            _comunicacao_fake(CanalComunicacaoOrcamento.EMAIL),
        ]
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=orc)
        mock_os_repo.listar_comunicacoes_por_ordem_servico_id = AsyncMock(return_value=comunicacoes)

        uc = ObterOrcamentoPorOrdemServicoUseCase(ordem_servico_repo=mock_os_repo)
        resultado = await uc.execute(str(os.id))

        assert len(resultado.comunicacoes) == 2
        canais = {c.canal for c in resultado.comunicacoes}
        assert "WHATSAPP" in canais
        assert "EMAIL" in canais


# ---------------------------------------------------------------------------
# ListarComunicacoesOrcamentoUseCase
# ---------------------------------------------------------------------------

class TestListarComunicacoesOrcamentoUseCase:
    async def test_deve_listar_comunicacoes_do_orcamento(self, mock_os_repo):
        os = _os_fake()
        orc = _orcamento_fake()
        com_whatsapp = _comunicacao_fake(
            CanalComunicacaoOrcamento.WHATSAPP, destino="11991234567"
        )
        com_email = _comunicacao_fake(
            CanalComunicacaoOrcamento.EMAIL, destino="user@example.com"
        )
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=orc)
        mock_os_repo.listar_comunicacoes_por_ordem_servico_id = AsyncMock(
            return_value=[com_whatsapp, com_email]
        )

        uc = ListarComunicacoesOrcamentoUseCase(ordem_servico_repo=mock_os_repo)
        resultado = await uc.execute(str(os.id))

        assert len(resultado) == 2

        res_whatsapp = next(r for r in resultado if r.canal == "WHATSAPP")
        assert res_whatsapp.destino == "11991234567"
        assert res_whatsapp.sucesso is True
        assert res_whatsapp.mensagem == "WhatsApp enviado"
        assert res_whatsapp.provedor == "mock"

        res_email = next(r for r in resultado if r.canal == "EMAIL")
        assert res_email.destino == "user@example.com"
        assert res_email.sucesso is True
        assert res_email.mensagem == "E-mail enviado"

    async def test_deve_retornar_lista_vazia_quando_sem_comunicacoes(self, mock_os_repo):
        os = _os_fake()
        orc = _orcamento_fake()
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=orc)
        mock_os_repo.listar_comunicacoes_por_ordem_servico_id = AsyncMock(return_value=[])

        uc = ListarComunicacoesOrcamentoUseCase(ordem_servico_repo=mock_os_repo)
        resultado = await uc.execute(str(os.id))

        assert resultado == []

    async def test_deve_retornar_erro_quando_os_nao_existe(self, mock_os_repo):
        uc = ListarComunicacoesOrcamentoUseCase(ordem_servico_repo=mock_os_repo)
        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

    async def test_deve_retornar_erro_quando_orcamento_nao_existe(self, mock_os_repo):
        os = _os_fake()
        mock_os_repo.obter_por_id = AsyncMock(return_value=os)
        mock_os_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=None)

        uc = ListarComunicacoesOrcamentoUseCase(ordem_servico_repo=mock_os_repo)
        with pytest.raises(OrcamentoNaoEncontradoError):
            await uc.execute(str(os.id))
