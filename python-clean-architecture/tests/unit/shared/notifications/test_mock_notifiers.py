"""Testes unitários para os notificadores mockados de orçamento."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.shared.infra.notifications.mock_notifiers import (
    MockEmailNotifier,
    MockWhatsAppNotifier,
)
from app.shared.infra.notifications.notifier import ResultadoNotificacao


# ---------------------------------------------------------------------------
# MockWhatsAppNotifier
# ---------------------------------------------------------------------------

class TestMockWhatsAppNotifier:
    async def test_deve_enviar_orcamento_com_sucesso(self):
        notifier = MockWhatsAppNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="11991234567",
            total_geral="570.00",
        )

        assert isinstance(resultado, ResultadoNotificacao)
        assert resultado.sucesso is True
        assert resultado.canal == "WHATSAPP"
        assert resultado.mensagem == "WhatsApp enviado"
        assert resultado.provedor == "mock"
        assert resultado.referencia_externa is None
        assert isinstance(resultado.enviado_em, datetime)

    async def test_deve_preencher_enviado_em(self):
        notifier = MockWhatsAppNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="11991234567",
            total_geral="100.00",
        )
        assert resultado.enviado_em is not None

    async def test_deve_retornar_referencia_externa_none(self):
        notifier = MockWhatsAppNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="11999999999",
            total_geral="0.00",
        )
        assert resultado.referencia_externa is None

    async def test_deve_aceitar_ids_distintos(self):
        notifier = MockWhatsAppNotifier()
        os_id = uuid4()
        orc_id = uuid4()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=os_id,
            orcamento_id=orc_id,
            destino="11900000000",
            total_geral="250.00",
        )
        assert resultado.sucesso is True


# ---------------------------------------------------------------------------
# MockEmailNotifier
# ---------------------------------------------------------------------------

class TestMockEmailNotifier:
    async def test_deve_enviar_orcamento_com_sucesso(self):
        notifier = MockEmailNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="cliente@example.com",
            total_geral="570.00",
        )

        assert isinstance(resultado, ResultadoNotificacao)
        assert resultado.sucesso is True
        assert resultado.canal == "EMAIL"
        assert resultado.mensagem == "E-mail enviado"
        assert resultado.provedor == "mock"
        assert resultado.referencia_externa is None
        assert isinstance(resultado.enviado_em, datetime)

    async def test_deve_preencher_enviado_em(self):
        notifier = MockEmailNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="test@test.com",
            total_geral="100.00",
        )
        assert resultado.enviado_em is not None

    async def test_deve_retornar_referencia_externa_none(self):
        notifier = MockEmailNotifier()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=uuid4(),
            orcamento_id=uuid4(),
            destino="a@b.com",
            total_geral="0.00",
        )
        assert resultado.referencia_externa is None

    async def test_deve_aceitar_ids_distintos(self):
        notifier = MockEmailNotifier()
        os_id = uuid4()
        orc_id = uuid4()
        resultado = await notifier.enviar_orcamento(
            ordem_servico_id=os_id,
            orcamento_id=orc_id,
            destino="another@example.com",
            total_geral="999.99",
        )
        assert resultado.sucesso is True


# ---------------------------------------------------------------------------
# ResultadoNotificacao dataclass
# ---------------------------------------------------------------------------

class TestResultadoNotificacao:
    def test_deve_criar_resultado_com_todos_os_campos(self):
        agora = datetime.now()
        resultado = ResultadoNotificacao(
            canal="WHATSAPP",
            sucesso=True,
            mensagem="ok",
            enviado_em=agora,
            provedor="mock",
            referencia_externa="ref-001",
        )
        assert resultado.canal == "WHATSAPP"
        assert resultado.sucesso is True
        assert resultado.mensagem == "ok"
        assert resultado.enviado_em == agora
        assert resultado.provedor == "mock"
        assert resultado.referencia_externa == "ref-001"

    def test_referencia_externa_default_none(self):
        resultado = ResultadoNotificacao(
            canal="EMAIL",
            sucesso=False,
            mensagem="falhou",
            enviado_em=datetime.now(),
            provedor="mock",
        )
        assert resultado.referencia_externa is None
