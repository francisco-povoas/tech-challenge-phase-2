"""Implementações mockadas dos notificadores de orçamento."""

from datetime import UTC, datetime
from uuid import UUID

from app.shared.infra.notifications.notifier import ResultadoNotificacao


class MockWhatsAppNotifier:
    """Notificador WhatsApp mockado — não envia nada real."""

    async def enviar_orcamento(
        self,
        *,
        ordem_servico_id: UUID,
        orcamento_id: UUID,
        destino: str,
        total_geral: str,
    ) -> ResultadoNotificacao:
        return ResultadoNotificacao(
            canal="WHATSAPP",
            sucesso=True,
            mensagem="WhatsApp enviado",
            enviado_em=datetime.now(UTC),
            provedor="mock",
            referencia_externa=None,
        )


class MockEmailNotifier:
    """Notificador e-mail mockado — não envia nada real."""

    async def enviar_orcamento(
        self,
        *,
        ordem_servico_id: UUID,
        orcamento_id: UUID,
        destino: str,
        total_geral: str,
    ) -> ResultadoNotificacao:
        return ResultadoNotificacao(
            canal="EMAIL",
            sucesso=True,
            mensagem="E-mail enviado",
            enviado_em=datetime.now(UTC),
            provedor="mock",
            referencia_externa=None,
        )
