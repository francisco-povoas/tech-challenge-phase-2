from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.application.dtos.servico import AtualizarServico, ServicoResponse
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import ServicoInvalidoError, ServicoNaoEncontradoError
from app.modules.servicos.domain.ports.servico_uow import ServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtualizarServicoUseCase:
    uow: ServicoUnitOfWork

    async def execute(self, servico_id: str, dto: AtualizarServico) -> ServicoResponse:
        """Atualiza os dados de um serviço existente (PATCH — preserva campos não informados).

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ServicoNaoEncontradoError: Se o serviço não for encontrado.
            ServicoInvalidoError: Se os novos dados forem inválidos.
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
                    nome=dto.nome if dto.nome is not None else existente.nome,
                    descricao=dto.descricao if dto.descricao is not None else existente.descricao,
                    valor_base=Decimal(str(dto.valor_base)) if dto.valor_base is not None else existente.valor_base,
                    tempo_medio_minutos=dto.tempo_medio_minutos if dto.tempo_medio_minutos is not None else existente.tempo_medio_minutos,
                    ativo=existente.ativo,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ServicoNaoEncontradoError(
                    f"Serviço com ID {servico_id} não encontrado."
                )

            logger.info(f"Serviço {servico_id} atualizado com sucesso")
            return ServicoResponse(
                id=str(atualizado.id),
                nome=atualizado.nome,
                descricao=atualizado.descricao,
                valor_base=atualizado.valor_base,
                tempo_medio_minutos=atualizado.tempo_medio_minutos,
                ativo=atualizado.ativo,
            )
