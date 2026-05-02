from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class CriarVeiculoRequest:
    cliente_id: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: Optional[int] = None
    ano_modelo: Optional[int] = None
    cor: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class VeiculoResponse:
    id: str
    cliente_id: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: Optional[int]
    ano_modelo: Optional[int]
    cor: Optional[str]


@dataclass(frozen=True)
class AtualizarVeiculo:
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano_fabricacao: Optional[int] = None
    ano_modelo: Optional[int] = None
    cor: Optional[str] = None

    def __post_init__(self) -> None:
        fields = [
            self.marca,
            self.modelo,
            self.ano_fabricacao,
            self.ano_modelo,
            self.cor,
        ]
        if all(f is None for f in fields):
            raise ValueError("Pelo menos um campo deve ser informado para atualização.")
