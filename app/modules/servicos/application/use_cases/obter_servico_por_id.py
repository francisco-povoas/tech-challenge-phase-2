from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.servicos.application.dtos.servico import ServicoResponse
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.servicos.domain.ports.servico_repo import ServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterServicoPorIdUseCase:
    servico_repo: ServicoRepo

    async def execute(self, servico_id: str) -> ServicoResponse:
        """Retorna os dados de um serviço pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ServicoNaoEncontradoError: Se o serviço não for encontrado.
        """
        id_value = ID.from_string(servico_id)
        servico = await self.servico_repo.obter_por_id(id_value)

        if not servico:
            raise ServicoNaoEncontradoError(f"Serviço com ID {servico_id} não encontrado.")

        logger.info(f"Serviço {servico_id} obtido com sucesso")
        return ServicoResponse(
            id=str(servico.id),
            nome=servico.nome,
            descricao=servico.descricao,
            valor_base=servico.valor_base,
            tempo_medio_minutos=servico.tempo_medio_minutos,
            ativo=servico.ativo,
        )
