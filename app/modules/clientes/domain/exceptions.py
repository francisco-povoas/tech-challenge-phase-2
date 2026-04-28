"""Exceções de domínio do módulo Clientes."""

from app.shared.exceptions import DomainException


class ClienteNaoEncontradoError(DomainException):
    """Lançada quando o cliente solicitado não é encontrado."""
    pass


class CpfCnpjJaCadastradoError(DomainException):
    """Lançada ao tentar criar um cliente com CPF/CNPJ já cadastrado."""
    pass


class ClienteInvalidoError(DomainException):
    """Lançada quando os dados do cliente são inválidos."""
    pass
