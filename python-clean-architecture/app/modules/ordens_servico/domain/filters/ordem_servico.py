"""Filtros de listagem para Ordens de Serviço."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.modules.ordens_servico.domain.entities.ordem_servico import StatusOrdemServico


@dataclass(frozen=True)
class ListarOrdensServicoFiltro:
    status: Optional[StatusOrdemServico] = None
    cliente_id: Optional[str] = None
    veiculo_id: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
