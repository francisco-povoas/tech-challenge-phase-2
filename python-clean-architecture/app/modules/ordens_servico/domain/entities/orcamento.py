"""Entidade de domínio: Orçamento de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.exceptions import OrcamentoInvalidoError


class StatusOrcamento(str, Enum):
    """Status possíveis de um Orçamento."""

    GERADO = "GERADO"
    COMUNICADO = "COMUNICADO"
    APROVADO = "APROVADO"      # futuro
    RECUSADO = "RECUSADO"      # futuro


@dataclass(frozen=True, kw_only=True)
class Orcamento:
    """Representa o orçamento gerado a partir do diagnóstico de uma OS."""

    id: ID
    ordem_servico_id: UUID
    status: StatusOrcamento
    total_servicos: Decimal
    total_itens: Decimal
    total_geral: Decimal
    criado_em: datetime
    atualizado_em: datetime
    comunicado_em: Optional[datetime]
    observacao: Optional[str]

    def __post_init__(self) -> None:
        if self.total_servicos < Decimal("0"):
            raise OrcamentoInvalidoError("total_servicos não pode ser negativo.")
        if self.total_itens < Decimal("0"):
            raise OrcamentoInvalidoError("total_itens não pode ser negativo.")
        esperado = self.total_servicos + self.total_itens
        if self.total_geral != esperado:
            raise OrcamentoInvalidoError(
                f"total_geral ({self.total_geral}) deve ser igual a "
                f"total_servicos + total_itens ({esperado})."
            )

    def marcar_como_comunicado(self, comunicado_em: datetime) -> "Orcamento":
        """Retorna novo Orcamento com status COMUNICADO."""
        return Orcamento(
            id=self.id,
            ordem_servico_id=self.ordem_servico_id,
            status=StatusOrcamento.COMUNICADO,
            total_servicos=self.total_servicos,
            total_itens=self.total_itens,
            total_geral=self.total_geral,
            criado_em=self.criado_em,
            atualizado_em=comunicado_em,
            comunicado_em=comunicado_em,
            observacao=self.observacao,
        )
