"""Exceções de domínio do módulo Veículos."""
from app.shared.exceptions import DomainException


class VeiculoNaoEncontradoError(DomainException):
    """Lançada quando o veículo solicitado não é encontrado."""
    pass


class PlacaJaCadastradaError(DomainException):
    """Lançada ao tentar criar um veículo com placa já cadastrada."""
    pass


class VeiculoInvalidoError(DomainException):
    """Lançada quando os dados do veículo são inválidos."""
    pass
