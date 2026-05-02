from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ListarVeiculosFiltro:
    cliente_id: Optional[UUID] = None
    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
