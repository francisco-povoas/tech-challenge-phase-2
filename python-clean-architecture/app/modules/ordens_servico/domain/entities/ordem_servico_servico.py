"""Entidade de domínio: vínculo de serviço em uma Ordem de Serviço."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.exceptions import OrdemServicoInvalidaError


@dataclass(frozen=True, kw_only=True)
class OrdemServicoServico:
    """Representa um serviço vinculado a uma Ordem de Serviço.

    Guarda snapshot do serviço no momento da inclusão.
    """

    id: ID
    ordem_servico_id: UUID
    servico_id: UUID
    nome_servico: str
    descricao_servico: Optional[str]
    valor_unitario: Decimal
    tempo_estimado_minutos: int
    tempo_executado_minutos: Optional[int]  # futuro — registro de execução
    observacao: Optional[str]
    cancelado: bool

    def __post_init__(self) -> None:
        if not self.nome_servico or not self.nome_servico.strip():
            raise OrdemServicoInvalidaError("O nome do serviço não pode ser vazio.")
        if self.valor_unitario < Decimal("0"):
            raise OrdemServicoInvalidaError("O valor unitário do serviço não pode ser negativo.")
        if self.tempo_estimado_minutos <= 0:
            raise OrdemServicoInvalidaError("O tempo estimado do serviço deve ser maior que zero.")
