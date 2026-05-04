"""Use case: Registrar Pagamento de uma Ordem de Serviço."""

from dataclasses import dataclass
from decimal import Decimal

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    OrdemServicoDetalheResponse,
    RegistrarPagamentoOrdemServicoRequest,
)
from app.modules.ordens_servico.application.use_cases.obter_ordem_servico_por_id import _to_detalhe
from app.modules.ordens_servico.domain.entities.orcamento import StatusOrcamento
from app.modules.ordens_servico.domain.enums import FormaPagamento
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoPagamentoJaRegistradoError,
    OrdemServicoTransicaoInvalidaError,
    ValorPagamentoInvalidoError,
    ValorPagamentoMenorQueOrcamentoError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class RegistrarPagamentoOrdemServicoUseCase:
    uow: OrdemServicoUnitOfWork

    async def execute(
        self,
        ordem_servico_id: str,
        dto: RegistrarPagamentoOrdemServicoRequest,
    ) -> OrdemServicoDetalheResponse:
        _id = ID.from_string(ordem_servico_id)

        # Validar forma_pagamento antes de iniciar a transação
        try:
            FormaPagamento(dto.forma_pagamento)
        except ValueError:
            from app.modules.ordens_servico.domain.exceptions import ValorPagamentoInvalidoError
            raise ValorPagamentoInvalidoError(
                f"Forma de pagamento inválida: '{dto.forma_pagamento}'. "
                f"Valores aceitos: {[fp.value for fp in FormaPagamento]}."
            )

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Buscar orçamento para validar valor_pago contra total_geral
            orcamento = await self.uow.ordem_servico_repo.obter_orcamento_por_ordem_servico_id(_id)
            total_orcamento: Decimal | None = None
            if orcamento and orcamento.status == StatusOrcamento.APROVADO:
                total_orcamento = orcamento.total_geral

            # 3. Registrar pagamento via domínio (valida status, duplicidade, valor e orcamento)
            os_paga = os.registrar_pagamento(
                forma_pagamento=dto.forma_pagamento,
                valor_pago=dto.valor_pago,
                observacao=dto.observacao,
                total_orcamento=total_orcamento,
            )

            # 4. Persistir OS
            await self.uow.ordem_servico_repo.atualizar(os_paga)

            # 5. Commit
            await self.uow.commit()

            # 6. Buscar dados para resposta
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_id)
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)

            logger.info(
                f"Pagamento registrado para OS '{ordem_servico_id}' — "
                f"forma: {dto.forma_pagamento}, valor: {dto.valor_pago}."
            )
            return _to_detalhe(os_paga, servicos, itens)
