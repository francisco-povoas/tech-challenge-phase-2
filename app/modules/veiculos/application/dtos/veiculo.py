from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class CriarVeiculoRequest:
    placa: str
    marca: str
    modelo: str
    ano: int
    cliente_id: str


@dataclass(frozen=True, kw_only=True)
class VeiculoResponse:
    id: str
    placa: str
    marca: str
    modelo: str
    ano: int
    cliente_id: str


@dataclass(frozen=True)
class AtualizarVeiculo:
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
