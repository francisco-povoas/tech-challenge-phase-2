"""Use case: Gerar Orçamento de uma Ordem de Serviço."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.shared.infra.notifications.notifier import WhatsAppNotifier, EmailNotifier
from app.modules.clientes.infrastructure.db.repositories.cliente_repo import ClienteRepo
from app.modules.ordens_servico.application.dtos.ordem_servico import (
    GerarOrcamentoRequest,
    OrcamentoComunicacaoResponse,
    OrcamentoResponse,
)
from app.modules.ordens_servico.domain.entities.ordem_servico import OrdemServico, StatusOrdemServico
from app.modules.ordens_servico.domain.entities.ordem_servico_item import StatusItemNaOS
from app.modules.ordens_servico.domain.entities.orcamento import Orcamento, StatusOrcamento
from app.modules.ordens_servico.domain.entities.orcamento_comunicacao import (
    CanalComunicacaoOrcamento,
    OrcamentoComunicacao,
)
from app.modules.ordens_servico.domain.exceptions import (
    ClienteSemContatoParaOrcamentoError,
    OrcamentoJaExisteParaOrdemServicoError,
    OrdemServicoInvalidaError,
    OrdemServicoNaoEncontradaError,
    OrdemServicoTransicaoInvalidaError,
)
from app.modules.ordens_servico.domain.ports.ordem_servico_uow import OrdemServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class GerarOrcamentoUseCase:
    uow: OrdemServicoUnitOfWork
    cliente_repo: ClienteRepo
    whatsapp_notifier: WhatsAppNotifier
    email_notifier: EmailNotifier

    async def execute(
        self,
        ordem_servico_id: str,
        dto: Optional[GerarOrcamentoRequest] = None,
    ) -> OrcamentoResponse:
        _id = ID.from_string(ordem_servico_id)

        async with self.uow:
            # 1. Buscar OS
            os = await self.uow.ordem_servico_repo.obter_por_id(_id)
            if not os:
                raise OrdemServicoNaoEncontradaError(
                    f"OS com ID {ordem_servico_id} não encontrada."
                )

            # 2. Verificar se orçamento já existe (antes de validar status,
            #    pois após a primeira geração a OS muda para AGUARDANDO_APROVACAO
            #    e a duplicidade deve ter prioridade sobre o erro de status)
            if await self.uow.ordem_servico_repo.orcamento_existe_para_os(_id):
                raise OrcamentoJaExisteParaOrdemServicoError(
                    "Já existe orçamento gerado para esta ordem de serviço."
                )

            # 3. Validar status da OS
            if os.status != StatusOrdemServico.DIAGNOSTICO_CONCLUIDO:
                raise OrdemServicoTransicaoInvalidaError(
                    f"Só é possível gerar orçamento para OS com status "
                    f"'DIAGNOSTICO_CONCLUIDO'. Status atual: '{os.status.value}'."
                )

            # 4. Buscar cliente e dados de contato
            cliente = await self.cliente_repo.obter_por_id(ID.from_string(str(os.cliente_id)))
            if not cliente:
                raise OrdemServicoInvalidaError(
                    f"Cliente com ID {os.cliente_id} não encontrado."
                )

            email_cliente = cliente.email.value if cliente.email else None
            telefone_cliente = cliente.telefone.value if cliente.telefone else None

            if not email_cliente or not telefone_cliente:
                raise ClienteSemContatoParaOrcamentoError(
                    "Cliente não possui e-mail e telefone para envio do orçamento."
                )

            # 5. Calcular totais
            servicos = await self.uow.ordem_servico_repo.listar_servicos_da_os(_id)
            servicos_ativos = [s for s in servicos if not s.cancelado]
            if not servicos_ativos:
                raise OrdemServicoInvalidaError(
                    "A OS não possui serviços ativos para gerar orçamento."
                )

            itens = await self.uow.ordem_servico_repo.listar_itens_da_os(_id)
            itens_ativos = [
                i for i in itens if i.status != StatusItemNaOS.CANCELADO
            ]

            total_servicos = sum(
                (s.valor_unitario for s in servicos_ativos), Decimal("0.00")
            )
            total_itens = sum(
                (i.valor_unitario * i.quantidade for i in itens_ativos), Decimal("0.00")
            )
            total_geral = total_servicos + total_itens

            # 6. Reservar ID do orçamento e disparar notificações mockadas
            # (antes de persistir, para não abrir a transação para I/O externo)
            orcamento_id = ID.generate()
            agora = datetime.now(UTC)

            # 7. Enviar WhatsApp mockado
            resultado_whatsapp = await self.whatsapp_notifier.enviar_orcamento(
                ordem_servico_id=os.id.value,
                orcamento_id=orcamento_id.value,
                destino=telefone_cliente,
                total_geral=str(total_geral),
            )

            # 8. Enviar e-mail mockado
            resultado_email = await self.email_notifier.enviar_orcamento(
                ordem_servico_id=os.id.value,
                orcamento_id=orcamento_id.value,
                destino=email_cliente,
                total_geral=str(total_geral),
            )

            # 9. Determinar status final do orçamento com base nos resultados
            ambos_sucesso = resultado_whatsapp.sucesso and resultado_email.sucesso
            comunicado_em = datetime.now(UTC) if ambos_sucesso else None
            status_orcamento = StatusOrcamento.COMUNICADO if ambos_sucesso else StatusOrcamento.GERADO

            # 10. Criar orçamento já com status final (evita session.get posterior
            #     que dispararia autoflush prematuro sobre comunicações pendentes)
            orcamento = Orcamento(
                id=orcamento_id,
                ordem_servico_id=os.id.value,
                status=status_orcamento,
                total_servicos=total_servicos,
                total_itens=total_itens,
                total_geral=total_geral,
                criado_em=agora,
                atualizado_em=comunicado_em or agora,
                comunicado_em=comunicado_em,
                observacao=dto.observacao if dto else None,
            )
            # salvar_orcamento já faz flush() internamente para garantir que a
            # linha exista no banco antes de inserir as comunicações (FK).
            await self.uow.ordem_servico_repo.salvar_orcamento(orcamento)

            # 11. Registrar comunicações
            comunicacao_whatsapp = OrcamentoComunicacao(
                id=ID.generate(),
                orcamento_id=orcamento.id.value,
                ordem_servico_id=os.id.value,
                canal=CanalComunicacaoOrcamento.WHATSAPP,
                destino=telefone_cliente,
                sucesso=resultado_whatsapp.sucesso,
                mensagem=resultado_whatsapp.mensagem,
                provedor=resultado_whatsapp.provedor,
                referencia_externa=resultado_whatsapp.referencia_externa,
                enviado_em=resultado_whatsapp.enviado_em,
                criado_em=agora,
            )
            comunicacao_email = OrcamentoComunicacao(
                id=ID.generate(),
                orcamento_id=orcamento.id.value,
                ordem_servico_id=os.id.value,
                canal=CanalComunicacaoOrcamento.EMAIL,
                destino=email_cliente,
                sucesso=resultado_email.sucesso,
                mensagem=resultado_email.mensagem,
                provedor=resultado_email.provedor,
                referencia_externa=resultado_email.referencia_externa,
                enviado_em=resultado_email.enviado_em,
                criado_em=agora,
            )
            await self.uow.ordem_servico_repo.salvar_comunicacao(comunicacao_whatsapp)
            await self.uow.ordem_servico_repo.salvar_comunicacao(comunicacao_email)

            # 12. Se ambos os envios tiveram sucesso: atualizar OS
            comunicacoes = [comunicacao_whatsapp, comunicacao_email]
            if ambos_sucesso:
                os_atualizada = OrdemServico(
                    id=os.id,
                    cliente_id=os.cliente_id,
                    veiculo_id=os.veiculo_id,
                    status=StatusOrdemServico.AGUARDANDO_APROVACAO,
                    queixa_inicial=os.queixa_inicial,
                    diagnostico=os.diagnostico,
                    criado_em=os.criado_em,
                    atualizado_em=comunicado_em,
                    iniciado_diagnostico_em=os.iniciado_diagnostico_em,
                    diagnostico_concluido_em=os.diagnostico_concluido_em,
                )
                await self.uow.ordem_servico_repo.atualizar(os_atualizada)

            logger.info(
                f"Orçamento '{orcamento.id}' gerado para OS '{ordem_servico_id}' "
                f"com status '{orcamento.status.value}'."
            )

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
