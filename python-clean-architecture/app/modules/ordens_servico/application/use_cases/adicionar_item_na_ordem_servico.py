"""Use case: Adicionar Item de Estoque a uma Ordem de Serviço."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    AdicionarItemNaOSRequest,
    OrdemServicoItemResponse,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import (
    OrdemServicoItem,
    StatusItemNaOS,
)
from app.modules.ordens_servico.domain.exceptions import (
    ItemJaAdicionadoNaOrdemServicoError,
    OrdemServicoInvalidaError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AdicionarItemNaOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self, ordem_servico_id: str, dto: AdicionarItemNaOSRequest
    ) -> OrdemServicoItemResponse:
        if dto.quantidade <= 0:
            raise OrdemServicoInvalidaError("A quantidade deve ser maior que zero.")

        os_id = ID.from_string(ordem_servico_id)
        item_id = ID.from_string(dto.item_estoque_id)

        async with self.uow:
            os = await self.uow.ordem_servico_repo.obter_por_id(os_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            if os.status != StatusOrdemServico.EM_DIAGNOSTICO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível adicionar itens em OS com status "
                    f"'EM_DIAGNOSTICO'. Status atual: '{os.status.value}'."
                )

            # Verificar duplicidade ativa — antes de qualquer alteração no estoque
            existente = await self.uow.ordem_servico_repo.obter_item_ativo_por_item_estoque_id(
                os_id, item_id
            )
            if existente:
                raise ItemJaAdicionadoNaOrdemServicoError(
                    "Item já foi adicionado a esta ordem de serviço."
                )

            # Busca com lock pessimista para evitar condição de corrida
            item_estoque = await self.uow.item_estoque_repo.obter_por_id_com_lock(item_id)
            if not item_estoque:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque com ID {dto.item_estoque_id} não encontrado."
                )

            # Tentar reservar quantidade
            if item_estoque.quantidade_disponivel >= dto.quantidade:
                # Há saldo suficiente — reservar imediatamente
                from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
                from datetime import UTC, datetime

                item_atualizado = ItemEstoque(
                    id=item_estoque.id,
                    tipo=item_estoque.tipo,
                    nome=item_estoque.nome,
                    descricao=item_estoque.descricao,
                    codigo=item_estoque.codigo,
                    quantidade_disponivel=item_estoque.quantidade_disponivel - dto.quantidade,
                    quantidade_reservada=item_estoque.quantidade_reservada + dto.quantidade,
                    quantidade_minima=item_estoque.quantidade_minima,
                    valor_unitario=item_estoque.valor_unitario,
                    ativo=item_estoque.ativo,
                    criado_em=item_estoque.criado_em,
                    atualizado_em=datetime.now(UTC),
                )
                await self.uow.item_estoque_repo.atualizar(item_atualizado)
                status_item = StatusItemNaOS.RESERVADO
                logger.info(
                    f"Item '{dto.item_estoque_id}' reservado ({dto.quantidade} un.) para OS '{ordem_servico_id}'"
                )
            else:
                # Sem saldo suficiente — marcar como A_RECEBER sem alterar estoque
                status_item = StatusItemNaOS.A_RECEBER
                logger.info(
                    f"Item '{dto.item_estoque_id}' marcado como A_RECEBER na OS '{ordem_servico_id}' "
                    f"(disponível: {item_estoque.quantidade_disponivel}, solicitado: {dto.quantidade})"
                )

            os_item = OrdemServicoItem(
                id=ID.generate(),
                ordem_servico_id=UUID(ordem_servico_id),
                item_estoque_id=UUID(dto.item_estoque_id),
                nome_item=item_estoque.nome,
                tipo_item=item_estoque.tipo.value,
                quantidade=dto.quantidade,
                valor_unitario=Decimal(str(item_estoque.valor_unitario)),
                status=status_item,
            )

            await self.uow.ordem_servico_repo.salvar_item(os_item)

        return OrdemServicoItemResponse(
            id=str(os_item.id),
            item_estoque_id=str(os_item.item_estoque_id),
            nome_item=os_item.nome_item,
            tipo_item=os_item.tipo_item,
            quantidade=os_item.quantidade,
            valor_unitario=os_item.valor_unitario,
            status=os_item.status.value,
        )
