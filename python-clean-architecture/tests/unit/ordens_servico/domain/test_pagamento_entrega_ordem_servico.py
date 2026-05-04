"""Testes unitários de domínio para a Etapa 5 — Pagamento simples e entrega da OS.

Cobre:
  - OrdemServico.registrar_pagamento()
  - OrdemServico.entregar()
  - OrdemServicoItem.consumir()
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico import (
    OrdemServico,
    StatusOrdemServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.enums import FormaPagamento
from app.modules.ordens_servico.domain.exceptions import (
    ItemOrdemServicoStatusInvalidoError,
    OrdemServicoPagamentoJaRegistradoError,
    OrdemServicoPagamentoNaoRegistradoError,
    OrdemServicoTransicaoInvalidaError,
    ValorPagamentoInvalidoError,
    ValorPagamentoMenorQueOrcamentoError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(
    status: StatusOrdemServico = StatusOrdemServico.FINALIZADA,
    pagamento_registrado_em: datetime | None = None,
    forma_pagamento: str | None = None,
    valor_pago: Decimal | None = None,
    pagamento_observacao: str | None = None,
) -> OrdemServico:
    agora = _agora()
    return OrdemServico(
        id=ID.generate(),
        cliente_id=uuid4(),
        veiculo_id=uuid4(),
        status=status,
        queixa_inicial="Barulho no motor",
        diagnostico="Motor com desgaste",
        criado_em=agora,
        atualizado_em=agora,
        iniciado_diagnostico_em=agora,
        diagnostico_concluido_em=agora,
        pagamento_registrado_em=pagamento_registrado_em,
        forma_pagamento=forma_pagamento,
        valor_pago=valor_pago,
        pagamento_observacao=pagamento_observacao,
    )


def _os_finalizada_paga() -> OrdemServico:
    """OS FINALIZADA com pagamento já registrado."""
    return _os_fake(
        status=StatusOrdemServico.FINALIZADA,
        pagamento_registrado_em=_agora(),
        forma_pagamento=FormaPagamento.PIX.value,
        valor_pago=Decimal("270.00"),
        pagamento_observacao="Pago via PIX",
    )


def _osi_fake(status: StatusItemNaOS = StatusItemNaOS.EM_USO, quantidade: int = 2) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        item_estoque_id=uuid4(),
        nome_item="Filtro de óleo",
        tipo_item="PECA",
        quantidade=quantidade,
        valor_unitario=Decimal("35.00"),
        status=status,
    )


# ---------------------------------------------------------------------------
# OrdemServico.registrar_pagamento()
# ---------------------------------------------------------------------------

class TestOrdemServicoRegistrarPagamento:

    def test_deve_registrar_pagamento_em_os_finalizada(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("270.00"),
            observacao="Pagamento recebido via PIX.",
            total_orcamento=Decimal("270.00"),
        )

        assert nova_os.status == StatusOrdemServico.FINALIZADA
        assert nova_os.pagamento_registrado_em is not None
        assert nova_os.forma_pagamento == FormaPagamento.PIX.value
        assert nova_os.valor_pago == Decimal("270.00")
        assert nova_os.pagamento_observacao == "Pagamento recebido via PIX."

    def test_registrar_pagamento_retorna_nova_instancia(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.DINHEIRO.value,
            valor_pago=Decimal("100.00"),
        )

        assert nova_os is not os

    def test_registrar_pagamento_preserva_status_original(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        os.registrar_pagamento(
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("100.00"),
        )

        assert os.status == StatusOrdemServico.FINALIZADA
        assert os.pagamento_registrado_em is None

    def test_registrar_pagamento_preserva_campos_da_os(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("100.00"),
        )

        assert nova_os.id == os.id
        assert nova_os.cliente_id == os.cliente_id
        assert nova_os.veiculo_id == os.veiculo_id
        assert nova_os.queixa_inicial == os.queixa_inicial
        assert nova_os.diagnostico == os.diagnostico

    def test_deve_registrar_pagamento_sem_observacao(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.CARTAO_CREDITO.value,
            valor_pago=Decimal("150.00"),
            observacao=None,
        )

        assert nova_os.pagamento_observacao is None
        assert nova_os.pagamento_registrado_em is not None
        assert nova_os.valor_pago == Decimal("150.00")

    def test_deve_registrar_pagamento_maior_que_orcamento(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("300.00"),
            total_orcamento=Decimal("270.00"),
        )

        assert nova_os.valor_pago == Decimal("300.00")
        assert nova_os.pagamento_registrado_em is not None

    def test_deve_registrar_pagamento_sem_total_orcamento(self):
        """Sem total_orcamento, apenas valida valor > 0."""
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        nova_os = os.registrar_pagamento(
            forma_pagamento=FormaPagamento.TRANSFERENCIA.value,
            valor_pago=Decimal("50.00"),
        )

        assert nova_os.pagamento_registrado_em is not None

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.EM_EXECUCAO,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    def test_nao_deve_registrar_pagamento_em_os_fora_de_finalizada(
        self, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.registrar_pagamento(
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal("100.00"),
            )

    def test_nao_deve_registrar_pagamento_duplicado(self):
        os = _os_fake(
            status=StatusOrdemServico.FINALIZADA,
            pagamento_registrado_em=_agora(),
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("270.00"),
        )

        with pytest.raises(OrdemServicoPagamentoJaRegistradoError):
            os.registrar_pagamento(
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal("270.00"),
            )

    def test_nao_deve_registrar_pagamento_com_valor_zero(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        with pytest.raises(ValorPagamentoInvalidoError):
            os.registrar_pagamento(
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal("0.00"),
            )

    def test_nao_deve_registrar_pagamento_com_valor_negativo(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        with pytest.raises(ValorPagamentoInvalidoError):
            os.registrar_pagamento(
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal("-1.00"),
            )

    def test_nao_deve_registrar_pagamento_menor_que_orcamento(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        with pytest.raises(ValorPagamentoMenorQueOrcamentoError):
            os.registrar_pagamento(
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal("269.99"),
                total_orcamento=Decimal("270.00"),
            )


# ---------------------------------------------------------------------------
# OrdemServico.entregar()
# ---------------------------------------------------------------------------

class TestOrdemServicoEntregar:

    def test_deve_entregar_os_finalizada_com_pagamento_registrado(self):
        os = _os_finalizada_paga()

        nova_os = os.entregar()

        assert nova_os.status == StatusOrdemServico.ENTREGUE

    def test_entregar_retorna_nova_instancia(self):
        os = _os_finalizada_paga()

        nova_os = os.entregar()

        assert nova_os is not os

    def test_entregar_preserva_status_original(self):
        os = _os_finalizada_paga()

        os.entregar()

        assert os.status == StatusOrdemServico.FINALIZADA

    def test_entregar_preserva_campos_da_os(self):
        os = _os_finalizada_paga()

        nova_os = os.entregar()

        assert nova_os.id == os.id
        assert nova_os.cliente_id == os.cliente_id
        assert nova_os.veiculo_id == os.veiculo_id
        assert nova_os.queixa_inicial == os.queixa_inicial

    def test_entregar_preserva_dados_de_pagamento(self):
        os = _os_finalizada_paga()

        nova_os = os.entregar()

        assert nova_os.pagamento_registrado_em == os.pagamento_registrado_em
        assert nova_os.forma_pagamento == os.forma_pagamento
        assert nova_os.valor_pago == os.valor_pago
        assert nova_os.pagamento_observacao == os.pagamento_observacao

    def test_nao_deve_entregar_os_sem_pagamento_registrado(self):
        os = _os_fake(StatusOrdemServico.FINALIZADA)  # sem pagamento

        with pytest.raises(OrdemServicoPagamentoNaoRegistradoError):
            os.entregar()

    def test_nao_deve_entregar_os_ja_entregue(self):
        os = _os_fake(StatusOrdemServico.ENTREGUE)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.entregar()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.EM_EXECUCAO,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    def test_nao_deve_entregar_os_fora_de_finalizada(
        self, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.entregar()


# ---------------------------------------------------------------------------
# OrdemServicoItem.consumir()
# ---------------------------------------------------------------------------

class TestOrdemServicoItemConsumirDominio:

    def test_deve_consumir_item_em_uso(self):
        item = _osi_fake(StatusItemNaOS.EM_USO)

        novo_item = item.consumir()

        assert novo_item.status == StatusItemNaOS.CONSUMIDO

    def test_consumir_retorna_nova_instancia(self):
        item = _osi_fake(StatusItemNaOS.EM_USO)

        novo_item = item.consumir()

        assert novo_item is not item

    def test_consumir_preserva_status_original(self):
        item = _osi_fake(StatusItemNaOS.EM_USO)

        item.consumir()

        assert item.status == StatusItemNaOS.EM_USO

    def test_consumir_preserva_campos_do_item(self):
        item = _osi_fake(StatusItemNaOS.EM_USO)

        novo_item = item.consumir()

        assert novo_item.id == item.id
        assert novo_item.ordem_servico_id == item.ordem_servico_id
        assert novo_item.item_estoque_id == item.item_estoque_id
        assert novo_item.nome_item == item.nome_item
        assert novo_item.quantidade == item.quantidade
        assert novo_item.valor_unitario == item.valor_unitario

    def test_nao_deve_consumir_item_reservado(self):
        item = _osi_fake(StatusItemNaOS.RESERVADO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.consumir()

    def test_nao_deve_consumir_item_a_receber(self):
        item = _osi_fake(StatusItemNaOS.A_RECEBER)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.consumir()

    def test_nao_deve_consumir_item_cancelado(self):
        item = _osi_fake(StatusItemNaOS.CANCELADO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.consumir()

    def test_nao_deve_consumir_item_ja_consumido(self):
        item = _osi_fake(StatusItemNaOS.CONSUMIDO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.consumir()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusItemNaOS.RESERVADO,
            StatusItemNaOS.A_RECEBER,
            StatusItemNaOS.CANCELADO,
            StatusItemNaOS.CONSUMIDO,
        ],
    )
    def test_status_invalidos_levantam_erro_ao_consumir(
        self, status_invalido: StatusItemNaOS
    ):
        item = _osi_fake(status_invalido)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.consumir()
