from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.servicos.application.dtos.servico import ServicoResponse
from app.modules.servicos.domain.exceptions import ServicoNaoEncontradoError
from app.modules.servicos.domain.ports.servico_repo import ServicoRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterServicoPorNomeUseCase:
    servico_repo: ServicoRepo

    async def execute(self, nome: str) -> ServicoResponse:
        """Retorna os dados de um serviço pelo nome exato.

        Raises:
            ServicoNaoEncontradoError: Se o serviço não for encontrado.
        """
        servico = await self.servico_repo.obter_por_nome(nome)

        if not servico:
            raise ServicoNaoEncontradoError(f"Serviço com nome '{nome}' não encontrado.")

        logger.info(f"Serviço com nome '{nome}' obtido com sucesso")
        return ServicoResponse(
            id=str(servico.id),
            nome=servico.nome,
            descricao=servico.descricao,
            valor_base=servico.valor_base,
            tempo_medio_minutos=servico.tempo_medio_minutos,
            ativo=servico.ativo,
        )
