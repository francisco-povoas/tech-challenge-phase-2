from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListarServicosFiltro:
    nome: Optional[str] = None
    ativo: Optional[bool] = None
