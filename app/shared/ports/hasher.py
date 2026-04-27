from typing import Protocol


class HasherProtocol(Protocol):
    """Contrato/porta para operações de hash de senha."""

    def hash(self, value: str) -> str: ...

    def verify(self, value: str, hashed: str) -> bool: ...
