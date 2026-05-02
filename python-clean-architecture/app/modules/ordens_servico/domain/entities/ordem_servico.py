"""Entidade de domínio: Ordem de Serviço."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.exceptions import (
    OrdemServicoInvalidaError,
    OrdemServicoTransicaoInvalidaError,
)


class StatusOrdemServico(str, Enum):
    """Status possíveis de uma Ordem de Serviço."""

    # Etapa 1 — implementada
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    DIAGNOSTICO_CONCLUIDO = "DIAGNOSTICO_CONCLUIDO"

    # Etapas futuras — declaradas para preparar o modelo
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    AGUARDANDO_ITENS = "AGUARDANDO_ITENS"
    APROVADA = "APROVADA"
    EM_EXECUCAO = "EM_EXECUCAO"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    ENCERRADA = "ENCERRADA"


# Transições válidas entre status
_TRANSICOES_VALIDAS: dict[StatusOrdemServico, set[StatusOrdemServico]] = {
    StatusOrdemServico.RECEBIDA: {
        StatusOrdemServico.EM_DIAGNOSTICO,
    },
    StatusOrdemServico.EM_DIAGNOSTICO: {
        StatusOrdemServico.DIAGNOSTICO_CONCLUIDO,
    },
    StatusOrdemServico.DIAGNOSTICO_CONCLUIDO: {
        StatusOrdemServico.AGUARDANDO_APROVACAO,
    },
    StatusOrdemServico.AGUARDANDO_APROVACAO: {
        StatusOrdemServico.APROVADA,
        StatusOrdemServico.AGUARDANDO_ITENS,
        StatusOrdemServico.ENCERRADA,
    },
    StatusOrdemServico.AGUARDANDO_ITENS: {
        StatusOrdemServico.APROVADA,
    },
    StatusOrdemServico.APROVADA: {
        StatusOrdemServico.EM_EXECUCAO,
    },
    StatusOrdemServico.EM_EXECUCAO: {
        StatusOrdemServico.FINALIZADA,
    },
    StatusOrdemServico.FINALIZADA: {
        StatusOrdemServico.ENTREGUE,
    },
    StatusOrdemServico.ENTREGUE: set(),   # estado terminal — conclusão bem-sucedida
    StatusOrdemServico.ENCERRADA: set(),  # estado terminal — orçamento negado/cancelamento
}


@dataclass(frozen=True, kw_only=True)
class OrdemServico:
    """Entidade de domínio representando uma Ordem de Serviço."""

    id: ID
    cliente_id: UUID
    veiculo_id: UUID
    status: StatusOrdemServico
    queixa_inicial: str
    diagnostico: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    iniciado_diagnostico_em: Optional[datetime]
    diagnostico_concluido_em: Optional[datetime]

    def __post_init__(self) -> None:
        if not self.queixa_inicial or not self.queixa_inicial.strip():
            raise OrdemServicoInvalidaError("A queixa inicial não pode ser vazia.")

    def pode_transitar_para(self, novo_status: StatusOrdemServico) -> bool:
        """Verifica se a transição de status é válida."""
        return novo_status in _TRANSICOES_VALIDAS.get(self.status, set())

    def validar_transicao(self, novo_status: StatusOrdemServico) -> None:
        """Lança exceção se a transição de status não for permitida."""
        if not self.pode_transitar_para(novo_status):
            raise OrdemServicoTransicaoInvalidaError(
                f"Não é possível alterar o status de '{self.status.value}' "
                f"para '{novo_status.value}'."
            )
