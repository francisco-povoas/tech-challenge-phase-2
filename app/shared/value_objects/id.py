from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


class InvalidIDError(Exception):
    pass


@dataclass(frozen=True)
class ID:
    """Value object representando um identificador único (UUID)."""

    value: UUID

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Cria um ID a partir de uma string UUID.

        Raises:
            InvalidIDError: Se a string não for um UUID válido.
        """
        try:
            return cls(UUID(value))
        except (ValueError, TypeError) as e:
            raise InvalidIDError(f"UUID inválido: {value}") from e

    @classmethod
    def generate(cls) -> Self:
        """Gera um novo ID baseado em UUID."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)
