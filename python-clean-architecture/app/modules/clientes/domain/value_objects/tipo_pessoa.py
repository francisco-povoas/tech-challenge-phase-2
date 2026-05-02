from enum import StrEnum

from app.shared.exceptions import DomainException


class TipoPessoaInvalidoError(DomainException):
    """Lançada quando o tipo de pessoa é inválido."""
    pass


class TipoPessoa(StrEnum):
    """Value object representando o tipo de pessoa do cliente."""

    PF = "PF"
    PJ = "PJ"

    @classmethod
    def tipos(cls) -> list[str]:
        return [cls.PF.value, cls.PJ.value]
