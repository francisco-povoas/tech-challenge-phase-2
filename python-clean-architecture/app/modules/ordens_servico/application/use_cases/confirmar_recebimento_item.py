"""Use case: Confirmar Recebimento de Item A_RECEBER de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoDetalheResponse
from app.modules.ordens_servico.application.use_cases.obter_ordem_servico_por_id import _to_detalhe
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import StatusItemNaOS
from app.modules.ordens_servico.domain.exceptions import (
    ItemOrdemServicoStatusInvalidoError,
    OrdemServicoItemNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ConfirmarRecebimentoItemDaOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self,
        ordem_servico_id: str,
        ordem_servico_item_id: str,
    ) -> OrdemServicoDetalheResponse:
        _os_id = ID.from_string(ordem_servico_id)
        _item_id = ID.from_string(ordem_servico_item_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Validar status da OS
            if os.status != StatusOrdemServico.AGUARDANDO_ITENS:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível confirmar recebimento de item para OS com status "
                    f"'AGUARDANDO_ITENS'. Status atual: '{os.status.value}'."
                )

            # 3. Buscar item da OS
            item = await self.uow.ordem_servico_repo.obter_item_por_id(_item_id)
            if not item:
                raise OrdemServicoItemNaoEncontradoError(
                    "Item da ordem de serviço não encontrado."
                )

            # 4. Validar que item pertence à OS informada
            if str(item.ordem_servico_id) != ordem_servico_id:
                raise OrdemServicoItemNaoEncontradoError(
                    "Item informado não pertence à ordem de serviço."
                )

            # 5. Validar e transitar item A_RECEBER -> RESERVADO (via método de domínio)
            item_reservado = item.confirmar_recebimento()

            # 6. Buscar ItemEstoque com lock pessimista e atualizar quantidade_reservada
            item_estoque = await self.uow.item_estoque_repo.obter_por_id_com_lock(
                ID.from_string(str(item.item_estoque_id))
            )
            if not item_estoque:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque '{item.item_estoque_id}' não encontrado."
                )

            agora = datetime.now(UTC)
            item_estoque_atualizado = ItemEstoque(
                id=item_estoque.id,
                tipo=item_estoque.tipo,
                nome=item_estoque.nome,
                descricao=item_estoque.descricao,
                codigo=item_estoque.codigo,
                valor_unitario=item_estoque.valor_unitario,
                quantidade_disponivel=item_estoque.quantidade_disponivel,
                quantidade_reservada=item_estoque.quantidade_reservada + item.quantidade,
                quantidade_minima=item_estoque.quantidade_minima,
                ativo=item_estoque.ativo,
                criado_em=item_estoque.criado_em,
                atualizado_em=agora,
            )
            await self.uow.item_estoque_repo.atualizar(item_estoque_atualizado)

            # 7. Persistir item atualizado
            await self.uow.ordem_servico_repo.atualizar_item(item_reservado)

            # 8. Verificar se ainda há itens ativos A_RECEBER (excluindo o item atual)
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_os_id)
            # Substituir o item atual pela versão atualizada na lista para checar estado final
            itens_atualizados = [
                item_reservado if str(i.id) == ordem_servico_item_id else i
                for i in itens
            ]
            itens_ativos = [i for i in itens_atualizados if i.status != StatusItemNaOS.CANCELADO]
            tem_a_receber = any(i.status == StatusItemNaOS.A_RECEBER for i in itens_ativos)

            novo_status_os = (
                StatusOrdemServico.AGUARDANDO_ITENS
                if tem_a_receber
                else StatusOrdemServico.APROVADA
            )

            os_atualizada = OrdemServico(
                id=os.id,
                cliente_id=os.cliente_id,
                veiculo_id=os.veiculo_id,
                status=novo_status_os,
                queixa_inicial=os.queixa_inicial,
                diagnostico=os.diagnostico,
                criado_em=os.criado_em,
                atualizado_em=agora,
                iniciado_diagnostico_em=os.iniciado_diagnostico_em,
                diagnostico_concluido_em=os.diagnostico_concluido_em,
            )

            await self.uow.ordem_servico_repo.atualizar(os_atualizada)

            # 9. Buscar servicos para montar resposta dentro da transação
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_os_id)

            await self.uow.commit()

            logger.info(
                f"Recebimento do item '{ordem_servico_item_id}' da OS '{ordem_servico_id}' "
                f"confirmado. OS -> {novo_status_os.value}"
            )

        return _to_detalhe(os_atualizada, servicos, itens_atualizados)
