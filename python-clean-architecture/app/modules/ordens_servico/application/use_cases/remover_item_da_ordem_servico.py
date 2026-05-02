"""Use case: Remover (cancelar) Item de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoInvalidaError,
    OrdemServicoItemNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RemoverItemDaOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self, ordem_servico_id: str, ordem_servico_item_id: str
    ) -> None:
        os_id = ID.from_string(ordem_servico_id)
        osi_id = ID.from_string(ordem_servico_item_id)

        async with self.uow:
            os = await self.uow.ordem_servico_repo.obter_por_id(os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            if os.status != StatusOrdemServico.EM_DIAGNOSTICO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível remover itens em OS com status "
                    f"'EM_DIAGNOSTICO'. Status atual: '{os.status.value}'."
                )

            os_item = await self.uow.ordem_servico_repo.obter_item_por_id(osi_id)
            if not os_item:
                raise OrdemServicoItemNaoEncontradoError(
                    f"Item com ID {ordem_servico_item_id} não encontrado na OS."
                )

            if str(os_item.ordem_servico_id) != ordem_servico_id:
                raise OrdemServicoItemNaoEncontradoError(
                    f"Item com ID {ordem_servico_item_id} não pertence à OS {ordem_servico_id}."
                )

            if os_item.status == StatusItemNaOS.CANCELADO:
                raise OrdemServicoInvalidaError("O item já foi cancelado.")

            # Se estava RESERVADO, devolver saldo ao estoque
            if os_item.status == StatusItemNaOS.RESERVADO:
                item_id = ID.from_string(str(os_item.item_estoque_id))
                item_estoque = await self.uow.item_estoque_repo.obter_por_id_com_lock(item_id)
                if item_estoque:
                    item_atualizado = ItemEstoque(
                        id=item_estoque.id,
                        tipo=item_estoque.tipo,
                        nome=item_estoque.nome,
                        descricao=item_estoque.descricao,
                        codigo=item_estoque.codigo,
                        quantidade_disponivel=item_estoque.quantidade_disponivel + os_item.quantidade,
                        quantidade_reservada=max(0, item_estoque.quantidade_reservada - os_item.quantidade),
                        quantidade_minima=item_estoque.quantidade_minima,
                        valor_unitario=item_estoque.valor_unitario,
                        ativo=item_estoque.ativo,
                        criado_em=item_estoque.criado_em,
                        atualizado_em=datetime.now(UTC),
                    )
                    await self.uow.item_estoque_repo.atualizar(item_atualizado)
                    logger.info(
                        f"Estoque devolvido: {os_item.quantidade} un. do item "
                        f"'{os_item.item_estoque_id}' retornadas ao estoque"
                    )

            # Cancelar item na OS
            os_item_cancelado = OrdemServicoItem(
                id=os_item.id,
                ordem_servico_id=os_item.ordem_servico_id,
                item_estoque_id=os_item.item_estoque_id,
                nome_item=os_item.nome_item,
                tipo_item=os_item.tipo_item,
                quantidade=os_item.quantidade,
                valor_unitario=os_item.valor_unitario,
                status=StatusItemNaOS.CANCELADO,
            )

            await self.uow.ordem_servico_repo.atualizar_item(os_item_cancelado)
            logger.info(
                f"Item '{ordem_servico_item_id}' cancelado da OS '{ordem_servico_id}'"
            )
