import re
from dataclasses import dataclass

from app.shared.exceptions import DomainException


class CpfCnpjInvalidoError(DomainException):
    """Lançada quando o CPF ou CNPJ é inválido."""
    pass


@dataclass(frozen=True)
class CpfCnpj:
    """Value object representando um CPF (11 dígitos) ou CNPJ (14 dígitos).

    Normaliza automaticamente o valor, removendo qualquer caractere não-numérico.
    A validação de correspondência com o tipo de pessoa (PF/PJ) é feita na entidade.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"\D", "", self.value)
        object.__setattr__(self, "value", normalized)
        if len(normalized) not in (11, 14):
            raise CpfCnpjInvalidoError(
                f"CPF/CNPJ deve conter 11 dígitos (CPF) ou 14 dígitos (CNPJ). "
                f"Recebido: {len(normalized)} dígito(s)."
            )
