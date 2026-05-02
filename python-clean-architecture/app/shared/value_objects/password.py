from dataclasses import dataclass


class InvalidPasswordError(Exception):
    pass


@dataclass(frozen=True)
class Password:
    """Value object representando uma senha com validação de tamanho."""

    value: str
    _MIN_PASSWORD_LENGTH = 8
    _MAX_PASSWORD_LENGTH = 100

    def __post_init__(self):
        if not (self._MIN_PASSWORD_LENGTH <= len(self.value) <= self._MAX_PASSWORD_LENGTH):
            raise InvalidPasswordError(
                f"A senha deve ter entre {self._MIN_PASSWORD_LENGTH} "
                f"e {self._MAX_PASSWORD_LENGTH} caracteres"
            )
