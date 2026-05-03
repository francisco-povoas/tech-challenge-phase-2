"""Use case: Aprovar Orçamento de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import OrcamentoResponse
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import StatusItemNaOS
from app.modules.ordens_servico.domain.exceptions import (
    OrcamentoNaoEncontradoError,
    OrcamentoStatusInvalidoError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AprovarOrcamentoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(self, ordem_servico_id: str) -> OrcamentoResponse:
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
                    f"Só é possível aprovar orçamento de OS com status "
                    f"'AGUARDANDO_APROVACAO'. Status atual: '{os.status.value}'."
                )

            # 3. Buscar orçamento
            orcamento = await self.uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id(_id)
            if not orcamento:
                raise OrcamentoNaoEncontradoError(
                    f"Orçamento não encontrado para a OS '{ordem_servico_id}'."
                )

            # 4. Validar status do orçamento (lança OrcamentoStatusInvalidoError se não COMUNICADO)
            agora = datetime.now(UTC)
            orcamento_aprovado = orcamento.aprovar(respondido_em=agora)

            # 5. Verificar itens ativos para determinar novo status da OS
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)
            itens_ativos = [i for i in itens if i.status != StatusItemNaOS.CANCELADO]

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

            # 6. Persistir
            await self.uow.ordem_servico_repo.atualizar_orcamento(orcamento_aprovado)
            await self.uow.ordem_servico_repo.atualizar(os_atualizada)

            # Buscar comunicações ainda dentro da transação
            comunicacoes = await self.uow.ordem_servico_repo.listar_comunicacoes_por_ordem_servico_id(_id)

            await self.uow.commit()

            logger.info(
                f"Orçamento da OS '{ordem_servico_id}' aprovado. "
                f"OS -> {novo_status_os.value}"
            )

        from app.modules.ordens_servico.application.use_cases.obter_orcamento_por_ordem_servico import (
            _to_orcamento_response,
        )
        return _to_orcamento_response(orcamento_aprovado, comunicacoes)
