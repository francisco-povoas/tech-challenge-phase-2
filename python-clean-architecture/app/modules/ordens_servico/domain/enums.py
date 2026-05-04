"""Enums de domínio do módulo Ordens de Serviço."""

from enum import Enum


class FormaPagamento(str, Enum):
    """Formas de pagamento aceitas para liquidação de uma Ordem de Serviço."""

    DINHEIRO = "DINHEIRO"
    PIX = "PIX"
    CARTAO_CREDITO = "CARTAO_CREDITO"
    CARTAO_DEBITO = "CARTAO_DEBITO"
    BOLETO = "BOLETO"
    TRANSFERENCIA = "TRANSFERENCIA"
