"""Exceções de domínio do módulo Estoque."""

from app.shared.exceptions import DomainException


class ItemEstoqueNaoEncontradoError(DomainException):
    """Lançada quando o item de estoque solicitado não é encontrado."""
    pass


class CodigoItemEstoqueJaCadastradoError(DomainException):
    """Lançada ao tentar criar um item de estoque com código já cadastrado."""
    pass


class ItemEstoqueInvalidoError(DomainException):
    """Lançada quando os dados do item de estoque são inválidos."""
    pass
