from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import datetime

from app.shared.exceptions import DomainException
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.shared.value_objects.password import Password

class InvalidUsuarioError(DomainException):
    pass

@dataclass(frozen=True, kw_only=True)
class Usuario:
    """Entidade de domínio representando um usuário do sistema."""

    id            : ID
    nome          : str
    email         : Email
    senha         : Password
    criado_em     : datetime
    atualizado_em : datetime
    ativo         : bool


    def __post_init__(self):
        if not self.nome or not self.nome.strip():
            raise InvalidUsuarioError("O nome do usuário não pode ser vazio")

@dataclass(frozen=True, kw_only=True)
class UsuarioPerfil:
    """Entidade de domínio representando a associação entre um usuário e um perfil."""

    id: ID
    usuario_id: ID
    perfil_id: ID
    criado_em: datetime