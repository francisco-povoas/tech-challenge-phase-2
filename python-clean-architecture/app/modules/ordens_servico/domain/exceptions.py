"""Exceções de domínio do módulo Ordens de Serviço."""

from app.shared.exceptions import DomainException


class OrdemServicoNaoEncontradaError(DomainException):
    """Lançada quando a OS solicitada não é encontrada."""
    pass


class OrdemServicoInvalidaError(DomainException):
    """Lançada quando os dados da OS são inválidos."""
    pass


class OrdemServicoTransicaoInvalidaError(DomainException):
    """Lançada quando uma transição de status inválida é solicitada."""
    pass


class OrdemServicoServicoNaoEncontradoError(DomainException):
    """Lançada quando o vínculo de serviço na OS não é encontrado."""
    pass


class OrdemServicoItemNaoEncontradoError(DomainException):
    """Lançada quando o vínculo de item na OS não é encontrado."""
    pass


class ServicoJaAdicionadoNaOrdemServicoError(DomainException):
    """Lançada quando o serviço já está ativo na OS."""
    pass


class ItemJaAdicionadoNaOrdemServicoError(DomainException):
    """Lançada quando o item de estoque já está ativo na OS."""
    pass

