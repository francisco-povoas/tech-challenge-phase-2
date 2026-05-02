from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ListarClientesFiltro:
    nome: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    ativo: Optional[bool] = None
