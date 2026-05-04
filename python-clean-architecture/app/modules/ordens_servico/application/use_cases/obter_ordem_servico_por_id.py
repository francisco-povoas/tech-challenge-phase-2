"""Use case: Obter Ordem de Serviço por ID (detalhamento)."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    OrdemServicoDetalheResponse,
    OrdemServicoItemResponse,
    OrdemServicoServicoResponse,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import OrdemServicoItem
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.exceptions import OrdemServicoNaoEncontradaError
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterOrdemServicoPorIdUseCase:
    ordem_servico_repo: OrdemServicoRepo

    async def execute(self, ordem_servico_id: str) -> OrdemServicoDetalheResponse:
        _id = ID.from_string(ordem_servico_id)
        os = await self.ordem_servico_repo.obter_por_id(_id)
        if not os:
            raise OrdemServicoNaoEncontradaError(
                f"OS com ID {ordem_servico_id} não encontrada."
            )

        servicos = await self.ordem_servico_repo.listar_servicos_da_os(_id)
        itens = await self.ordem_servico_repo.listar_itens_da_os(_id)

        logger.debug(f"OS '{ordem_servico_id}' detalhada com sucesso")
        return _to_detalhe(os, servicos, itens)


def _to_detalhe(
    os: OrdemServico,
    servicos: list[OrdemServicoServico],
    itens: list[OrdemServicoItem],
) -> OrdemServicoDetalheResponse:
    return OrdemServicoDetalheResponse(
        id=str(os.id),
        cliente_id=str(os.cliente_id),
        veiculo_id=str(os.veiculo_id),
        status=os.status.value,
        queixa_inicial=os.queixa_inicial,
        diagnostico=os.diagnostico,
        criado_em=os.criado_em,
        atualizado_em=os.atualizado_em,
        iniciado_diagnostico_em=os.iniciado_diagnostico_em,
        diagnostico_concluido_em=os.diagnostico_concluido_em,
        pagamento_registrado_em=os.pagamento_registrado_em,
        forma_pagamento=os.forma_pagamento,
        valor_pago=os.valor_pago,
        pagamento_observacao=os.pagamento_observacao,
        servicos=[_servico_to_response(s) for s in servicos],
        itens=[_item_to_response(i) for i in itens],
    )


def _servico_to_response(s: OrdemServicoServico) -> OrdemServicoServicoResponse:
    return OrdemServicoServicoResponse(
        id=str(s.id),
        servico_id=str(s.servico_id),
        nome_servico=s.nome_servico,
        descricao_servico=s.descricao_servico,
        valor_unitario=s.valor_unitario,
        tempo_estimado_minutos=s.tempo_estimado_minutos,
        tempo_executado_minutos=s.tempo_executado_minutos,
        observacao=s.observacao,
        cancelado=s.cancelado,
    )


def _item_to_response(i: OrdemServicoItem) -> OrdemServicoItemResponse:
    return OrdemServicoItemResponse(
        id=str(i.id),
        item_estoque_id=str(i.item_estoque_id),
        nome_item=i.nome_item,
        tipo_item=i.tipo_item,
        quantidade=i.quantidade,
        valor_unitario=i.valor_unitario,
        status=i.status.value,
    )
