import re
from dataclasses import dataclass

from app.shared.exceptions import DomainException


class TelefoneInvalidoError(DomainException):
    """Lançada quando o telefone é inválido."""
    pass


@dataclass(frozen=True)
class Telefone:
    """Value object representando um número de telefone.

    Normaliza automaticamente o valor, removendo qualquer caractere não-numérico.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"\D", "", self.value)
        object.__setattr__(self, "value", normalized)
        if not normalized:
            raise TelefoneInvalidoError("O telefone não pode ser vazio.")
