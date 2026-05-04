"""Testes unitários de application para a Etapa 5 — Pagamento simples e entrega da OS.

Cobre:
  - RegistrarPagamentoOrdemServicoUseCase
  - EntregarOrdemServicoUseCase
"""

import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque, TipoItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    RegistrarPagamentoOrdemServicoRequest,
)
from app.modules.ordens_servico.application.use_cases.registrar_pagamento_ordem_servico import (
    RegistrarPagamentoOrdemServicoUseCase,
)
from app.modules.ordens_servico.application.use_cases.entregar_ordem_servico import (
    EntregarOrdemServicoUseCase,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import (
    OrdemServico,
    StatusOrdemServico,
)
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento, StatusOrcamento
from app.modules.ordens_servico.domain.enums import FormaPagamento
from app.modules.ordens_servico.domain.exceptions import (
    EstoqueReservadoInsuficienteError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoPagamentoJaRegistradoError,
    OrdemServicoPagamentoNaoRegistradoError,
    OrdemServicoPossuiItemPendenteError,
    OrdemServicoPossuiItemReservadoError,
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
    return _os_fake(
        status=StatusOrdemServico.FINALIZADA,
        pagamento_registrado_em=_agora(),
        forma_pagamento=FormaPagamento.PIX.value,
        valor_pago=Decimal("270.00"),
        pagamento_observacao="Pago via PIX",
    )


def _osi_fake(
    os: OrdemServico,
    status: StatusItemNaOS = StatusItemNaOS.EM_USO,
    quantidade: int = 2,
    item_estoque_id: _uuid.UUID | None = None,
) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=_uuid.UUID(str(os.id)),
        item_estoque_id=item_estoque_id or uuid4(),
        nome_item="Filtro de óleo",
        tipo_item="PECA",
        quantidade=quantidade,
        valor_unitario=Decimal("35.00"),
        status=status,
    )


def _item_estoque_fake(
    item_estoque_id: _uuid.UUID | None = None,
    disponivel: int = 8,
    reservada: int = 2,
) -> ItemEstoque:
    agora = _agora()
    return ItemEstoque(
        id=ID.from_string(str(item_estoque_id)) if item_estoque_id else ID.generate(),
        tipo=TipoItemEstoque.PECA,
        nome="Filtro de óleo",
        descricao="Filtro de óleo do motor",
        codigo="FO-001",
        quantidade_disponivel=disponivel,
        quantidade_reservada=reservada,
        quantidade_minima=1,
        valor_unitario=Decimal("35.00"),
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )


def _orcamento_fake(
    os: OrdemServico,
    status: StatusOrcamento = StatusOrcamento.APROVADO,
    total_geral: Decimal = Decimal("270.00"),
) -> Orcamento:
    agora = _agora()
    total_servicos = Decimal("180.00")
    total_itens = total_geral - total_servicos
    return Orcamento(
        id=ID.generate(),
        ordem_servico_id=_uuid.UUID(str(os.id)),
        status=status,
        total_servicos=total_servicos,
        total_itens=total_itens,
        total_geral=total_geral,
        criado_em=agora,
        atualizado_em=agora,
        comunicado_em=agora,
        observacao=None,
        respondido_em=agora,
        motivo_recusa=None,
    )


def _dto_pagamento(
    forma_pagamento: str = FormaPagamento.PIX.value,
    valor_pago: Decimal = Decimal("270.00"),
    observacao: str | None = "Pagamento recebido via PIX.",
) -> RegistrarPagamentoOrdemServicoRequest:
    return RegistrarPagamentoOrdemServicoRequest(
        forma_pagamento=forma_pagamento,
        valor_pago=valor_pago,
        observacao=observacao,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_os_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.listar_itens_da_os = AsyncMock(return_value=[])
    repo.listar_servicos_da_os = AsyncMock(return_value=[])
    repo.obter_orcamento_por_ordem_servico_id = AsyncMock(return_value=None)
    repo.atualizar = AsyncMock()
    repo.atualizar_item = AsyncMock()
    return repo


@pytest.fixture
def mock_item_estoque_repo():
    repo = MagicMock()
    repo.obter_por_id_com_lock = AsyncMock(return_value=None)
    repo.atualizar = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_os_repo, mock_item_estoque_repo):
    uow = MagicMock()
    uow.ordem_servico_repo = mock_os_repo
    uow.item_estoque_repo = mock_item_estoque_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


# ---------------------------------------------------------------------------
# RegistrarPagamentoOrdemServicoUseCase
# ---------------------------------------------------------------------------

class TestRegistrarPagamentoOrdemServicoUseCase:

    async def test_deve_registrar_pagamento_de_os_finalizada(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        orcamento = _orcamento_fake(os, total_geral=Decimal("270.00"))

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(
            return_value=orcamento
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), _dto_pagamento())

        assert resultado.status == StatusOrdemServico.FINALIZADA.value
        assert resultado.pagamento_registrado_em is not None
        assert resultado.forma_pagamento == FormaPagamento.PIX.value
        assert resultado.valor_pago == Decimal("270.00")
        assert resultado.pagamento_observacao == "Pagamento recebido via PIX."
        mock_uow.commit.assert_called_once()

    async def test_deve_registrar_pagamento_maior_que_total_do_orcamento(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        orcamento = _orcamento_fake(os, total_geral=Decimal("270.00"))

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(
            return_value=orcamento
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(
            str(os.id),
            _dto_pagamento(valor_pago=Decimal("300.00")),
        )

        assert resultado.valor_pago == Decimal("300.00")
        mock_uow.commit.assert_called_once()

    async def test_deve_registrar_pagamento_sem_observacao(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(
            str(os.id),
            _dto_pagamento(observacao=None),
        )

        assert resultado.pagamento_observacao is None
        assert resultado.pagamento_registrado_em is not None
        mock_uow.commit.assert_called_once()

    async def test_deve_lidar_com_orcamento_nao_encontrado(self, mock_uow):
        """Sem orçamento aprovado, registra pagamento validando apenas valor > 0."""
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(
            return_value=None
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), _dto_pagamento())

        assert resultado.pagamento_registrado_em is not None
        mock_uow.commit.assert_called_once()

    async def test_nao_deve_registrar_pagamento_de_os_inexistente(self, mock_uow):
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()), _dto_pagamento())

        mock_uow.commit.assert_not_called()

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
    async def test_nao_deve_registrar_pagamento_de_os_fora_de_finalizada(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id), _dto_pagamento())

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_pagamento_duplicado(self, mock_uow):
        os = _os_fake(
            StatusOrdemServico.FINALIZADA,
            pagamento_registrado_em=_agora(),
            forma_pagamento=FormaPagamento.PIX.value,
            valor_pago=Decimal("270.00"),
        )
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPagamentoJaRegistradoError):
            await uc.execute(str(os.id), _dto_pagamento())

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_pagamento_com_valor_zero(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ValorPagamentoInvalidoError):
            await uc.execute(str(os.id), _dto_pagamento(valor_pago=Decimal("0.00")))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_pagamento_com_valor_negativo(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ValorPagamentoInvalidoError):
            await uc.execute(str(os.id), _dto_pagamento(valor_pago=Decimal("-1.00")))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_pagamento_menor_que_orcamento_aprovado(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        orcamento = _orcamento_fake(os, total_geral=Decimal("270.00"))

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(
            return_value=orcamento
        )

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ValorPagamentoMenorQueOrcamentoError):
            await uc.execute(str(os.id), _dto_pagamento(valor_pago=Decimal("269.99")))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_registrar_pagamento_com_forma_invalida(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ValorPagamentoInvalidoError):
            await uc.execute(
                str(os.id),
                _dto_pagamento(forma_pagamento="CRIPTOMOEDA"),
            )

        mock_uow.commit.assert_not_called()

    async def test_registrar_pagamento_nao_deve_alterar_estoque(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        # Sobrescreve repo de estoque para garantir que não é chamado
        estoque_repo = MagicMock()
        estoque_repo.obter_por_id_com_lock = AsyncMock()
        estoque_repo.atualizar = AsyncMock()
        mock_uow.item_estoque_repo = estoque_repo

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id), _dto_pagamento())

        estoque_repo.obter_por_id_com_lock.assert_not_called()
        estoque_repo.atualizar.assert_not_called()

    async def test_registrar_pagamento_nao_deve_alterar_itens(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        item_em_uso = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_em_uso]
        )
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), _dto_pagamento())

        # nenhuma chamada a atualizar_item deve ter sido feita
        mock_uow.ordem_servico_repo.atualizar_item.assert_not_called()

        # item na resposta continua EM_USO
        item_na_resposta = resultado.itens[0]
        assert item_na_resposta.status == StatusItemNaOS.EM_USO.value

    async def test_orcamento_nao_aprovado_nao_e_usado_para_validacao(self, mock_uow):
        """Orçamento GERADO/COMUNICADO/RECUSADO não deve ser usado como limite de valor."""
        os = _os_fake(StatusOrdemServico.FINALIZADA)
        orcamento_nao_aprovado = _orcamento_fake(
            os, status=StatusOrcamento.COMUNICADO, total_geral=Decimal("270.00")
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id = AsyncMock(
            return_value=orcamento_nao_aprovado
        )
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = RegistrarPagamentoOrdemServicoUseCase(uow=mock_uow)
        # valor abaixo do orçamento, mas orçamento não está APROVADO — deve passar
        resultado = await uc.execute(
            str(os.id), _dto_pagamento(valor_pago=Decimal("1.00"))
        )

        assert resultado.pagamento_registrado_em is not None
        mock_uow.commit.assert_called_once()


# ---------------------------------------------------------------------------
# EntregarOrdemServicoUseCase
# ---------------------------------------------------------------------------

class TestEntregarOrdemServicoUseCase:

    async def test_deve_entregar_os_finalizada_paga_e_consumir_item_em_uso(self, mock_uow):
        os = _os_finalizada_paga()
        ie_id = uuid4()
        item = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=2, item_estoque_id=ie_id)
        item_estoque = _item_estoque_fake(
            item_estoque_id=ie_id, disponivel=8, reservada=2
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(
            return_value=item_estoque
        )

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        # OS vira ENTREGUE
        assert resultado.status == StatusOrdemServico.ENTREGUE.value

        # Item vira CONSUMIDO
        item_na_resposta = resultado.itens[0]
        assert item_na_resposta.status == StatusItemNaOS.CONSUMIDO.value

        # Estoque: disponivel inalterado, reservada zerada
        item_estoque_atualizado = mock_uow.item_estoque_repo.atualizar.call_args[0][0]
        assert item_estoque_atualizado.quantidade_disponivel == 8
        assert item_estoque_atualizado.quantidade_reservada == 0

        mock_uow.commit.assert_called_once()

    async def test_deve_consumir_multiplos_itens_em_uso(self, mock_uow):
        os = _os_finalizada_paga()
        ie1_id = uuid4()
        ie2_id = uuid4()
        item1 = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=2, item_estoque_id=ie1_id)
        item2 = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=1, item_estoque_id=ie2_id)
        ie1 = _item_estoque_fake(item_estoque_id=ie1_id, disponivel=8, reservada=2)
        ie2 = _item_estoque_fake(item_estoque_id=ie2_id, disponivel=5, reservada=1)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item1, item2]
        )
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(
            side_effect=[ie1, ie2]
        )

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.ENTREGUE.value
        assert all(i.status == StatusItemNaOS.CONSUMIDO.value for i in resultado.itens)
        assert mock_uow.item_estoque_repo.atualizar.call_count == 2
        assert mock_uow.commit.call_count == 1

        # Checar que cada estoque teve reservada reduzida corretamente
        calls = mock_uow.item_estoque_repo.atualizar.call_args_list
        ie1_atualizado = calls[0][0][0]
        ie2_atualizado = calls[1][0][0]
        assert ie1_atualizado.quantidade_reservada == 0  # 2 - 2
        assert ie2_atualizado.quantidade_reservada == 0  # 1 - 1

    async def test_deve_ignorar_item_cancelado_na_entrega(self, mock_uow):
        os = _os_finalizada_paga()
        ie_id = uuid4()
        item_em_uso = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=1, item_estoque_id=ie_id)
        item_cancelado = _osi_fake(os, StatusItemNaOS.CANCELADO)
        ie = _item_estoque_fake(item_estoque_id=ie_id, disponivel=5, reservada=1)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_em_uso, item_cancelado]
        )
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=ie)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.ENTREGUE.value
        # lock de estoque chamado apenas uma vez (somente item EM_USO)
        assert mock_uow.item_estoque_repo.obter_por_id_com_lock.call_count == 1
        mock_uow.commit.assert_called_once()

    async def test_entregar_nao_deve_alterar_quantidade_disponivel(self, mock_uow):
        os = _os_finalizada_paga()
        ie_id = uuid4()
        item = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=2, item_estoque_id=ie_id)
        ie = _item_estoque_fake(item_estoque_id=ie_id, disponivel=8, reservada=2)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=ie)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id))

        ie_atualizado = mock_uow.item_estoque_repo.atualizar.call_args[0][0]
        assert ie_atualizado.quantidade_disponivel == 8
        assert ie_atualizado.quantidade_reservada == 0

    async def test_deve_usar_lock_pessimista_ao_baixar_estoque(self, mock_uow):
        os = _os_finalizada_paga()
        ie_id = uuid4()
        item = _osi_fake(os, StatusItemNaOS.EM_USO, item_estoque_id=ie_id)
        ie = _item_estoque_fake(item_estoque_id=ie_id, reservada=2)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=ie)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id))

        # obter_por_id_com_lock deve ser chamado com o ID do item de estoque
        chamado_com = mock_uow.item_estoque_repo.obter_por_id_com_lock.call_args[0][0]
        assert str(chamado_com) == str(ID.from_string(str(ie_id)))

    async def test_nao_deve_entregar_os_inexistente(self, mock_uow):
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=None)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()))

        mock_uow.commit.assert_not_called()

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
    async def test_nao_deve_entregar_os_fora_de_finalizada(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_entregar_os_sem_pagamento_registrado(self, mock_uow):
        os = _os_fake(StatusOrdemServico.FINALIZADA)  # sem pagamento
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPagamentoNaoRegistradoError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_entregar_com_item_a_receber(self, mock_uow):
        os = _os_finalizada_paga()
        item = _osi_fake(os, StatusItemNaOS.A_RECEBER)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPossuiItemPendenteError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_entregar_com_item_reservado(self, mock_uow):
        os = _os_finalizada_paga()
        item = _osi_fake(os, StatusItemNaOS.RESERVADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoPossuiItemReservadoError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_entregar_se_item_estoque_nao_existir(self, mock_uow):
        os = _os_finalizada_paga()
        item = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=None)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemEstoqueNaoEncontradoError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        # item da OS não deve ter sido persistido como CONSUMIDO
        mock_uow.ordem_servico_repo.atualizar.assert_not_called()

    async def test_nao_deve_entregar_se_estoque_reservado_for_insuficiente(self, mock_uow):
        os = _os_finalizada_paga()
        ie_id = uuid4()
        item = _osi_fake(os, StatusItemNaOS.EM_USO, quantidade=3, item_estoque_id=ie_id)
        # reservado=1 < quantidade=3
        ie = _item_estoque_fake(item_estoque_id=ie_id, disponivel=8, reservada=1)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=ie)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(EstoqueReservadoInsuficienteError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_baixar_estoque_de_item_ja_consumido(self, mock_uow):
        """Item CONSUMIDO antes da entrega não deve acionar baixa de estoque."""
        os = _os_finalizada_paga()
        item_consumido = _osi_fake(os, StatusItemNaOS.CONSUMIDO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_consumido]
        )
        mock_uow.ordem_servico_repo.listar_servicos_da_os = AsyncMock(return_value=[])

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id))

        assert resultado.status == StatusOrdemServico.ENTREGUE.value
        # nenhum lock nem atualização de estoque para item já CONSUMIDO
        mock_uow.item_estoque_repo.obter_por_id_com_lock.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_entregar_duas_vezes(self, mock_uow):
        os = _os_fake(StatusOrdemServico.ENTREGUE)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.obter_por_id_com_lock.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_chamar_commit_quando_ocorrer_erro_na_entrega(self, mock_uow):
        """Qualquer erro na entrega não deve chamar commit."""
        os = _os_finalizada_paga()
        item = _osi_fake(os, StatusItemNaOS.EM_USO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        # lock retorna None → ItemEstoqueNaoEncontradoError
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=None)

        uc = EntregarOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemEstoqueNaoEncontradoError):
            await uc.execute(str(os.id))

        mock_uow.commit.assert_not_called()
