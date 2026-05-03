"""Testes unitários para ConfirmarRecebimentoItemDaOrdemServicoUseCase."""

import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque, TipoItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.use_cases.confirmar_recebimento_item import (
    ConfirmarRecebimentoItemDaOrdemServicoUseCase,
)
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
    OrdemServicoItemNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agora() -> datetime:
    return datetime.now(UTC)


def _os_fake(
    status: StatusOrdemServico = StatusOrdemServico.AGUARDANDO_ITENS,
) -> OrdemServico:
    agora = _agora()
    return OrdemServico(
        id=ID.generate(),
        cliente_id=uuid4(),
        veiculo_id=uuid4(),
        status=status,
        queixa_inicial="Barulho ao acelerar",
        diagnostico="Correia com desgaste",
        criado_em=agora,
        atualizado_em=agora,
        iniciado_diagnostico_em=agora,
        diagnostico_concluido_em=agora,
    )


def _os_item_fake(
    os: OrdemServico,
    status: StatusItemNaOS = StatusItemNaOS.A_RECEBER,
    quantidade: int = 1,
    item_estoque_id: _uuid.UUID | None = None,
) -> OrdemServicoItem:
    return OrdemServicoItem(
        id=ID.generate(),
        ordem_servico_id=_uuid.UUID(str(os.id)),
        item_estoque_id=item_estoque_id if item_estoque_id is not None else uuid4(),
        nome_item="Correia Alternador",
        tipo_item="PECA",
        quantidade=quantidade,
        valor_unitario=Decimal("220.00"),
        status=status,
    )


def _item_estoque_fake(
    item_estoque_id: _uuid.UUID | None = None,
    disponivel: int = 0,
    reservada: int = 0,
) -> ItemEstoque:
    agora = _agora()
    return ItemEstoque(
        id=ID.from_string(str(item_estoque_id)) if item_estoque_id else ID.generate(),
        tipo=TipoItemEstoque.PECA,
        nome="Correia Alternador",
        descricao="Correia do alternador",
        codigo="CA-001",
        quantidade_disponivel=disponivel,
        quantidade_reservada=reservada,
        quantidade_minima=1,
        valor_unitario=Decimal("220.00"),
        ativo=True,
        criado_em=agora,
        atualizado_em=agora,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_os_repo():
    repo = MagicMock()
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.obter_item_por_id = AsyncMock(return_value=None)
    repo.listar_itens_da_os = AsyncMock(return_value=[])
    repo.listar_servicos_da_os = AsyncMock(return_value=[])
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
# Cenários positivos
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItemUseCase:
    async def test_deve_confirmar_recebimento_do_unico_item_a_receber_e_aprovar_os(
        self, mock_uow
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=item_estoque)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), str(item.id))

        # OS deve virar APROVADA
        assert resultado.status == StatusOrdemServico.APROVADA.value

        # Item deve virar RESERVADO na resposta
        item_na_resposta = next(i for i in resultado.itens if i.id == str(item.id))
        assert item_na_resposta.status == StatusItemNaOS.RESERVADO.value

        # Estoque atualizado: reservada += 1, disponivel inalterado
        item_estoque_atualizado = mock_uow.item_estoque_repo.atualizar.call_args[0][0]
        assert item_estoque_atualizado.quantidade_reservada == 1
        assert item_estoque_atualizado.quantidade_disponivel == 0

        # Commit chamado
        mock_uow.commit.assert_called_once()

    async def test_deve_confirmar_recebimento_e_manter_os_aguardando_itens_quando_ainda_houver_outro_item_a_receber(
        self, mock_uow
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item1 = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item2 = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item1.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item1)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item1, item2]
        )
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(
            return_value=item_estoque
        )

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), str(item1.id))

        # OS deve permanecer AGUARDANDO_ITENS
        assert resultado.status == StatusOrdemServico.AGUARDANDO_ITENS.value

        # item1 RESERVADO, item2 A_RECEBER
        item1_resp = next(i for i in resultado.itens if i.id == str(item1.id))
        item2_resp = next(i for i in resultado.itens if i.id == str(item2.id))
        assert item1_resp.status == StatusItemNaOS.RESERVADO.value
        assert item2_resp.status == StatusItemNaOS.A_RECEBER.value

        mock_uow.commit.assert_called_once()

    async def test_deve_ignorar_item_cancelado_ao_decidir_se_os_vira_aprovada(
        self, mock_uow
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item_a_receber = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_cancelado = _os_item_fake(os, status=StatusItemNaOS.CANCELADO, quantidade=2)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item_a_receber.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item_a_receber)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(
            return_value=[item_a_receber, item_cancelado]
        )
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(
            return_value=item_estoque
        )

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        resultado = await uc.execute(str(os.id), str(item_a_receber.id))

        # Item cancelado não conta como pendente → OS vira APROVADA
        assert resultado.status == StatusOrdemServico.APROVADA.value

        # Item cancelado permanece CANCELADO
        item_cancelado_resp = next(
            i for i in resultado.itens if i.id == str(item_cancelado.id)
        )
        assert item_cancelado_resp.status == StatusItemNaOS.CANCELADO.value

        mock_uow.commit.assert_called_once()

    async def test_deve_aumentar_quantidade_reservada_e_nao_alterar_quantidade_disponivel(
        self, mock_uow
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=2)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item.item_estoque_id,
            disponivel=5,
            reservada=3,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=item_estoque)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id), str(item.id))

        item_estoque_atualizado = mock_uow.item_estoque_repo.atualizar.call_args[0][0]
        assert item_estoque_atualizado.quantidade_disponivel == 5   # inalterado
        assert item_estoque_atualizado.quantidade_reservada == 5    # 3 + 2

    async def test_deve_usar_lock_pessimista_ao_buscar_item_estoque(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=item_estoque)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id), str(item.id))

        # Deve ter chamado obter_por_id_com_lock com o item_estoque_id do item da OS
        mock_uow.item_estoque_repo.obter_por_id_com_lock.assert_called_once()
        id_buscado = mock_uow.item_estoque_repo.obter_por_id_com_lock.call_args[0][0]
        assert str(id_buscado) == str(item.item_estoque_id)

    async def test_deve_persistir_item_os_estoque_e_os(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=item_estoque)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id), str(item.id))

        # Item da OS atualizado
        mock_uow.ordem_servico_repo.atualizar_item.assert_called_once()
        item_atualizado = mock_uow.ordem_servico_repo.atualizar_item.call_args[0][0]
        assert item_atualizado.status == StatusItemNaOS.RESERVADO

        # Estoque atualizado
        mock_uow.item_estoque_repo.atualizar.assert_called_once()

        # OS atualizada
        mock_uow.ordem_servico_repo.atualizar.assert_called_once()
        os_atualizada = mock_uow.ordem_servico_repo.atualizar.call_args[0][0]
        assert os_atualizada.status == StatusOrdemServico.APROVADA

        # Commit chamado
        mock_uow.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Cenários negativos — OS
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItemOsInvalida:
    async def test_nao_deve_confirmar_recebimento_de_os_inexistente(self, mock_uow):
        # mock_os_repo.obter_por_id retorna None por padrão
        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()), str(uuid4()))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusOrdemServico.RECEBIDA,
            StatusOrdemServico.EM_DIAGNOSTICO,
            StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
            StatusOrdemServico.AGUARDANDO_APROVACAO,
            StatusOrdemServico.APROVADA,
            StatusOrdemServico.EM_EXECUCAO,
            StatusOrdemServico.FINALIZADA,
            StatusOrdemServico.ENTREGUE,
            StatusOrdemServico.ENCERRADA,
        ],
    )
    async def test_nao_deve_confirmar_recebimento_se_os_nao_estiver_aguardando_itens(
        self, mock_uow, status_invalido: StatusOrdemServico
    ):
        os = _os_fake(status=status_invalido)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id), str(uuid4()))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()


# ---------------------------------------------------------------------------
# Cenários negativos — item da OS
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItemNaoEncontrado:
    async def test_nao_deve_confirmar_recebimento_de_item_inexistente(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        # obter_item_por_id retorna None por padrão

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoItemNaoEncontradoError):
            await uc.execute(str(os.id), str(uuid4()))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_confirmar_recebimento_de_item_que_nao_pertence_a_os(
        self, mock_uow
    ):
        os_a = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        os_b = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        # Item pertence à OS B
        item_de_os_b = _os_item_fake(os_b, status=StatusItemNaOS.A_RECEBER)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os_a)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item_de_os_b)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoItemNaoEncontradoError):
            await uc.execute(str(os_a.id), str(item_de_os_b.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()


# ---------------------------------------------------------------------------
# Cenários negativos — status do item
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItemStatusInvalido:
    @pytest.mark.parametrize(
        "status_invalido",
        [
            StatusItemNaOS.RESERVADO,
            StatusItemNaOS.CANCELADO,
            StatusItemNaOS.EM_USO,
            StatusItemNaOS.CONSUMIDO,
        ],
    )
    async def test_nao_deve_confirmar_recebimento_de_item_com_status_invalido(
        self, mock_uow, status_invalido: StatusItemNaOS
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=status_invalido)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()

    async def test_nao_deve_confirmar_recebimento_de_item_reservado(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.RESERVADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_confirmar_recebimento_de_item_cancelado(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.CANCELADO)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Cenários negativos — ItemEstoque
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoItemEstoqueInexistente:
    async def test_nao_deve_confirmar_recebimento_se_item_estoque_nao_existir(
        self, mock_uow
    ):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        # obter_por_id_com_lock retorna None (padrão da fixture)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemEstoqueNaoEncontradoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()
        mock_uow.item_estoque_repo.atualizar.assert_not_called()


# ---------------------------------------------------------------------------
# Garantias de commit / ausência de commit em erro
# ---------------------------------------------------------------------------

class TestConfirmarRecebimentoCommit:
    async def test_nao_deve_chamar_commit_quando_os_nao_encontrada(self, mock_uow):
        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoNaoEncontradaError):
            await uc.execute(str(uuid4()), str(uuid4()))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_chamar_commit_quando_status_os_invalido(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.APROVADA)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoTransicaoInvalidaError):
            await uc.execute(str(os.id), str(uuid4()))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_chamar_commit_quando_item_nao_encontrado(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(OrdemServicoItemNaoEncontradoError):
            await uc.execute(str(os.id), str(uuid4()))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_chamar_commit_quando_status_item_invalido(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.RESERVADO)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemOrdemServicoStatusInvalidoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()

    async def test_nao_deve_chamar_commit_quando_item_estoque_inexistente(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        # obter_por_id_com_lock retorna None por padrão

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)

        with pytest.raises(ItemEstoqueNaoEncontradoError):
            await uc.execute(str(os.id), str(item.id))

        mock_uow.commit.assert_not_called()

    async def test_deve_chamar_commit_exatamente_uma_vez_em_sucesso(self, mock_uow):
        os = _os_fake(status=StatusOrdemServico.AGUARDANDO_ITENS)
        item = _os_item_fake(os, status=StatusItemNaOS.A_RECEBER, quantidade=1)
        item_estoque = _item_estoque_fake(
            item_estoque_id=item.item_estoque_id,
            disponivel=0,
            reservada=0,
        )

        mock_uow.ordem_servico_repo.obter_por_id = AsyncMock(return_value=os)
        mock_uow.ordem_servico_repo.obter_item_por_id = AsyncMock(return_value=item)
        mock_uow.ordem_servico_repo.listar_itens_da_os = AsyncMock(return_value=[item])
        mock_uow.item_estoque_repo.obter_por_id_com_lock = AsyncMock(return_value=item_estoque)

        uc = ConfirmarRecebimentoItemDaOrdemServicoUseCase(uow=mock_uow)
        await uc.execute(str(os.id), str(item.id))

        assert mock_uow.commit.call_count == 1
