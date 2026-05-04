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


class ItemOrdemServicoStatusInvalidoError(DomainException):
    """Lançada quando o item da OS não está no status esperado para a operação."""
    pass


class OrcamentoInvalidoError(DomainException):
    """Lançada quando os dados do orçamento são inválidos."""
    pass


class OrcamentoNaoEncontradoError(DomainException):
    """Lançada quando o orçamento solicitado não é encontrado."""
    pass


class OrcamentoJaExisteParaOrdemServicoError(DomainException):
    """Lançada quando já existe um orçamento para a OS."""
    pass


class OrcamentoStatusInvalidoError(DomainException):
    """Lançada quando o orçamento não está no status esperado para a operação."""
    pass


class ClienteSemContatoParaOrcamentoError(DomainException):
    """Lançada quando o cliente não possui e-mail e/ou telefone para envio do orçamento."""
    pass


class OrdemServicoPossuiItemAReceberError(DomainException):
    """Lançada quando a OS possui item ativo com status A_RECEBER impedindo a execução."""
    pass


class OrdemServicoServicoCanceladoError(DomainException):
    """Lançada quando se tenta operar em um serviço cancelado da OS."""
    pass


class TempoExecutadoInvalidoError(DomainException):
    """Lançada quando o tempo executado informado é inválido."""
    pass


class OrdemServicoPossuiServicoSemTempoExecutadoError(DomainException):
    """Lançada quando a OS possui serviço ativo sem tempo executado registrado."""
    pass


class OrdemServicoPagamentoJaRegistradoError(DomainException):
    """Lançada quando se tenta registrar pagamento de OS que já possui pagamento."""
    pass


class OrdemServicoPagamentoNaoRegistradoError(DomainException):
    """Lançada quando se tenta entregar OS sem pagamento registrado."""
    pass


class ValorPagamentoInvalidoError(DomainException):
    """Lançada quando valor_pago é inválido (zero ou negativo)."""
    pass


class ValorPagamentoMenorQueOrcamentoError(DomainException):
    """Lançada quando valor_pago é menor que o total_geral do orçamento aprovado."""
    pass


class OrdemServicoPossuiItemPendenteError(DomainException):
    """Lançada quando a OS possui item ativo com status A_RECEBER impedindo a entrega."""
    pass


class OrdemServicoPossuiItemReservadoError(DomainException):
    """Lançada quando a OS possui item ativo com status RESERVADO impedindo a entrega."""
    pass


class EstoqueReservadoInsuficienteError(DomainException):
    """Lançada quando a quantidade reservada no estoque é insuficiente para consumir o item."""
    pass

