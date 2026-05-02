from dataclasses import dataclass
from typing import Optional

from app.modules.estoque.domain.entities.item_estoque import TipoItemEstoque


@dataclass(frozen=True)
class ListarItensEstoqueFiltro:
    tipo: Optional[TipoItemEstoque] = None
    nome: Optional[str] = None
    codigo: Optional[str] = None
    ativo: Optional[bool] = None
    baixo_estoque: Optional[bool] = None
