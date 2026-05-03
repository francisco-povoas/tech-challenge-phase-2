"""Abstrações (ports) para notificação de orçamento ao cliente."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol
from uuid import UUID


@dataclass(frozen=True)
class ResultadoNotificacao:
    """Resultado do envio de uma notificação de orçamento."""

    canal: str
    sucesso: bool
    mensagem: str
    enviado_em: datetime
    provedor: str
    referencia_externa: Optional[str] = None


class WhatsAppNotifier(Protocol):
    """Port de envio de orçamento por WhatsApp."""

    async def enviar_orcamento(
        self,
        *,
        ordem_servico_id: UUID,
        orcamento_id: UUID,
        destino: str,
        total_geral: str,
    ) -> ResultadoNotificacao: ...


class EmailNotifier(Protocol):
    """Port de envio de orçamento por e-mail."""

    async def enviar_orcamento(
        self,
        *,
        ordem_servico_id: UUID,
        orcamento_id: UUID,
        destino: str,
        total_geral: str,
    ) -> ResultadoNotificacao: ...
