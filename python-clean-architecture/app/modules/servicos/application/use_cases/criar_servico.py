from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.application.dtos.servico import CriarServicoRequest, ServicoResponse
from app.modules.servicos.domain.entities.servico import Servico
from app.modules.servicos.domain.exceptions import NomeServicoJaCadastradoError, ServicoInvalidoError
from app.modules.servicos.domain.ports.servico_uow import ServicoUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class CriarServicoUseCase:
    uow: ServicoUnitOfWork

    async def execute(self, dto: CriarServicoRequest) -> ServicoResponse:
        """Cria um novo serviço no catálogo, garantindo unicidade de nome.

        Raises:
            ServicoInvalidoError: Se os dados fornecidos forem inválidos.
            NomeServicoJaCadastradoError: Se já existir serviço com o mesmo nome.
        """
        async with self.uow:
            if await self.uow.servico_repo.obter_por_nome(dto.nome):
                logger.warning(f"Nome de serviço '{dto.nome}' já cadastrado")
                raise NomeServicoJaCadastradoError(
                    f"Já existe um serviço com o nome '{dto.nome}'."
                )

            agora = datetime.now(UTC)

            servico = Servico(
                id=ID.generate(),
                nome=dto.nome,
                descricao=dto.descricao,
                valor_base=Decimal(str(dto.valor_base)),
                tempo_medio_minutos=dto.tempo_medio_minutos,
                ativo=True,
                criado_em=agora,
                atualizado_em=agora,
            )

            await self.uow.servico_repo.salvar(servico)
            logger.info(f"Serviço '{dto.nome}' criado com sucesso")

            return ServicoResponse(
                id=str(servico.id),
                nome=servico.nome,
                descricao=servico.descricao,
                valor_base=servico.valor_base,
                tempo_medio_minutos=servico.tempo_medio_minutos,
                ativo=servico.ativo,
            )
