"""Exceções de domínio do módulo Serviços."""

from app.shared.exceptions import DomainException


class ServicoNaoEncontradoError(DomainException):
    """Lançada quando o serviço solicitado não é encontrado."""
    pass


class NomeServicoJaCadastradoError(DomainException):
    """Lançada ao tentar criar um serviço com nome já cadastrado."""
    pass


class ServicoInvalidoError(DomainException):
    """Lançada quando os dados do serviço são inválidos."""
    pass
