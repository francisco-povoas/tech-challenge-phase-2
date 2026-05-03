"""Use case: Recusar Orçamento de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.ordens_servico.application.dtos.ordem_servico import OrcamentoResponse
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import OrdemServicoItem, StatusItemNaOS
from app.modules.ordens_servico.domain.exceptions import (
    OrcamentoNaoEncontradoError,
    OrcamentoStatusInvalidoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RecusarOrcamentoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self,
        ordem_servico_id: str,
        motivo_recusa: Optional[str] = None,
    ) -> OrcamentoResponse:
        _id = ID.from_string(ordem_servico_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Validar status da OS
            if os.status != StatusOrdemServico.AGUARDANDO_APROVACAO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível recusar orçamento de OS com status "
                    f"'AGUARDANDO_APROVACAO'. Status atual: '{os.status.value}'."
                )

            # 3. Buscar orçamento
            orcamento = await self.uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id(_id)
            if not orcamento:
                raise OrcamentoNaoEncontradoError(
                    f"Orçamento não encontrado para a OS '{ordem_servico_id}'."
                )

            # 4. Validar e recusar orçamento (lança OrcamentoStatusInvalidoError se não COMUNICADO)
            agora = datetime.now(UTC)
            orcamento_recusado = orcamento.recusar(respondido_em=agora, motivo_recusa=motivo_recusa)

            # 5. Encerrar OS
            os_encerrada = OrdemServico(
                id=os.id,
                cliente_id=os.cliente_id,
                veiculo_id=os.veiculo_id,
                status=StatusOrdemServico.ENCERRADA,
                queixa_inicial=os.queixa_inicial,
                diagnostico=os.diagnostico,
                criado_em=os.criado_em,
                atualizado_em=agora,
                iniciado_diagnostico_em=os.iniciado_diagnostico_em,
                diagnostico_concluido_em=os.diagnostico_concluido_em,
            )

            # 6. Processar itens: cancelar e liberar estoque quando necessário
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)
            itens_ativos = [i for i in itens if i.status != StatusItemNaOS.CANCELADO]

            for item in itens_ativos:
                if item.status == StatusItemNaOS.RESERVADO:
                    # Liberar reserva no estoque com lock pessimista
                    item_estoque = await self.uow.item_estoque_repo.obter_por_id_com_lock(
                        ID.from_string(str(item.item_estoque_id))
                    )
                    if item_estoque:
                        item_estoque_atualizado = ItemEstoque(
                            id=item_estoque.id,
                            tipo=item_estoque.tipo,
                            nome=item_estoque.nome,
                            descricao=item_estoque.descricao,
                            codigo=item_estoque.codigo,
                            valor_unitario=item_estoque.valor_unitario,
                            quantidade_disponivel=item_estoque.quantidade_disponivel + item.quantidade,
                            quantidade_reservada=max(0, item_estoque.quantidade_reservada - item.quantidade),
                            quantidade_minima=item_estoque.quantidade_minima,
                            ativo=item_estoque.ativo,
                            criado_em=item_estoque.criado_em,
                            atualizado_em=agora,
                        )
                        await self.uow.item_estoque_repo.atualizar(item_estoque_atualizado)
                        logger.info(
                            f"Estoque liberado: {item.quantidade} un. do item "
                            f"'{item.item_estoque_id}' retornadas ao estoque."
                        )

                # Cancelar item (RESERVADO ou A_RECEBER)
                item_cancelado = OrdemServicoItem(
                    id=item.id,
                    ordem_servico_id=item.ordem_servico_id,
                    item_estoque_id=item.item_estoque_id,
                    nome_item=item.nome_item,
                    tipo_item=item.tipo_item,
                    quantidade=item.quantidade,
                    valor_unitario=item.valor_unitario,
                    status=StatusItemNaOS.CANCELADO,
                )
                await self.uow.ordem_servico_repo.atualizar_item(item_cancelado)

            # 7. Persistir orçamento e OS
            await self.uow.ordem_servico_repo.atualizar_orcamento(orcamento_recusado)
            await self.uow.ordem_servico_repo.atualizar(os_encerrada)

            # Buscar comunicações ainda dentro da transação
            comunicacoes = await self.uow.ordem_servico_repo.listar_comunicacoes_por_ordem_servico_id(_id)

            await self.uow.commit()

            logger.info(
                f"Orçamento da OS '{ordem_servico_id}' recusado. "
                f"OS -> ENCERRADA. Itens ativos cancelados: {len(itens_ativos)}."
            )

        from app.modules.ordens_servico.application.use_cases.obter_orcamento_por_ordem_servico import (
            _to_orcamento_response,
        )
        return _to_orcamento_response(orcamento_recusado, comunicacoes)
