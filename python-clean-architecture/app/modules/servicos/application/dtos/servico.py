from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class CriarServicoRequest:
    nome: str
    descricao: Optional[str] = None
    valor_base: Decimal
    tempo_medio_minutos: int


@dataclass(frozen=True, kw_only=True)
class ServicoResponse:
    id: str
    nome: str
    descricao: Optional[str]
    valor_base: Decimal
    tempo_medio_minutos: int
    ativo: bool


@dataclass(frozen=True)
class AtualizarServico:
    nome: Optional[str] = None
    descricao: Optional[str] = None
    valor_base: Optional[Decimal] = None
    tempo_medio_minutos: Optional[int] = None

    def __post_init__(self) -> None:
        fields = [
            self.nome,
            self.descricao,
            self.valor_base,
            self.tempo_medio_minutos,
        ]
        if all(f is None for f in fields):
            raise ValueError("Pelo menos um campo deve ser informado para atualização.")
