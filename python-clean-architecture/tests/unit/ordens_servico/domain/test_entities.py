"""Testes unitários para as entidades de domínio do módulo ordens_servico."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico import (
    OrdemServico,
    StatusOrdemServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import (
    OrdemServicoServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoInvalidaError,
    OrdemServicoTransicaoInvalidaError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(
    status: StatusOrdemServico = StatusOrdemServico.RECEBIDA,
    queixa_inicial: str = "Barulho no motor",
    diagnostico: str | None = None,
) -> OrdemServico:
    agora = _agora()
    return OrdemServico(
        id=ID.generate(),
        cliente_id=uuid4(),
        veiculo_id=uuid4(),
        status=status,
        queixa_inicial=queixa_inicial,
        diagnostico=diagnostico,
        criado_em=agora,
        atualizado_em=agora,
        iniciado_diagnostico_em=None,
        diagnostico_concluido_em=None,
    )


def _oss_fake(cancelado: bool = False) -> OrdemServicoServico:
    return OrdemServicoServico(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        servico_id=uuid4(),
        nome_servico="Troca de óleo",
        descricao_servico="Substituição do óleo do motor",
        valor_unitario=Decimal("120.00"),
        tempo_estimado_minutos=60,
        tempo_executado_minutos=None,
        observacao=None,
        cancelado=cancelado,
    )


def _osi_fake(status: StatusItemNaOS = StatusItemNaOS.RESERVADO) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        item_estoque_id=uuid4(),
        nome_item="Filtro de óleo",
        tipo_item="PECA",
        quantidade=2,
        valor_unitario=Decimal("35.00"),
        status=status,
    )


# ---------------------------------------------------------------------------
# OrdemServico entity
# ---------------------------------------------------------------------------

class TestOrdemServicoEntidade:
    def test_criacao_valida(self):
        os = _os_fake()
        assert os.status == StatusOrdemServico.RECEBIDA
        assert os.queixa_inicial == "Barulho no motor"

    def test_queixa_inicial_vazia_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            _os_fake(queixa_inicial="")

    def test_queixa_inicial_somente_espacos_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            _os_fake(queixa_inicial="   ")

    def test_pode_transitar_para_status_valido(self):
        os = _os_fake(status=StatusOrdemServico.RECEBIDA)
        assert os.pode_transitar_para(StatusOrdemServico.EM_DIAGNOSTICO) is True

    def test_pode_transitar_para_status_invalido(self):
        os = _os_fake(status=StatusOrdemServico.RECEBIDA)
        assert os.pode_transitar_para(StatusOrdemServico.FINALIZADA) is False

    def test_validar_transicao_valida_nao_levanta_erro(self):
        os = _os_fake(status=StatusOrdemServico.RECEBIDA)
        os.validar_transicao(StatusOrdemServico.EM_DIAGNOSTICO)  # não deve lançar

    def test_validar_transicao_invalida_levanta_erro(self):
        os = _os_fake(status=StatusOrdemServico.RECEBIDA)
        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.validar_transicao(StatusOrdemServico.FINALIZADA)

    def test_estados_terminais_nao_tem_transicoes(self):
        for status_terminal in (StatusOrdemServico.ENTREGUE, StatusOrdemServico.ENCERRADA):
            os = _os_fake(status=status_terminal)
            for outro in StatusOrdemServico:
                assert os.pode_transitar_para(outro) is False

    def test_transicao_recebida_para_em_diagnostico(self):
        os = _os_fake(status=StatusOrdemServico.RECEBIDA)
        assert os.pode_transitar_para(StatusOrdemServico.EM_DIAGNOSTICO)

    def test_transicao_em_diagnostico_para_diagnostico_concluido(self):
        os = _os_fake(status=StatusOrdemServico.EM_DIAGNOSTICO)
        assert os.pode_transitar_para(StatusOrdemServico.DIAGNOSTICO_CONCLUIDO)

    def test_transicao_diagnostico_concluido_para_aguardando_aprovacao(self):
        os = _os_fake(status=StatusOrdemServico.DIAGNOSTICO_CONCLUIDO)
        assert os.pode_transitar_para(StatusOrdemServico.AGUARDANDO_APROVACAO)

    def test_aprovada_nao_pode_ir_para_aguardando_itens(self):
        """Correção: APROVADA→AGUARDANDO_ITENS foi removida do mapa de transições."""
        os = _os_fake(status=StatusOrdemServico.APROVADA)
        assert os.pode_transitar_para(StatusOrdemServico.AGUARDANDO_ITENS) is False

    def test_entregue_nao_pode_ir_para_encerrada(self):
        """Correção: ENTREGUE→ENCERRADA foi removida do mapa de transições."""
        os = _os_fake(status=StatusOrdemServico.ENTREGUE)
        assert os.pode_transitar_para(StatusOrdemServico.ENCERRADA) is False

    def test_aguardando_itens_nao_pode_ir_para_encerrada(self):
        """Correção: AGUARDANDO_ITENS→ENCERRADA foi removida."""
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        assert os.pode_transitar_para(StatusOrdemServico.ENCERRADA) is False

    def test_aguardando_itens_pode_ir_para_aprovada(self):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        assert os.pode_transitar_para(StatusOrdemServico.APROVADA)


# ---------------------------------------------------------------------------
# OrdemServicoServico entity
# ---------------------------------------------------------------------------

class TestOrdemServicoServicoEntidade:
    def test_criacao_valida(self):
        oss = _oss_fake()
        assert oss.nome_servico == "Troca de óleo"
        assert oss.cancelado is False

    def test_nome_vazio_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                servico_id=uuid4(),
                nome_servico="",
                descricao_servico=None,
                valor_unitario=Decimal("50.00"),
                tempo_estimado_minutos=30,
                tempo_executado_minutos=None,
                observacao=None,
                cancelado=False,
            )

    def test_nome_somente_espacos_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                servico_id=uuid4(),
                nome_servico="   ",
                descricao_servico=None,
                valor_unitario=Decimal("50.00"),
                tempo_estimado_minutos=30,
                tempo_executado_minutos=None,
                observacao=None,
                cancelado=False,
            )

    def test_valor_negativo_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                servico_id=uuid4(),
                nome_servico="Troca de óleo",
                descricao_servico=None,
                valor_unitario=Decimal("-1.00"),
                tempo_estimado_minutos=30,
                tempo_executado_minutos=None,
                observacao=None,
                cancelado=False,
            )

    def test_valor_zero_e_valido(self):
        oss = OrdemServicoServico(
            id=ID.generate(),
            ordem_servico_id=uuid4(),
            servico_id=uuid4(),
            nome_servico="Diagnóstico gratuito",
            descricao_servico=None,
            valor_unitario=Decimal("0.00"),
            tempo_estimado_minutos=30,
            tempo_executado_minutos=None,
            observacao=None,
            cancelado=False,
        )
        assert oss.valor_unitario == Decimal("0.00")

    def test_tempo_estimado_zero_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                servico_id=uuid4(),
                nome_servico="Serviço",
                descricao_servico=None,
                valor_unitario=Decimal("50.00"),
                tempo_estimado_minutos=0,
                tempo_executado_minutos=None,
                observacao=None,
                cancelado=False,
            )

    def test_tempo_estimado_negativo_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoServico(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                servico_id=uuid4(),
                nome_servico="Serviço",
                descricao_servico=None,
                valor_unitario=Decimal("50.00"),
                tempo_estimado_minutos=-10,
                tempo_executado_minutos=None,
                observacao=None,
                cancelado=False,
            )


# ---------------------------------------------------------------------------
# OrdemServicoItem entity
# ---------------------------------------------------------------------------

class TestOrdemServicoItemEntidade:
    def test_criacao_valida(self):
        osi = _osi_fake()
        assert osi.nome_item == "Filtro de óleo"
        assert osi.status == StatusItemNaOS.RESERVADO

    def test_nome_vazio_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoItem(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                item_estoque_id=uuid4(),
                nome_item="",
                tipo_item="PECA",
                quantidade=1,
                valor_unitario=Decimal("10.00"),
                status=StatusItemNaOS.RESERVADO,
            )

    def test_quantidade_zero_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoItem(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                item_estoque_id=uuid4(),
                nome_item="Filtro",
                tipo_item="PECA",
                quantidade=0,
                valor_unitario=Decimal("10.00"),
                status=StatusItemNaOS.RESERVADO,
            )

    def test_quantidade_negativa_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoItem(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                item_estoque_id=uuid4(),
                nome_item="Filtro",
                tipo_item="PECA",
                quantidade=-1,
                valor_unitario=Decimal("10.00"),
                status=StatusItemNaOS.RESERVADO,
            )

    def test_valor_negativo_levanta_erro(self):
        with pytest.raises(OrdemServicoInvalidaError):
            OrdemServicoItem(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                item_estoque_id=uuid4(),
                nome_item="Filtro",
                tipo_item="PECA",
                quantidade=1,
                valor_unitario=Decimal("-1.00"),
                status=StatusItemNaOS.RESERVADO,
            )

    def test_valor_zero_e_valido(self):
        osi = OrdemServicoItem(
            id=ID.generate(),
            ordem_servico_id=uuid4(),
            item_estoque_id=uuid4(),
            nome_item="Filtro",
            tipo_item="PECA",
            quantidade=1,
            valor_unitario=Decimal("0.00"),
            status=StatusItemNaOS.A_RECEBER,
        )
        assert osi.valor_unitario == Decimal("0.00")

    def test_status_a_receber(self):
        osi = _osi_fake(status=StatusItemNaOS.A_RECEBER)
        assert osi.status == StatusItemNaOS.A_RECEBER
