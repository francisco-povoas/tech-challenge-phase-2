"""Use case: Listar Comunicações do Orçamento de uma OS."""

from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.application.dtos.ordem_servico import OrcamentoComunicacaoResponse
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import OrcamentoComunicacao
from app.modules.ordens_servico.domain.exceptions import (
    OrcamentoNaoEncontradoError,
    OrdemServicoNaoEncontradaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_repo import OrdemServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarComunicacoesOrcamentoUseCase:
    ordem_servico_repo: OrdemServicoRepo

    async def execute(self, ordem_servico_id: str) -> list[OrcamentoComunicacaoResponse]:
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
        return [_to_response(c) for c in comunicacoes]


def _to_response(c: OrcamentoComunicacao) -> OrcamentoComunicacaoResponse:
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
