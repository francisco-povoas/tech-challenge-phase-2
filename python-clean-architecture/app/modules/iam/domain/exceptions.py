"""Exceções de domínio do módulo IAM."""

from app.shared.exceptions import DomainException


class UsuarioNaoEncontradoError(DomainException):
    """Lançada quando o usuário solicitado não é encontrado."""
    pass


class UsuarioJaExisteError(DomainException):
    """Lançada ao tentar criar um usuário com e-mail já cadastrado."""
    pass


class AutenticacaoFalhouError(DomainException):
    """Lançada quando as credenciais de autenticação são inválidas."""
    pass


class InvalidUsuarioError(DomainException):
    """Lançada quando os dados do usuário são inválidos."""
    pass
