from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.application.dtos.servico import ServicoResponse
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.servicos.domain.ports.servico_uow import ServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtivarServicoUseCase:
    uow: ServicoUnitOfWork

    async def execute(self, servico_id: str) -> ServicoResponse:
        """Ativa um serviço previamente desativado.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ServicoNaoEncontradoError: Se o serviço não for encontrado.
        """
        id_value = ID.from_string(servico_id)

        async with self.uow:
            existente = await self.uow.servico_repo.obter_por_id(id_value)
            if not existente:
                raise ServicoNaoEncontradoError(
                    f"Serviço com ID {servico_id} não encontrado."
                )

            agora = datetime.now(UTC)

            atualizado = await self.uow.servico_repo.atualizar(
                Servico(
                    id=existente.id,
                    nome=existente.nome,
                    descricao=existente.descricao,
                    valor_base=existente.valor_base,
                    tempo_medio_minutos=existente.tempo_medio_minutos,
                    ativo=True,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ServicoNaoEncontradoError(
                    f"Serviço com ID {servico_id} não encontrado."
                )

            logger.info(f"Serviço {servico_id} ativado com sucesso")
            return ServicoResponse(
                id=str(atualizado.id),
                nome=atualizado.nome,
                descricao=atualizado.descricao,
                valor_base=atualizado.valor_base,
                tempo_medio_minutos=atualizado.tempo_medio_minutos,
                ativo=atualizado.ativo,
            )
