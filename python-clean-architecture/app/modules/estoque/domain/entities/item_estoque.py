from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.shared.value_objects.id import ID
from app.modules.estoque.domain.exceptions import ItemEstoqueInvalidoError


class TipoItemEstoque(str, Enum):
    PECA = "PECA"
    INSUMO = "INSUMO"


@dataclass(frozen=True, kw_only=True)
class ItemEstoque:
    """Entidade de domínio representando um item de estoque (peça ou insumo)."""

    id: ID
    tipo: TipoItemEstoque
    nome: str
    descricao: Optional[str]
    codigo: Optional[str]
    quantidade_disponivel: int
    quantidade_reservada: int
    quantidade_minima: int
    valor_unitario: Decimal
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ItemEstoqueInvalidoError("O nome do item de estoque não pode ser vazio.")

        if len(self.nome) > 100:
            raise ItemEstoqueInvalidoError(
                "O nome do item de estoque deve ter no máximo 100 caracteres."
            )

        if self.descricao is not None and len(self.descricao) > 255:
            raise ItemEstoqueInvalidoError(
                "A descrição do item de estoque deve ter no máximo 255 caracteres."
            )

        if self.codigo is not None and len(self.codigo) > 50:
            raise ItemEstoqueInvalidoError(
                "O código do item de estoque deve ter no máximo 50 caracteres."
            )

        if self.quantidade_disponivel < 0:
            raise ItemEstoqueInvalidoError(
                "A quantidade disponível não pode ser negativa."
            )

        if self.quantidade_reservada < 0:
            raise ItemEstoqueInvalidoError(
                "A quantidade reservada não pode ser negativa."
            )

        if self.quantidade_minima < 0:
            raise ItemEstoqueInvalidoError(
                "A quantidade mínima não pode ser negativa."
            )

        if self.valor_unitario < Decimal("0"):
            raise ItemEstoqueInvalidoError(
                "O valor unitário do item não pode ser negativo."
            )
