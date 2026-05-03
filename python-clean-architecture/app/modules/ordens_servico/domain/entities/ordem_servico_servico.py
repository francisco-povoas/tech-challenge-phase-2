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

    def registrar_tempo_executado(self, tempo_executado_minutos: int) -> "OrdemServicoServico":
        """Registra (ou sobrescreve) o tempo executado do serviço.

        Retorna nova instância com tempo_executado_minutos atualizado.
        Lança OrdemServicoServicoCanceladoError se o serviço estiver cancelado.
        Lança TempoExecutadoInvalidoError se o tempo for <= 0.
        """
        from app.modules.ordens_servico.domain.exceptions import (
            OrdemServicoServicoCanceladoError,
            TempoExecutadoInvalidoError,
        )

        if self.cancelado:
            raise OrdemServicoServicoCanceladoError(
                "Não é possível registrar tempo executado em serviço cancelado."
            )
        if tempo_executado_minutos <= 0:
            raise TempoExecutadoInvalidoError(
                "Tempo executado deve ser maior que zero."
            )
        return OrdemServicoServico(
            id=self.id,
            ordem_servico_id=self.ordem_servico_id,
            servico_id=self.servico_id,
            nome_servico=self.nome_servico,
            descricao_servico=self.descricao_servico,
            valor_unitario=self.valor_unitario,
            tempo_estimado_minutos=self.tempo_estimado_minutos,
            tempo_executado_minutos=tempo_executado_minutos,
            observacao=self.observacao,
            cancelado=self.cancelado,
        )
