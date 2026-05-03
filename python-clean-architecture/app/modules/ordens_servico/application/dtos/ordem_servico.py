"""DTOs (request/response) do módulo Ordens de Serviço."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


# ---------------------------------------------------------------------------
# Request DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class CriarOrdemServicoRequest:
    cliente_id: str
    veiculo_id: str
    queixa_inicial: str


@dataclass(frozen=True, kw_only=True)
class RegistrarDiagnosticoRequest:
    diagnostico: str


@dataclass(frozen=True, kw_only=True)
class AdicionarServicoNaOSRequest:
    servico_id: str
    observacao: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class AdicionarItemNaOSRequest:
    item_estoque_id: str
    quantidade: int


@dataclass(frozen=True, kw_only=True)
class GerarOrcamentoRequest:
    """Body opcional para geração do orçamento."""
    observacao: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class RecusarOrcamentoRequest:
    """Body opcional para recusa do orçamento."""
    motivo_recusa: Optional[str] = None


# ---------------------------------------------------------------------------
# Response DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class OrdemServicoServicoResponse:
    id: str
    servico_id: str
    nome_servico: str
    descricao_servico: Optional[str]
    valor_unitario: Decimal
    tempo_estimado_minutos: int
    tempo_executado_minutos: Optional[int]
    observacao: Optional[str]
    cancelado: bool


@dataclass(frozen=True, kw_only=True)
class OrdemServicoItemResponse:
    id: str
    item_estoque_id: str
    nome_item: str
    tipo_item: str
    quantidade: int
    valor_unitario: Decimal
    status: str


@dataclass(frozen=True, kw_only=True)
class OrdemServicoResumoResponse:
    """Resposta resumida — usada na listagem."""

    id: str
    cliente_id: str
    veiculo_id: str
    status: str
    queixa_inicial: str
    diagnostico: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    iniciado_diagnostico_em: Optional[datetime]
    diagnostico_concluido_em: Optional[datetime]


@dataclass(frozen=True, kw_only=True)
class OrdemServicoDetalheResponse:
    """Resposta completa — usada no detalhamento."""

    id: str
    cliente_id: str
    veiculo_id: str
    status: str
    queixa_inicial: str
    diagnostico: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    iniciado_diagnostico_em: Optional[datetime]
    diagnostico_concluido_em: Optional[datetime]
    servicos: list[OrdemServicoServicoResponse] = field(default_factory=list)
    itens: list[OrdemServicoItemResponse] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class OrcamentoComunicacaoResponse:
    """Resposta de uma comunicação de orçamento."""

    id: str
    orcamento_id: str
    ordem_servico_id: str
    canal: str
    destino: str
    sucesso: bool
    mensagem: str
    provedor: str
    referencia_externa: Optional[str]
    enviado_em: datetime
    criado_em: datetime


@dataclass(frozen=True, kw_only=True)
class OrcamentoResponse:
    """Resposta completa do orçamento de uma OS."""

    id: str
    ordem_servico_id: str
    status: str
    total_servicos: Decimal
    total_itens: Decimal
    total_geral: Decimal
    criado_em: datetime
    atualizado_em: datetime
    comunicado_em: Optional[datetime]
    observacao: Optional[str]
    respondido_em: Optional[datetime] = None
    motivo_recusa: Optional[str] = None
    comunicacoes: list[OrcamentoComunicacaoResponse] = field(default_factory=list)
