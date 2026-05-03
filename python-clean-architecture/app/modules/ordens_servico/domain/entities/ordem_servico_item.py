"""Entidade de domínio: vínculo de item de estoque em uma Ordem de Serviço."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.exceptions import OrdemServicoInvalidaError


class StatusItemNaOS(str, Enum):
    """Status de um item de estoque vinculado a uma OS."""

    # Etapa 1 — implementados
    RESERVADO = "RESERVADO"   # quantidade separada no estoque para a OS
    A_RECEBER = "A_RECEBER"   # OS precisa do item, mas não havia saldo disponível
    CANCELADO = "CANCELADO"   # item deixou de ser necessário na OS

    # Etapas futuras
    EM_USO = "EM_USO"         # futuro — item entrou em uso na execução
    CONSUMIDO = "CONSUMIDO"   # futuro — item foi consumido definitivamente


@dataclass(frozen=True, kw_only=True)
class OrdemServicoItem:
    """Representa um item de estoque vinculado a uma Ordem de Serviço.

    Guarda snapshot do item no momento da inclusão.
    O status operacional fica neste vínculo, não no ItemEstoque.
    """

    id: ID
    ordem_servico_id: UUID
    item_estoque_id: UUID
    nome_item: str
    tipo_item: str
    quantidade: int
    valor_unitario: Decimal
    status: StatusItemNaOS

    def __post_init__(self) -> None:
        if not self.nome_item or not self.nome_item.strip():
            raise OrdemServicoInvalidaError("O nome do item não pode ser vazio.")
        if self.quantidade <= 0:
            raise OrdemServicoInvalidaError("A quantidade do item deve ser maior que zero.")
        if self.valor_unitario < Decimal("0"):
            raise OrdemServicoInvalidaError("O valor unitário do item não pode ser negativo.")

    def confirmar_recebimento(self) -> "OrdemServicoItem":
        """Confirma recebimento do item (A_RECEBER -> RESERVADO).

        Retorna nova instância com status RESERVADO.
        Lança ItemOrdemServicoStatusInvalidoError se o item não estiver A_RECEBER.
        """
        from app.modules.ordens_servico.domain.exceptions import ItemOrdemServicoStatusInvalidoError

        if self.status != StatusItemNaOS.A_RECEBER:
            raise ItemOrdemServicoStatusInvalidoError(
                f"Só é possível confirmar recebimento de item com status "
                f"'A_RECEBER'. Status atual: '{self.status.value}'."
            )
        return OrdemServicoItem(
            id=self.id,
            ordem_servico_id=self.ordem_servico_id,
            item_estoque_id=self.item_estoque_id,
            nome_item=self.nome_item,
            tipo_item=self.tipo_item,
            quantidade=self.quantidade,
            valor_unitario=self.valor_unitario,
            status=StatusItemNaOS.RESERVADO,
        )

    def colocar_em_uso(self) -> "OrdemServicoItem":
        """Coloca item em uso (RESERVADO -> EM_USO).

        Retorna nova instância com status EM_USO.
        Lança ItemOrdemServicoStatusInvalidoError se o item não estiver RESERVADO.
        """
        from app.modules.ordens_servico.domain.exceptions import ItemOrdemServicoStatusInvalidoError

        if self.status != StatusItemNaOS.RESERVADO:
            raise ItemOrdemServicoStatusInvalidoError(
                f"Só é possível colocar em uso item com status 'RESERVADO'. "
                f"Status atual: '{self.status.value}'."
            )
        return OrdemServicoItem(
            id=self.id,
            ordem_servico_id=self.ordem_servico_id,
            item_estoque_id=self.item_estoque_id,
            nome_item=self.nome_item,
            tipo_item=self.tipo_item,
            quantidade=self.quantidade,
            valor_unitario=self.valor_unitario,
            status=StatusItemNaOS.EM_USO,
        )
