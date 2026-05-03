"""Testes unitários para o domínio de confirmação de recebimento de item da OS."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.exceptions import ItemOrdemServicoStatusInvalidoError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _osi_fake(
    status: StatusItemNaOS = StatusItemNaOS.A_RECEBER,
    quantidade: int = 1,
) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        item_estoque_id=uuid4(),
        nome_item="Correia Alternador",
        tipo_item="PECA",
        quantidade=quantidade,
        valor_unitario=Decimal("220.00"),
        status=status,
    )


# ---------------------------------------------------------------------------
# confirmar_recebimento — transição válida
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItem:
    def test_deve_confirmar_recebimento_de_item_a_receber(self):
        item = _osi_fake(status=StatusItemNaOS.A_RECEBER)

        novo_item = item.confirmar_recebimento()

        assert novo_item.status == StatusItemNaOS.RESERVADO

    def test_confirmar_recebimento_retorna_nova_instancia(self):
        """Entidade é imutável; confirmar_recebimento deve retornar nova instância."""
        item = _osi_fake(status=StatusItemNaOS.A_RECEBER)

        novo_item = item.confirmar_recebimento()

        assert novo_item is not item

    def test_confirmar_recebimento_preserva_campos_do_item(self):
        item = _osi_fake(status=StatusItemNaOS.A_RECEBER, quantidade=3)

        novo_item = item.confirmar_recebimento()

        assert novo_item.id == item.id
        assert novo_item.ordem_servico_id == item.ordem_servico_id
        assert novo_item.item_estoque_id == item.item_estoque_id
        assert novo_item.nome_item == item.nome_item
        assert novo_item.tipo_item == item.tipo_item
        assert novo_item.quantidade == item.quantidade
        assert novo_item.valor_unitario == item.valor_unitario

    def test_confirmar_recebimento_nao_muta_status_original(self):
        item = _osi_fake(status=StatusItemNaOS.A_RECEBER)

        item.confirmar_recebimento()

        # entidade original imutável — status permanece A_RECEBER
        assert item.status == StatusItemNaOS.A_RECEBER


# ---------------------------------------------------------------------------
# confirmar_recebimento — status inválidos
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoStatusInvalido:
    def test_nao_deve_confirmar_recebimento_de_item_reservado(self):
        item = _osi_fake(status=StatusItemNaOS.RESERVADO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.confirmar_recebimento()

    def test_nao_deve_confirmar_recebimento_de_item_cancelado(self):
        item = _osi_fake(status=StatusItemNaOS.CANCELADO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.confirmar_recebimento()

    def test_nao_deve_confirmar_recebimento_de_item_em_uso(self):
        item = _osi_fake(status=StatusItemNaOS.EM_USO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.confirmar_recebimento()

    def test_nao_deve_confirmar_recebimento_de_item_consumido(self):
        item = _osi_fake(status=StatusItemNaOS.CONSUMIDO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.confirmar_recebimento()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusItemNaOS.RESERVADO,
            StatusItemNaOS.CANCELADO,
            StatusItemNaOS.EM_USO,
            StatusItemNaOS.CONSUMIDO,
        ],
    )
    def test_status_invalidos_levantam_erro(self, status_invalido: StatusItemNaOS):
        item = _osi_fake(status=status_invalido)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.confirmar_recebimento()
