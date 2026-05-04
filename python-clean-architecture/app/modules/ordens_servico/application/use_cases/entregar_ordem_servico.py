"""Use case: Entregar uma Ordem de Serviço (FINALIZADA -> ENTREGUE)."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.exceptions import ItemEstoqueNaoEncontradoError
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoDetalheResponse
from app.modules.ordens_servico.application.use_cases.obter_ordem_servico_por_id import _to_detalhe
from app.modules.ordens_servico.domain.entities.ordem_servico_item import StatusItemNaOS
from app.modules.ordens_servico.domain.exceptions import (
    EstoqueReservadoInsuficienteError,
    ItemOrdemServicoStatusInvalidoError,
    OrdemServicoPagamentoNaoRegistradoError,
    OrdemServicoPossuiItemPendenteError,
    OrdemServicoPossuiItemReservadoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class EntregarOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(self, ordem_servico_id: str) -> OrdemServicoDetalheResponse:
        _id = ID.from_string(ordem_servico_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Validar e transitar OS via domínio (valida FINALIZADA + pagamento registrado)
            os_entregue = os.entregar()

            # 3. Buscar itens da OS
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)

            # 4. Validar itens: A_RECEBER e RESERVADO bloqueiam entrega
            for item in itens:
                if item.status == StatusItemNaOS.A_RECEBER:
                    raise OrdemServicoPossuiItemPendenteError(
                        f"Não é possível entregar OS com item ativo em status "
                        f"'{item.status.value}'."
                    )
                if item.status == StatusItemNaOS.RESERVADO:
                    raise OrdemServicoPossuiItemReservadoError(
                        f"Não é possível entregar OS com item ativo em status "
                        f"'{item.status.value}'."
                    )

            # 5. Processar itens EM_USO: consumir + baixar estoque reservado
            itens_atualizados = []
            for item in itens:
                if item.status != StatusItemNaOS.EM_USO:
                    itens_atualizados.append(item)
                    continue

                # 5a. Consumir item via domínio
                item_consumido = item.consumir()

                # 5b. Buscar ItemEstoque com lock pessimista
                item_estoque = await self.uow.item_estoque_repo.obter_por_id_com_lock(
                    ID.from_string(str(item.item_estoque_id))
                )
                if not item_estoque:
                    raise ItemEstoqueNaoEncontradoError(
                        f"Item de estoque '{item.item_estoque_id}' não encontrado."
                    )

                # 5c. Validar reserva suficiente
                if item_estoque.quantidade_reservada < item.quantidade:
                    raise EstoqueReservadoInsuficienteError(
                        "Quantidade reservada insuficiente para consumir item "
                        "da ordem de serviço."
                    )

                # 5d. Baixar quantidade_reservada (quantidade_disponivel não muda)
                from datetime import UTC, datetime
                agora = datetime.now(UTC)
                item_estoque_atualizado = ItemEstoque(
                    id=item_estoque.id,
                    tipo=item_estoque.tipo,
                    nome=item_estoque.nome,
                    descricao=item_estoque.descricao,
                    codigo=item_estoque.codigo,
                    valor_unitario=item_estoque.valor_unitario,
                    quantidade_disponivel=item_estoque.quantidade_disponivel,
                    quantidade_reservada=item_estoque.quantidade_reservada - item.quantidade,
                    quantidade_minima=item_estoque.quantidade_minima,
                    ativo=item_estoque.ativo,
                    criado_em=item_estoque.criado_em,
                    atualizado_em=agora,
                )
                await self.uow.item_estoque_repo.atualizar(item_estoque_atualizado)

                # 5e. Persistir item consumido
                await self.uow.ordem_servico_repo.atualizar_item(item_consumido)
                itens_atualizados.append(item_consumido)

            # 6. Persistir OS como ENTREGUE
            await self.uow.ordem_servico_repo.atualizar(os_entregue)

            # 7. Commit único
            await self.uow.commit()

            # 8. Buscar serviços para montar resposta
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_id)

            logger.info(f"OS '{ordem_servico_id}' entregue com sucesso.")
            return _to_detalhe(os_entregue, servicos, itens_atualizados)
