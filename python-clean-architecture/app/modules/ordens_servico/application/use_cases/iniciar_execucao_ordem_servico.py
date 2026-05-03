"""Use case: Iniciar Execução de uma Ordem de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import OrdemServicoDetalheResponse
from app.modules.ordens_servico.application.use_cases.obter_ordem_servico_por_id import _to_detalhe
from app.modules.ordens_servico.domain.entities.ordem_servico_item import StatusItemNaOS
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoNaoEncontradaError,
    OrdemServicoPossuiItemAReceberError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class IniciarExecucaoOrdemServicoUseCase:
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

            # 2. Buscar itens da OS
            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)
            itens_ativos = [i for i in itens if i.status != StatusItemNaOS.CANCELADO]
            status_ativos = [i.status.value for i in itens_ativos]

            # 3. Transitar OS: APROVADA -> EM_EXECUCAO (valida status e item A_RECEBER)
            os_em_execucao = os.iniciar_execucao(itens_ativos_status=status_ativos)

            # 4. Transitar itens RESERVADO -> EM_USO
            itens_atualizados = []
            for item in itens_ativos:
                if item.status == StatusItemNaOS.RESERVADO:
                    itens_atualizados.append(item.colocar_em_uso())

            # 5. Persistir itens atualizados
            for item in itens_atualizados:
                await self.uow.ordem_servico_repo.atualizar_item(item)

            # 6. Persistir OS atualizada
            await self.uow.ordem_servico_repo.atualizar(os_em_execucao)

            # 7. Commit
            await self.uow.commit()

            # 8. Buscar serviços para montar resposta
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_id)
            itens_finais = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)

            logger.info(f"Execução da OS '{ordem_servico_id}' iniciada com sucesso.")
            return _to_detalhe(os_em_execucao, servicos, itens_finais)
