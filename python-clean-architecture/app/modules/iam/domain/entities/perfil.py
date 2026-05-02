from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import StrEnum
import datetime

from app.shared.exceptions import DomainException
from app.shared.value_objects.id import ID

class InvalidPerfilError(DomainException):
    pass


class PerfilTipos(StrEnum):
    ATENDENTE = "Atendente"
    MECANICO = "Mecanico"
    ADMINISTRADOR = "Administrador"

    @classmethod
    def tipos(cls):
        return [cls.ATENDENTE.value, cls.MECANICO.value, cls.ADMINISTRADOR.value]

@dataclass(frozen=True, kw_only=True)
class Perfil:
    """Entidade de domínio representando um perfil do sistema."""

    id: ID
    nome: str
    descricao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    def __post_init__(self):
        if not self.nome or not self.nome.strip():
            raise InvalidPerfilError("O nome do perfil não pode ser vazio")
        if self.nome not in PerfilTipos.tipos():
            raise InvalidPerfilError(f"O nome do perfil deve ser um dos seguintes: {', '.join(PerfilTipos.tipos())}")