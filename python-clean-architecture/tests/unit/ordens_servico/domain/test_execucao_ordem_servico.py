"""Testes unitários de domínio para a Fase 3 — Execução da OS.

Cobre:
  - OrdemServico.iniciar_execucao()
  - OrdemServico.finalizar()
  - OrdemServicoItem.colocar_em_uso()
  - OrdemServicoServico.registrar_tempo_executado()
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
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.exceptions import (
    ItemOrdemServicoStatusInvalidoError,
    OrdemServicoServicoCanceladoError,
    OrdemServicoTransicaoInvalidaError,
    OrdemServicoPossuiItemAReceberError,
    OrdemServicoPossuiServicoSemTempoExecutadoError,
    TempoExecutadoInvalidoError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(status: StatusOrdemServico = StatusOrdemServico.APROVADA) -> OrdemServico:
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


def _oss_fake(
    cancelado: bool = False,
    tempo_executado_minutos: int | None = None,
) -> OrdemServicoServico:
    return OrdemServicoServico(
        id=ID.generate(),
        ordem_servico_id=uuid4(),
        servico_id=uuid4(),
        nome_servico="Troca de óleo",
        descricao_servico=None,
        valor_unitario=Decimal("120.00"),
        tempo_estimado_minutos=60,
        tempo_executado_minutos=tempo_executado_minutos,
        observacao=None,
        cancelado=cancelado,
    )


# ---------------------------------------------------------------------------
# OrdemServico.iniciar_execucao()
# ---------------------------------------------------------------------------

class TestOrdemServicoIniciarExecucao:
    def test_deve_iniciar_execucao_de_os_aprovada_sem_item_a_receber(self):
        os = _os_fake(StatusOrdemServico.APROVADA)

        nova_os = os.iniciar_execucao(itens_ativos_status=[StatusItemNaOS.RESERVADO.value])

        assert nova_os.status == StatusOrdemServico.EM_EXECUCAO

    def test_iniciar_execucao_retorna_nova_instancia(self):
        """Entidade é imutável; deve retornar nova instância."""
        os = _os_fake(StatusOrdemServico.APROVADA)

        nova_os = os.iniciar_execucao(itens_ativos_status=[])

        assert nova_os is not os

    def test_iniciar_execucao_preserva_status_original(self):
        os = _os_fake(StatusOrdemServico.APROVADA)

        os.iniciar_execucao(itens_ativos_status=[])

        assert os.status == StatusOrdemServico.APROVADA

    def test_iniciar_execucao_preserva_campos_da_os(self):
        os = _os_fake(StatusOrdemServico.APROVADA)

        nova_os = os.iniciar_execucao(itens_ativos_status=[])

        assert nova_os.id == os.id
        assert nova_os.cliente_id == os.cliente_id
        assert nova_os.veiculo_id == os.veiculo_id
        assert nova_os.queixa_inicial == os.queixa_inicial
        assert nova_os.diagnostico == os.diagnostico

    def test_deve_iniciar_execucao_com_lista_de_itens_vazia(self):
        """OS APROVADA sem itens pode iniciar execução."""
        os = _os_fake(StatusOrdemServico.APROVADA)

        nova_os = os.iniciar_execucao(itens_ativos_status=[])

        assert nova_os.status == StatusOrdemServico.EM_EXECUCAO

    def test_nao_deve_iniciar_execucao_quando_existir_item_a_receber_ativo(self):
        os = _os_fake(StatusOrdemServico.APROVADA)

        with pytest.raises(OrdemServicoPossuiItemAReceberError):
            os.iniciar_execucao(
                itens_ativos_status=[
                    StatusItemNaOS.RESERVADO.value,
                    StatusItemNaOS.A_RECEBER.value,
                ]
            )

    def test_nao_deve_iniciar_execucao_quando_somente_item_a_receber(self):
        os = _os_fake(StatusOrdemServico.APROVADA)

        with pytest.raises(OrdemServicoPossuiItemAReceberError):
            os.iniciar_execucao(itens_ativos_status=[StatusItemNaOS.A_RECEBER.value])

    def test_deve_ignorar_item_cancelado_na_validacao_de_item_a_receber(self):
        """Itens CANCELADO são excluídos antes de chamar iniciar_execucao.

        O método recebe apenas status de itens ativos (não cancelados).
        Passando apenas RESERVADO, a execução deve ser permitida.
        """
        os = _os_fake(StatusOrdemServico.APROVADA)

        nova_os = os.iniciar_execucao(itens_ativos_status=[StatusItemNaOS.RESERVADO.value])

        assert nova_os.status == StatusOrdemServico.EM_EXECUCAO

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.EM_EXECUCAO,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    def test_nao_deve_iniciar_execucao_de_os_fora_de_aprovada(
        self, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.iniciar_execucao(itens_ativos_status=[])


# ---------------------------------------------------------------------------
# OrdemServico.finalizar()
# ---------------------------------------------------------------------------

class TestOrdemServicoFinalizar:
    def test_deve_finalizar_os_em_execucao_com_todos_servicos_ativos_com_tempo(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        nova_os = os.finalizar(servicos_ativos_com_tempo=[True, True])

        assert nova_os.status == StatusOrdemServico.FINALIZADA

    def test_deve_finalizar_os_sem_servicos_ativos(self):
        """OS sem serviços ativos pode ser finalizada (lista vazia → all([]) == True)."""
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        nova_os = os.finalizar(servicos_ativos_com_tempo=[])

        assert nova_os.status == StatusOrdemServico.FINALIZADA

    def test_finalizar_retorna_nova_instancia(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        nova_os = os.finalizar(servicos_ativos_com_tempo=[True])

        assert nova_os is not os

    def test_finalizar_preserva_status_original(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        os.finalizar(servicos_ativos_com_tempo=[True])

        assert os.status == StatusOrdemServico.EM_EXECUCAO

    def test_finalizar_preserva_campos_da_os(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        nova_os = os.finalizar(servicos_ativos_com_tempo=[True])

        assert nova_os.id == os.id
        assert nova_os.cliente_id == os.cliente_id
        assert nova_os.queixa_inicial == os.queixa_inicial

    def test_nao_deve_finalizar_os_com_servico_ativo_sem_tempo(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        with pytest.raises(OrdemServicoPossuiServicoSemTempoExecutadoError):
            os.finalizar(servicos_ativos_com_tempo=[True, False])

    def test_nao_deve_finalizar_os_quando_nenhum_servico_tem_tempo(self):
        os = _os_fake(StatusOrdemServico.EM_EXECUCAO)

        with pytest.raises(OrdemServicoPossuiServicoSemTempoExecutadoError):
            os.finalizar(servicos_ativos_com_tempo=[False])

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.AGUARDANDO_ITENS,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    def test_nao_deve_finalizar_os_fora_de_em_execucao(
        self, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            os.finalizar(servicos_ativos_com_tempo=[True])


# ---------------------------------------------------------------------------
# OrdemServicoItem.colocar_em_uso()
# ---------------------------------------------------------------------------

class TestOrdemServicoItemColocarEmUso:
    def test_deve_colocar_item_reservado_em_uso(self):
        item = _osi_fake(StatusItemNaOS.RESERVADO)

        novo_item = item.colocar_em_uso()

        assert novo_item.status == StatusItemNaOS.EM_USO

    def test_colocar_em_uso_retorna_nova_instancia(self):
        item = _osi_fake(StatusItemNaOS.RESERVADO)

        novo_item = item.colocar_em_uso()

        assert novo_item is not item

    def test_colocar_em_uso_preserva_status_original(self):
        item = _osi_fake(StatusItemNaOS.RESERVADO)

        item.colocar_em_uso()

        assert item.status == StatusItemNaOS.RESERVADO

    def test_colocar_em_uso_preserva_campos_do_item(self):
        item = _osi_fake(StatusItemNaOS.RESERVADO)

        novo_item = item.colocar_em_uso()

        assert novo_item.id == item.id
        assert novo_item.ordem_servico_id == item.ordem_servico_id
        assert novo_item.item_estoque_id == item.item_estoque_id
        assert novo_item.nome_item == item.nome_item
        assert novo_item.quantidade == item.quantidade
        assert novo_item.valor_unitario == item.valor_unitario

    def test_nao_deve_colocar_item_a_receber_em_uso(self):
        item = _osi_fake(StatusItemNaOS.A_RECEBER)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.colocar_em_uso()

    def test_nao_deve_colocar_item_cancelado_em_uso(self):
        item = _osi_fake(StatusItemNaOS.CANCELADO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.colocar_em_uso()

    def test_nao_deve_colocar_item_em_uso_novamente(self):
        item = _osi_fake(StatusItemNaOS.EM_USO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.colocar_em_uso()

    def test_nao_deve_colocar_item_consumido_em_uso(self):
        item = _osi_fake(StatusItemNaOS.CONSUMIDO)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.colocar_em_uso()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusItemNaOS.A_RECEBER,
            StatusItemNaOS.CANCELADO,
            StatusItemNaOS.EM_USO,
            StatusItemNaOS.CONSUMIDO,
        ],
    )
    def test_status_invalidos_levantam_erro_ao_colocar_em_uso(
        self, status_invalido: StatusItemNaOS
    ):
        item = _osi_fake(status_invalido)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            item.colocar_em_uso()


# ---------------------------------------------------------------------------
# OrdemServicoServico.registrar_tempo_executado()
# ---------------------------------------------------------------------------

class TestOrdemServicoServicoRegistrarTempoExecutado:
    def test_deve_registrar_tempo_executado_em_servico_ativo(self):
        servico = _oss_fake(cancelado=False, tempo_executado_minutos=None)

        novo_servico = servico.registrar_tempo_executado(75)

        assert novo_servico.tempo_executado_minutos == 75

    def test_registrar_tempo_retorna_nova_instancia(self):
        servico = _oss_fake()

        novo_servico = servico.registrar_tempo_executado(60)

        assert novo_servico is not servico

    def test_registrar_tempo_preserva_tempo_original_como_none(self):
        servico = _oss_fake(tempo_executado_minutos=None)

        servico.registrar_tempo_executado(60)

        assert servico.tempo_executado_minutos is None

    def test_registrar_tempo_preserva_campos_do_servico(self):
        servico = _oss_fake()

        novo_servico = servico.registrar_tempo_executado(45)

        assert novo_servico.id == servico.id
        assert novo_servico.ordem_servico_id == servico.ordem_servico_id
        assert novo_servico.servico_id == servico.servico_id
        assert novo_servico.nome_servico == servico.nome_servico
        assert novo_servico.valor_unitario == servico.valor_unitario
        assert novo_servico.cancelado == servico.cancelado

    def test_deve_sobrescrever_tempo_executado_em_servico_ativo(self):
        servico = _oss_fake(tempo_executado_minutos=60)

        novo_servico = servico.registrar_tempo_executado(90)

        assert novo_servico.tempo_executado_minutos == 90

    def test_sobrescrita_preserva_valor_anterior_no_original(self):
        servico = _oss_fake(tempo_executado_minutos=60)

        servico.registrar_tempo_executado(90)

        assert servico.tempo_executado_minutos == 60

    def test_nao_deve_registrar_tempo_zero(self):
        servico = _oss_fake()

        with pytest.raises(TempoExecutadoInvalidoError):
            servico.registrar_tempo_executado(0)

    def test_nao_deve_registrar_tempo_negativo(self):
        servico = _oss_fake()

        with pytest.raises(TempoExecutadoInvalidoError):
            servico.registrar_tempo_executado(-10)

    def test_nao_deve_registrar_tempo_em_servico_cancelado(self):
        servico = _oss_fake(cancelado=True)

        with pytest.raises(OrdemServicoServicoCanceladoError):
            servico.registrar_tempo_executado(30)

    def test_servico_cancelado_levanta_erro_antes_de_validar_tempo(self):
        """Serviço cancelado deve falhar mesmo que o tempo seja válido."""
        servico = _oss_fake(cancelado=True)

        with pytest.raises(OrdemServicoServicoCanceladoError):
            servico.registrar_tempo_executado(60)

    @pytest.mark.parametrize("tempo_invalido", [0, -1, -100])
    def test_tempos_invalidos_levantam_erro(self, tempo_invalido: int):
        servico = _oss_fake()

        with pytest.raises(TempoExecutadoInvalidoError):
            servico.registrar_tempo_executado(tempo_invalido)
