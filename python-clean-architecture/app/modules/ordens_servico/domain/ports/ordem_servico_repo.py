"""Contrato do repositório de Ordens de Serviço (porta de saída)."""

from typing import Any, Optional, Protocol
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import OrdemServicoItem
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import OrcamentoComunicacao
from app.modules.ordens_servico.domain.filters.ordem_servico import ListarOrdensServicoFiltro


class OrdemServicoRepo(Protocol):
    """Repositório da agregação Ordem de Serviço."""

    # --- OrdemServico ---

    async def salvar(self, os: OrdemServico) -> None: ...

    async def obter_por_id(self, _id: ID) -> Optional[OrdemServico]: ...

    async def atualizar(self, os: OrdemServico) -> Optional[OrdemServico]: ...

    async def listar(self, filtros: ListarOrdensServicoFiltro) -> list[OrdemServico]: ...

    # --- OrdemServicoServico ---

    async def salvar_servico(self, os_servico: OrdemServicoServico) -> None: ...

    async def obter_servico_por_id(self, _id: ID) -> Optional[OrdemServicoServico]: ...

    async def listar_servicos_da_os(
        self, ordem_servico_id: ID
    ) -> list[OrdemServicoServico]: ...

    async def atualizar_servico(
        self, os_servico: OrdemServicoServico
    ) -> Optional[OrdemServicoServico]: ...

    async def obter_servico_ativo_por_servico_id(
        self, ordem_servico_id: ID, servico_id: ID
    ) -> Optional[OrdemServicoServico]:
        """Retorna o vínculo ativo (cancelado=False) para o par OS+serviço, ou None."""
        ...

    # --- OrdemServicoItem ---

    async def salvar_item(self, os_item: OrdemServicoItem) -> None: ...

    async def obter_item_por_id(self, _id: ID) -> Optional[OrdemServicoItem]: ...

    async def listar_itens_da_os(
        self, ordem_servico_id: ID
    ) -> list[OrdemServicoItem]: ...

    async def atualizar_item(
        self, os_item: OrdemServicoItem
    ) -> Optional[OrdemServicoItem]: ...

    async def obter_item_ativo_por_item_estoque_id(
        self, ordem_servico_id: ID, item_estoque_id: ID
    ) -> Optional[OrdemServicoItem]:
        """Retorna o vínculo ativo (status != CANCELADO) para o par OS+item, ou None."""
        ...

    # --- Orcamento ---

    async def salvar_orcamento(self, orcamento: Orcamento) -> None: ...

    async def obter_orcamento_por_ordem_servico_id(
        self, ordem_servico_id: ID
    ) -> Optional[Orcamento]: ...

    async def atualizar_orcamento(self, orcamento: Orcamento) -> Optional[Orcamento]: ...

    async def orcamento_existe_para_os(self, ordem_servico_id: ID) -> bool: ...

    # --- OrcamentoComunicacao ---

    async def salvar_comunicacao(self, comunicacao: OrcamentoComunicacao) -> None: ...

    async def listar_comunicacoes_por_ordem_servico_id(
        self, ordem_servico_id: ID
    ) -> list[OrcamentoComunicacao]: ...

    async def listar_comunicacoes_por_orcamento_id(
        self, orcamento_id: ID
    ) -> list[OrcamentoComunicacao]: ...

    # --- Métricas ---

    async def obter_estatistica_tempo_execucao_servico(
        self, servico_id: UUID
    ) -> dict[str, Any]:
        """Retorna dict com keys: quantidade, media, menor, maior — filtrando apenas OS
        FINALIZADA/ENTREGUE com serviços ativos e com tempo_executado_minutos preenchido."""
        ...

    async def listar_execucoes_servico(
        self, servico_id: UUID
    ) -> list[dict[str, Any]]:
        """Retorna lista de dicts com keys: ordem_servico_id, ordem_servico_servico_id,
        tempo_executado_minutos, status_os — filtrando apenas OS FINALIZADA/ENTREGUE."""
        ...
