import re
from dataclasses import dataclass

from app.shared.exceptions import DomainException


class PlacaInvalidaError(DomainException):
    """Lançada quando a placa do veículo é inválida."""
    pass


# Padrões aceitos (sem máscara):
#   Formato antigo: ABC1234
#   Formato Mercosul: ABC1D23
_PLACA_RE = re.compile(r"^[A-Z]{3}[0-9]{1}[A-Z0-9]{1}[0-9]{2}$")


@dataclass(frozen=True)
class Placa:
    """Value object representando a placa de um veículo.

    Normaliza automaticamente o valor: maiúsculas, remove espaços e hífens.
    Aceita os formatos ABC1234 (antigo) e ABC1D23 (Mercosul).
    """

    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"[\s\-]", "", self.value).upper()
        object.__setattr__(self, "value", normalized)
        if not normalized:
            raise PlacaInvalidaError("A placa não pode ser vazia.")
        if not _PLACA_RE.match(normalized):
            raise PlacaInvalidaError(
                f"Placa '{normalized}' inválida. "
                "Formatos aceitos: ABC1234 (antigo) ou ABC1D23 (Mercosul)."
            )
