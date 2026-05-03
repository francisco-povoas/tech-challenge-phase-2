"""Entidade de domínio: registro de comunicação de um Orçamento."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from app.shared.value_objects.id import ID


class CanalComunicacaoOrcamento(str, Enum):
    """Canal pelo qual o orçamento foi comunicado ao cliente."""

    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"


@dataclass(frozen=True, kw_only=True)
class OrcamentoComunicacao:
    """Evidência de envio do orçamento ao cliente por um canal específico."""

    id: ID
    orcamento_id: UUID
    ordem_servico_id: UUID
    canal: CanalComunicacaoOrcamento
    destino: str          # telefone ou e-mail do cliente
    sucesso: bool
    mensagem: str
    provedor: str
    referencia_externa: Optional[str]
    enviado_em: datetime
    criado_em: datetime
