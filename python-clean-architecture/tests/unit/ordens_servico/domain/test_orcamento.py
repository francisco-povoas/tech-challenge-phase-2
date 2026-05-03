"""Testes unitários para as entidades de domínio de orçamento (ordens_servico)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.orcamento import (
    Orcamento,
    StatusOrcamento,
)
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import (
    CanalComunicacaoOrcamento,
    OrcamentoComunicacao,
)
from app.modules.ordens_servico.domain.exceptions import OrcamentoInvalidoError, OrcamentoStatusInvalidoError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _orcamento_fake(
    total_servicos: Decimal = Decimal("180.00"),
    total_itens: Decimal = Decimal("390.00"),
    status: StatusOrcamento = StatusOrcamento.GERADO,
    comunicado_em: datetime | None = None,
) -> Orcamento:
    agora = _agora()
    return Orcamento(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        status=status,
        total_servicos=total_servicos,
        total_itens=total_itens,
        total_geral=total_servicos + total_itens,
        criado_em=agora,
        atualizado_em=agora,
        comunicado_em=comunicado_em,
        observacao=None,
    )


def _comunicacao_fake(
    canal: CanalComunicacaoOrcamento = CanalComunicacaoOrcamento.WHATSAPP,
    destino: str = "11991234567",
    sucesso: bool = True,
    mensagem: str = "WhatsApp enviado",
    provedor: str = "mock",
    referencia_externa: str | None = None,
) -> OrcamentoComunicacao:
    agora = _agora()
    return OrcamentoComunicacao(
        id=ID.generate(),
        orcamento_id=uuid4(),
        ordem_servico_id=uuid4(),
        canal=canal,
        destino=destino,
        sucesso=sucesso,
        mensagem=mensagem,
        provedor=provedor,
        referencia_externa=referencia_externa,
        enviado_em=agora,
        criado_em=agora,
    )


# ---------------------------------------------------------------------------
# Orcamento entity
# ---------------------------------------------------------------------------

class TestOrcamentoEntidade:
    def test_deve_criar_orcamento_com_status_gerado(self):
        orc = _orcamento_fake()
        assert orc.status == StatusOrcamento.GERADO
        assert orc.total_servicos == Decimal("180.00")
        assert orc.total_itens == Decimal("390.00")
        assert orc.total_geral == Decimal("570.00")
        assert orc.comunicado_em is None
        assert orc.criado_em is not None
        assert orc.atualizado_em is not None
        assert orc.ordem_servico_id is not None

    def test_deve_marcar_orcamento_como_comunicado(self):
        orc = _orcamento_fake()
        comunicado_em = _agora()
        orc_comunicado = orc.marcar_como_comunicado(comunicado_em)

        assert orc_comunicado.status == StatusOrcamento.COMUNICADO
        assert orc_comunicado.comunicado_em == comunicado_em
        assert orc_comunicado.atualizado_em == comunicado_em
        # entidade original imutável
        assert orc.status == StatusOrcamento.GERADO
        assert orc.comunicado_em is None

    def test_marcar_como_comunicado_preserva_totais(self):
        orc = _orcamento_fake(
            total_servicos=Decimal("200.00"),
            total_itens=Decimal("100.00"),
        )
        orc_comunicado = orc.marcar_como_comunicado(_agora())
        assert orc_comunicado.total_servicos == Decimal("200.00")
        assert orc_comunicado.total_itens == Decimal("100.00")
        assert orc_comunicado.total_geral == Decimal("300.00")

    def test_nao_deve_criar_orcamento_com_total_servicos_negativo(self):
        with pytest.raises(OrcamentoInvalidoError):
            Orcamento(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                status=StatusOrcamento.GERADO,
                total_servicos=Decimal("-1.00"),
                total_itens=Decimal("0.00"),
                total_geral=Decimal("-1.00"),
                criado_em=_agora(),
                atualizado_em=_agora(),
                comunicado_em=None,
                observacao=None,
            )

    def test_nao_deve_criar_orcamento_com_total_itens_negativo(self):
        with pytest.raises(OrcamentoInvalidoError):
            Orcamento(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                status=StatusOrcamento.GERADO,
                total_servicos=Decimal("100.00"),
                total_itens=Decimal("-50.00"),
                total_geral=Decimal("50.00"),
                criado_em=_agora(),
                atualizado_em=_agora(),
                comunicado_em=None,
                observacao=None,
            )

    def test_nao_deve_criar_orcamento_com_total_geral_diferente_da_soma(self):
        with pytest.raises(OrcamentoInvalidoError):
            Orcamento(
                id=ID.generate(),
                ordem_servico_id=uuid4(),
                status=StatusOrcamento.GERADO,
                total_servicos=Decimal("100.00"),
                total_itens=Decimal("50.00"),
                total_geral=Decimal("999.00"),  # errado: deveria ser 150.00
                criado_em=_agora(),
                atualizado_em=_agora(),
                comunicado_em=None,
                observacao=None,
            )

    def test_valor_zero_deve_ser_valido(self):
        orc = Orcamento(
            id=ID.generate(),
            ordem_servico_id=uuid4(),
            status=StatusOrcamento.GERADO,
            total_servicos=Decimal("0.00"),
            total_itens=Decimal("0.00"),
            total_geral=Decimal("0.00"),
            criado_em=_agora(),
            atualizado_em=_agora(),
            comunicado_em=None,
            observacao=None,
        )
        assert orc.total_geral == Decimal("0.00")

    def test_observacao_pode_ser_none(self):
        orc = _orcamento_fake()
        assert orc.observacao is None

    def test_status_enum_valores(self):
        assert StatusOrcamento.GERADO.value == "GERADO"
        assert StatusOrcamento.COMUNICADO.value == "COMUNICADO"
        assert StatusOrcamento.APROVADO.value == "APROVADO"
        assert StatusOrcamento.RECUSADO.value == "RECUSADO"


# ---------------------------------------------------------------------------
# OrcamentoComunicacao entity
# ---------------------------------------------------------------------------

class TestOrcamentoComunicacaoEntidade:
    def test_deve_criar_comunicacao_whatsapp_com_sucesso(self):
        com = _comunicacao_fake(
            canal=CanalComunicacaoOrcamento.WHATSAPP,
            destino="11991234567",
            sucesso=True,
            mensagem="WhatsApp enviado",
            provedor="mock",
        )
        assert com.canal == CanalComunicacaoOrcamento.WHATSAPP
        assert com.destino == "11991234567"
        assert com.sucesso is True
        assert com.mensagem == "WhatsApp enviado"
        assert com.provedor == "mock"
        assert com.enviado_em is not None
        assert com.criado_em is not None

    def test_deve_criar_comunicacao_email_com_sucesso(self):
        com = _comunicacao_fake(
            canal=CanalComunicacaoOrcamento.EMAIL,
            destino="user@example.com",
            sucesso=True,
            mensagem="E-mail enviado",
            provedor="mock",
        )
        assert com.canal == CanalComunicacaoOrcamento.EMAIL
        assert com.destino == "user@example.com"
        assert com.sucesso is True
        assert com.mensagem == "E-mail enviado"

    def test_referencia_externa_pode_ser_none(self):
        com = _comunicacao_fake(referencia_externa=None)
        assert com.referencia_externa is None

    def test_referencia_externa_pode_ser_preenchida(self):
        com = _comunicacao_fake(referencia_externa="msg-id-123")
        assert com.referencia_externa == "msg-id-123"

    def test_sucesso_pode_ser_false(self):
        com = _comunicacao_fake(sucesso=False, mensagem="Falha ao enviar")
        assert com.sucesso is False
        assert com.mensagem == "Falha ao enviar"

    def test_canal_enum_valores(self):
        assert CanalComunicacaoOrcamento.WHATSAPP.value == "WHATSAPP"
        assert CanalComunicacaoOrcamento.EMAIL.value == "EMAIL"

    def test_orcamento_id_e_ordem_servico_id_sao_preservados(self):
        orc_id = uuid4()
        os_id = uuid4()
        agora = _agora()
        com = OrcamentoComunicacao(
            id=ID.generate(),
            orcamento_id=orc_id,
            ordem_servico_id=os_id,
            canal=CanalComunicacaoOrcamento.WHATSAPP,
            destino="11999999999",
            sucesso=True,
            mensagem="ok",
            provedor="mock",
            referencia_externa=None,
            enviado_em=agora,
            criado_em=agora,
        )
        assert com.orcamento_id == orc_id
        assert com.ordem_servico_id == os_id


# ---------------------------------------------------------------------------
# Orcamento.aprovar()
# ---------------------------------------------------------------------------

class TestOrcamentoAprovar:
    def test_deve_aprovar_orcamento_comunicado(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        aprovado = orc.aprovar(respondido_em=agora)

        assert aprovado.status == StatusOrcamento.APROVADO
        assert aprovado.respondido_em is not None
        assert aprovado.motivo_recusa is None
        # imutabilidade: original inalterado
        assert orc.status == StatusOrcamento.COMUNICADO

    def test_aprovacao_preserva_totais(self):
        agora = _agora()
        orc = _orcamento_fake(
            total_servicos=Decimal("200.00"),
            total_itens=Decimal("100.00"),
            status=StatusOrcamento.COMUNICADO,
            comunicado_em=agora,
        )
        aprovado = orc.aprovar(respondido_em=agora)

        assert aprovado.total_servicos == Decimal("200.00")
        assert aprovado.total_itens == Decimal("100.00")
        assert aprovado.total_geral == Decimal("300.00")
        assert aprovado.observacao == orc.observacao
        assert aprovado.ordem_servico_id == orc.ordem_servico_id

    def test_aprovacao_preenche_respondido_em(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        aprovado = orc.aprovar(respondido_em=agora)
        assert aprovado.respondido_em == agora

    @pytest.mark.parametrize("status_invalido", [
        StatusOrcamento.GERADO,
        StatusOrcamento.APROVADO,
        StatusOrcamento.RECUSADO,
    ])
    def test_nao_deve_aprovar_orcamento_fora_de_comunicado(self, status_invalido):
        orc = _orcamento_fake(status=status_invalido)
        with pytest.raises(OrcamentoStatusInvalidoError):
            orc.aprovar(respondido_em=_agora())

    def test_nao_deve_aprovar_orcamento_gerado(self):
        orc = _orcamento_fake(status=StatusOrcamento.GERADO)
        with pytest.raises(OrcamentoStatusInvalidoError):
            orc.aprovar(respondido_em=_agora())

    def test_nao_deve_aprovar_orcamento_aprovado(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        aprovado = orc.aprovar(respondido_em=agora)
        with pytest.raises(OrcamentoStatusInvalidoError):
            aprovado.aprovar(respondido_em=agora)

    def test_nao_deve_aprovar_orcamento_recusado(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        recusado = orc.recusar(respondido_em=agora)
        with pytest.raises(OrcamentoStatusInvalidoError):
            recusado.aprovar(respondido_em=agora)


# ---------------------------------------------------------------------------
# Orcamento.recusar()
# ---------------------------------------------------------------------------

class TestOrcamentoRecusar:
    def test_deve_recusar_orcamento_comunicado_com_motivo(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        recusado = orc.recusar(
            respondido_em=agora,
            motivo_recusa="Cliente nao aprovou o valor.",
        )

        assert recusado.status == StatusOrcamento.RECUSADO
        assert recusado.respondido_em is not None
        assert recusado.motivo_recusa == "Cliente nao aprovou o valor."
        # imutabilidade
        assert orc.status == StatusOrcamento.COMUNICADO

    def test_deve_recusar_orcamento_comunicado_sem_motivo(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        recusado = orc.recusar(respondido_em=agora, motivo_recusa=None)

        assert recusado.status == StatusOrcamento.RECUSADO
        assert recusado.respondido_em is not None
        assert recusado.motivo_recusa is None

    def test_recusa_preenche_respondido_em(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        recusado = orc.recusar(respondido_em=agora)
        assert recusado.respondido_em == agora

    def test_recusa_preserva_totais(self):
        agora = _agora()
        orc = _orcamento_fake(
            total_servicos=Decimal("180.00"),
            total_itens=Decimal("390.00"),
            status=StatusOrcamento.COMUNICADO,
            comunicado_em=agora,
        )
        recusado = orc.recusar(respondido_em=agora, motivo_recusa="Caro demais")

        assert recusado.total_servicos == Decimal("180.00")
        assert recusado.total_itens == Decimal("390.00")
        assert recusado.total_geral == Decimal("570.00")
        assert recusado.ordem_servico_id == orc.ordem_servico_id

    @pytest.mark.parametrize("status_invalido", [
        StatusOrcamento.GERADO,
        StatusOrcamento.APROVADO,
        StatusOrcamento.RECUSADO,
    ])
    def test_nao_deve_recusar_orcamento_fora_de_comunicado(self, status_invalido):
        orc = _orcamento_fake(status=status_invalido)
        with pytest.raises(OrcamentoStatusInvalidoError):
            orc.recusar(respondido_em=_agora())

    def test_nao_deve_recusar_orcamento_gerado(self):
        orc = _orcamento_fake(status=StatusOrcamento.GERADO)
        with pytest.raises(OrcamentoStatusInvalidoError):
            orc.recusar(respondido_em=_agora())

    def test_nao_deve_recusar_orcamento_aprovado(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        aprovado = orc.aprovar(respondido_em=agora)
        with pytest.raises(OrcamentoStatusInvalidoError):
            aprovado.recusar(respondido_em=agora)

    def test_nao_deve_recusar_orcamento_ja_recusado(self):
        agora = _agora()
        orc = _orcamento_fake(status=StatusOrcamento.COMUNICADO, comunicado_em=agora)
        recusado = orc.recusar(respondido_em=agora)
        with pytest.raises(OrcamentoStatusInvalidoError):
            recusado.recusar(respondido_em=agora)
