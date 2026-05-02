from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.modules.estoque.domain.entities.item_estoque import TipoItemEstoque


@dataclass(frozen=True, kw_only=True)
class CriarItemEstoqueRequest:
    tipo: TipoItemEstoque
    nome: str
    descricao: Optional[str] = None
    codigo: Optional[str] = None
    quantidade_disponivel: int = 0
    quantidade_minima: int = 0
    valor_unitario: Decimal


@dataclass(frozen=True, kw_only=True)
class ItemEstoqueResponse:
    id: str
    tipo: str
    nome: str
    descricao: Optional[str]
    codigo: Optional[str]
    quantidade_disponivel: int
    quantidade_reservada: int
    quantidade_minima: int
    valor_unitario: Decimal
    ativo: bool


@dataclass(frozen=True)
class AtualizarItemEstoque:
    tipo: Optional[TipoItemEstoque] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    codigo: Optional[str] = None
    quantidade_disponivel: Optional[int] = None
    quantidade_minima: Optional[int] = None
    valor_unitario: Optional[Decimal] = None

    def __post_init__(self) -> None:
        fields = [
            self.tipo,
            self.nome,
            self.descricao,
            self.codigo,
            self.quantidade_disponivel,
            self.quantidade_minima,
            self.valor_unitario,
        ]
        if all(f is None for f in fields):
            raise ValueError("Pelo menos um campo deve ser informado para atualização.")
