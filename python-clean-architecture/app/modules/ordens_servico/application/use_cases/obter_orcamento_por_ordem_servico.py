"""Use case: Obter Orçamento por Ordem de Serviço."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    OrcamentoComunicacaoResponse,
    OrcamentoResponse,
)
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import OrcamentoComunicacao
from app.modules.ordens_servico.domain.exceptions import (
    OrcamentoNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterOrcamentoPorOrdemServicoUseCase:
    ordem_servico_repo: OrdemServicoRepo

    async def execute(self, ordem_servico_id: str) -> OrcamentoResponse:
        _id = ID.from_string(ordem_servico_id)

        os = await self.ordem_servico_repo.obter_por_id(_id)
        if not os:
            raise OrdemServicoNaoEncontradaError(
                f"OS com ID {ordem_servico_id} não encontrada."
            )

        orcamento = await self.ordem_servico_repo.obter_orcamento_por_ordem_servico_id(_id)
        if not orcamento:
            raise OrcamentoNaoEncontradoError(
                f"Orçamento não encontrado para a OS '{ordem_servico_id}'."
            )

        comunicacoes = await self.ordem_servico_repo.listar_comunicacoes_por_ordem_servico_id(_id)

        return _to_orcamento_response(orcamento, comunicacoes)


def _to_orcamento_response(
    orcamento: Orcamento,
    comunicacoes: list[OrcamentoComunicacao],
) -> OrcamentoResponse:
    return OrcamentoResponse(
        id=str(orcamento.id),
        ordem_servico_id=str(orcamento.ordem_servico_id),
        status=orcamento.status.value,
        total_servicos=orcamento.total_servicos,
        total_itens=orcamento.total_itens,
        total_geral=orcamento.total_geral,
        criado_em=orcamento.criado_em,
        atualizado_em=orcamento.atualizado_em,
        comunicado_em=orcamento.comunicado_em,
        observacao=orcamento.observacao,
        comunicacoes=[_to_comunicacao_response(c) for c in comunicacoes],
    )


def _to_comunicacao_response(c: OrcamentoComunicacao) -> OrcamentoComunicacaoResponse:
    return OrcamentoComunicacaoResponse(
        id=str(c.id),
        orcamento_id=str(c.orcamento_id),
        ordem_servico_id=str(c.ordem_servico_id),
        canal=c.canal.value,
        destino=c.destino,
        sucesso=c.sucesso,
        mensagem=c.mensagem,
        provedor=c.provedor,
        referencia_externa=c.referencia_externa,
        enviado_em=c.enviado_em,
        criado_em=c.criado_em,
    )
