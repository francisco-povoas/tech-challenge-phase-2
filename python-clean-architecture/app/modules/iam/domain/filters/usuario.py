from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListarUsuariosFiltro:
    nome: Optional[str] = None
    email: Optional[str] = None
    ativo: Optional[bool] = None
