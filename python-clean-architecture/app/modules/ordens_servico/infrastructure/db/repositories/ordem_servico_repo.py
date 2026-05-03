"""Implementação concreta do repositório de Ordens de Serviço (SQLModel + PostgreSQL)."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.id import ID
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import OrdemServicoItem, StatusItemNaOS
from app.modules.ordens_servico.domain.entities.ordem_servico_servico import OrdemServicoServico
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento, StatusOrcamento
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import OrcamentoComunicacao, CanalComunicacaoOrcamento
from app.modules.ordens_servico.domain.filters.ordem_servico import ListarOrdensServicoFiltro
from app.modules.ordens_servico.infrastructure.db.models.ordem_servico_item_model import OrdemServicoItemModel
from app.modules.ordens_servico.infrastructure.db.models.ordem_servico_model import OrdemServicoModel
from app.modules.ordens_servico.infrastructure.db.models.ordem_servico_servico_model import OrdemServicoServicoModel
from app.modules.ordens_servico.infrastructure.db.models.ordem_servico_orcamento_model import OrdemServicoOrcamentoModel
from app.modules.ordens_servico.infrastructure.db.models.ordem_servico_orcamento_comunicacao_model import OrdemServicoOrcamentoComunicacaoModel


class OrdemServicoRepo:
    """Repositório da agregação Ordem de Serviço."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    # -----------------------------------------------------------------------
    # OrdemServico
    # -----------------------------------------------------------------------

    async def salvar(self, os: OrdemServico) -> None:
        model = OrdemServicoModel(
            id=os.id.value,
            cliente_id=os.cliente_id,
            veiculo_id=os.veiculo_id,
            status=os.status.value,
            queixa_inicial=os.queixa_inicial,
            diagnostico=os.diagnostico,
            criado_em=os.criado_em,
            atualizado_em=os.atualizado_em,
            iniciado_diagnostico_em=os.iniciado_diagnostico_em,
            diagnostico_concluido_em=os.diagnostico_concluido_em,
        )
        self.session.add(model)

    async def obter_por_id(self, _id: ID) -> Optional[OrdemServico]:
        model = await self.session.get(OrdemServicoModel, _id.value)
        if not model:
            return None
        return self._os_to_entity(model)

    async def atualizar(self, os: OrdemServico) -> Optional[OrdemServico]:
        model = await self.session.get(OrdemServicoModel, os.id.value)
        if not model:
            return None
        model.status = os.status.value
        model.queixa_inicial = os.queixa_inicial
        model.diagnostico = os.diagnostico
        model.atualizado_em = os.atualizado_em
        model.iniciado_diagnostico_em = os.iniciado_diagnostico_em
        model.diagnostico_concluido_em = os.diagnostico_concluido_em
        self.session.add(model)
        return os

    async def listar(self, filtros: ListarOrdensServicoFiltro) -> list[OrdemServico]:
        query = select(OrdemServicoModel)

        if filtros.status is not None:
            query = query.where(OrdemServicoModel.status == filtros.status.value)
        if filtros.cliente_id:
            query = query.where(OrdemServicoModel.cliente_id == UUID(filtros.cliente_id))
        if filtros.veiculo_id:
            query = query.where(OrdemServicoModel.veiculo_id == UUID(filtros.veiculo_id))
        if filtros.data_inicio:
            query = query.where(OrdemServicoModel.criado_em >= filtros.data_inicio)
        if filtros.data_fim:
            query = query.where(OrdemServicoModel.criado_em <= filtros.data_fim)

        result = await self.session.exec(query)
        return [self._os_to_entity(m) for m in result.all()]

    # -----------------------------------------------------------------------
    # OrdemServicoServico
    # -----------------------------------------------------------------------

    async def salvar_servico(self, os_servico: OrdemServicoServico) -> None:
        model = OrdemServicoServicoModel(
            id=os_servico.id.value,
            ordem_servico_id=os_servico.ordem_servico_id,
            servico_id=os_servico.servico_id,
            nome_servico=os_servico.nome_servico,
            descricao_servico=os_servico.descricao_servico,
            valor_unitario=os_servico.valor_unitario,
            tempo_estimado_minutos=os_servico.tempo_estimado_minutos,
            tempo_executado_minutos=os_servico.tempo_executado_minutos,
            observacao=os_servico.observacao,
            cancelado=os_servico.cancelado,
        )
        self.session.add(model)

    async def obter_servico_por_id(self, _id: ID) -> Optional[OrdemServicoServico]:
        model = await self.session.get(OrdemServicoServicoModel, _id.value)
        if not model:
            return None
        return self._oss_to_entity(model)

    async def listar_servicos_da_os(self, ordem_servico_id: ID) -> list[OrdemServicoServico]:
        result = await self.session.exec(
            select(OrdemServicoServicoModel).where(
                OrdemServicoServicoModel.ordem_servico_id == ordem_servico_id.value
            )
        )
        return [self._oss_to_entity(m) for m in result.all()]

    async def atualizar_servico(
        self, os_servico: OrdemServicoServico
    ) -> Optional[OrdemServicoServico]:
        model = await self.session.get(OrdemServicoServicoModel, os_servico.id.value)
        if not model:
            return None
        model.observacao = os_servico.observacao
        model.cancelado = os_servico.cancelado
        model.tempo_executado_minutos = os_servico.tempo_executado_minutos
        self.session.add(model)
        return os_servico

    async def obter_servico_ativo_por_servico_id(
        self, ordem_servico_id: ID, servico_id: ID
    ) -> Optional[OrdemServicoServico]:
        """Retorna o vínculo ativo (cancelado=False) para o par OS+serviço, ou None."""
        result = await self.session.exec(
            select(OrdemServicoServicoModel).where(
                OrdemServicoServicoModel.ordem_servico_id == ordem_servico_id.value,
                OrdemServicoServicoModel.servico_id == servico_id.value,
                OrdemServicoServicoModel.cancelado == False,  # noqa: E712
            )
        )
        model = result.first()
        return self._oss_to_entity(model) if model else None

    # -----------------------------------------------------------------------
    # OrdemServicoItem
    # -----------------------------------------------------------------------

    async def salvar_item(self, os_item: OrdemServicoItem) -> None:
        model = OrdemServicoItemModel(
            id=os_item.id.value,
            ordem_servico_id=os_item.ordem_servico_id,
            item_estoque_id=os_item.item_estoque_id,
            nome_item=os_item.nome_item,
            tipo_item=os_item.tipo_item,
            quantidade=os_item.quantidade,
            valor_unitario=os_item.valor_unitario,
            status=os_item.status.value,
        )
        self.session.add(model)

    async def obter_item_por_id(self, _id: ID) -> Optional[OrdemServicoItem]:
        model = await self.session.get(OrdemServicoItemModel, _id.value)
        if not model:
            return None
        return self._osi_to_entity(model)

    async def listar_itens_da_os(self, ordem_servico_id: ID) -> list[OrdemServicoItem]:
        result = await self.session.exec(
            select(OrdemServicoItemModel).where(
                OrdemServicoItemModel.ordem_servico_id == ordem_servico_id.value
            )
        )
        return [self._osi_to_entity(m) for m in result.all()]

    async def atualizar_item(self, os_item: OrdemServicoItem) -> Optional[OrdemServicoItem]:
        model = await self.session.get(OrdemServicoItemModel, os_item.id.value)
        if not model:
            return None
        model.status = os_item.status.value
        self.session.add(model)
        return os_item

    async def obter_item_ativo_por_item_estoque_id(
        self, ordem_servico_id: ID, item_estoque_id: ID
    ) -> Optional[OrdemServicoItem]:
        """Retorna o vínculo ativo (status != CANCELADO) para o par OS+item, ou None."""
        result = await self.session.exec(
            select(OrdemServicoItemModel).where(
                OrdemServicoItemModel.ordem_servico_id == ordem_servico_id.value,
                OrdemServicoItemModel.item_estoque_id == item_estoque_id.value,
                OrdemServicoItemModel.status != StatusItemNaOS.CANCELADO.value,
            )
        )
        model = result.first()
        return self._osi_to_entity(model) if model else None

    # -----------------------------------------------------------------------
    # Conversão model → entidade
    # -----------------------------------------------------------------------

    @staticmethod
    def _os_to_entity(model: OrdemServicoModel) -> OrdemServico:
        return OrdemServico(
            id=ID.from_string(str(model.id)),
            cliente_id=model.cliente_id,
            veiculo_id=model.veiculo_id,
            status=StatusOrdemServico(model.status),
            queixa_inicial=model.queixa_inicial,
            diagnostico=model.diagnostico,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            iniciado_diagnostico_em=model.iniciado_diagnostico_em,
            diagnostico_concluido_em=model.diagnostico_concluido_em,
        )

    @staticmethod
    def _oss_to_entity(model: OrdemServicoServicoModel) -> OrdemServicoServico:
        return OrdemServicoServico(
            id=ID.from_string(str(model.id)),
            ordem_servico_id=model.ordem_servico_id,
            servico_id=model.servico_id,
            nome_servico=model.nome_servico,
            descricao_servico=model.descricao_servico,
            valor_unitario=Decimal(str(model.valor_unitario)),
            tempo_estimado_minutos=model.tempo_estimado_minutos,
            tempo_executado_minutos=model.tempo_executado_minutos,
            observacao=model.observacao,
            cancelado=model.cancelado,
        )

    @staticmethod
    def _osi_to_entity(model: OrdemServicoItemModel) -> OrdemServicoItem:
        return OrdemServicoItem(
            id=ID.from_string(str(model.id)),
            ordem_servico_id=model.ordem_servico_id,
            item_estoque_id=model.item_estoque_id,
            nome_item=model.nome_item,
            tipo_item=model.tipo_item,
            quantidade=model.quantidade,
            valor_unitario=Decimal(str(model.valor_unitario)),
            status=StatusItemNaOS(model.status),
        )

    # -----------------------------------------------------------------------
    # Orcamento
    # -----------------------------------------------------------------------

    async def salvar_orcamento(self, orcamento: Orcamento) -> None:
        model = OrdemServicoOrcamentoModel(
            id=orcamento.id.value,
            ordem_servico_id=orcamento.ordem_servico_id,
            status=orcamento.status.value,
            total_servicos=orcamento.total_servicos,
            total_itens=orcamento.total_itens,
            total_geral=orcamento.total_geral,
            criado_em=orcamento.criado_em,
            atualizado_em=orcamento.atualizado_em,
            comunicado_em=orcamento.comunicado_em,
            observacao=orcamento.observacao,
            respondido_em=orcamento.respondido_em,
            motivo_recusa=orcamento.motivo_recusa,
        )
        self.session.add(model)
        # Flush imediato para garantir que a linha exista no banco antes de
        # qualquer inserção nas tabelas filhas (comunicações) que referenciam
        # esta linha via FK.
        await self.session.flush()

    async def obter_orcamento_por_ordem_servico_id(self, ordem_servico_id: ID) -> Optional[Orcamento]:
        result = await self.session.exec(
            select(OrdemServicoOrcamentoModel).where(
                OrdemServicoOrcamentoModel.ordem_servico_id == ordem_servico_id.value
            )
        )
        model = result.first()
        return self._orc_to_entity(model) if model else None

    async def atualizar_orcamento(self, orcamento: Orcamento) -> Optional[Orcamento]:
        model = await self.session.get(OrdemServicoOrcamentoModel, orcamento.id.value)
        if not model:
            return None
        model.status = orcamento.status.value
        model.atualizado_em = orcamento.atualizado_em
        model.comunicado_em = orcamento.comunicado_em
        model.respondido_em = orcamento.respondido_em
        model.motivo_recusa = orcamento.motivo_recusa
        self.session.add(model)
        return orcamento

    async def orcamento_existe_para_os(self, ordem_servico_id: ID) -> bool:
        result = await self.session.exec(
            select(OrdemServicoOrcamentoModel).where(
                OrdemServicoOrcamentoModel.ordem_servico_id == ordem_servico_id.value
            )
        )
        return result.first() is not None

    # -----------------------------------------------------------------------
    # OrcamentoComunicacao
    # -----------------------------------------------------------------------

    async def salvar_comunicacao(self, comunicacao: OrcamentoComunicacao) -> None:
        model = OrdemServicoOrcamentoComunicacaoModel(
            id=comunicacao.id.value,
            orcamento_id=comunicacao.orcamento_id,
            ordem_servico_id=comunicacao.ordem_servico_id,
            canal=comunicacao.canal.value,
            destino=comunicacao.destino,
            sucesso=comunicacao.sucesso,
            mensagem=comunicacao.mensagem,
            provedor=comunicacao.provedor,
            referencia_externa=comunicacao.referencia_externa,
            enviado_em=comunicacao.enviado_em,
            criado_em=comunicacao.criado_em,
        )
        self.session.add(model)

    async def listar_comunicacoes_por_ordem_servico_id(
        self, ordem_servico_id: ID
    ) -> list[OrcamentoComunicacao]:
        result = await self.session.exec(
            select(OrdemServicoOrcamentoComunicacaoModel).where(
                OrdemServicoOrcamentoComunicacaoModel.ordem_servico_id == ordem_servico_id.value
            )
        )
        return [self._com_to_entity(m) for m in result.all()]

    async def listar_comunicacoes_por_orcamento_id(
        self, orcamento_id: ID
    ) -> list[OrcamentoComunicacao]:
        result = await self.session.exec(
            select(OrdemServicoOrcamentoComunicacaoModel).where(
                OrdemServicoOrcamentoComunicacaoModel.orcamento_id == orcamento_id.value
            )
        )
        return [self._com_to_entity(m) for m in result.all()]

    # -----------------------------------------------------------------------
    # Conversão model → entidade (orcamento)
    # -----------------------------------------------------------------------

    @staticmethod
    def _orc_to_entity(model: OrdemServicoOrcamentoModel) -> Orcamento:
        return Orcamento(
            id=ID.from_string(str(model.id)),
            ordem_servico_id=model.ordem_servico_id,
            status=StatusOrcamento(model.status),
            total_servicos=Decimal(str(model.total_servicos)),
            total_itens=Decimal(str(model.total_itens)),
            total_geral=Decimal(str(model.total_geral)),
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            comunicado_em=model.comunicado_em,
            observacao=model.observacao,
            respondido_em=model.respondido_em,
            motivo_recusa=model.motivo_recusa,
        )

    @staticmethod
    def _com_to_entity(model: OrdemServicoOrcamentoComunicacaoModel) -> OrcamentoComunicacao:
        return OrcamentoComunicacao(
            id=ID.from_string(str(model.id)),
            orcamento_id=model.orcamento_id,
            ordem_servico_id=model.ordem_servico_id,
            canal=CanalComunicacaoOrcamento(model.canal),
            destino=model.destino,
            sucesso=model.sucesso,
            mensagem=model.mensagem,
            provedor=model.provedor,
            referencia_externa=model.referencia_externa,
            enviado_em=model.enviado_em,
            criado_em=model.criado_em,
        )
