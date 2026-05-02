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
