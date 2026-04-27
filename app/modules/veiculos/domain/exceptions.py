"""Exceções de domínio do módulo Veículos."""

from app.shared.exceptions import DomainException


class VeiculoNaoEncontradoError(DomainException):
    pass


class PlacaJaCadastradaError(DomainException):
    pass


class VeiculoInvalidoError(DomainException):
    pass
