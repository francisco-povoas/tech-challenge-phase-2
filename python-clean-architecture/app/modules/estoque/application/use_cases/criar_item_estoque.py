from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.application.dtos.item_estoque import CriarItemEstoqueRequest, ItemEstoqueResponse
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.exceptions import CodigoItemEstoqueJaCadastradoError, ItemEstoqueInvalidoError
from app.modules.estoque.domain.ports.item_estoque_uow import ItemEstoqueUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class CriarItemEstoqueUseCase:
    uow: ItemEstoqueUnitOfWork

    async def execute(self, dto: CriarItemEstoqueRequest) -> ItemEstoqueResponse:
        """Cria um novo item de estoque.

        Raises:
            ItemEstoqueInvalidoError: Se os dados fornecidos forem inválidos.
            CodigoItemEstoqueJaCadastradoError: Se já existir item com o mesmo código.
        """
        async with self.uow:
            if dto.codigo:
                existente = await self.uow.item_estoque_repo.obter_por_codigo(dto.codigo)
                if existente:
                    logger.warning(f"Código de item '{dto.codigo}' já cadastrado")
                    raise CodigoItemEstoqueJaCadastradoError(
                        f"Já existe um item de estoque com o código '{dto.codigo}'."
                    )

            agora = datetime.now(UTC)

            item = ItemEstoque(
                id=ID.generate(),
                tipo=dto.tipo,
                nome=dto.nome,
                descricao=dto.descricao,
                codigo=dto.codigo,
                quantidade_disponivel=dto.quantidade_disponivel,
                quantidade_reservada=0,
                quantidade_minima=dto.quantidade_minima,
                valor_unitario=Decimal(str(dto.valor_unitario)),
                ativo=True,
                criado_em=agora,
                atualizado_em=agora,
            )

            await self.uow.item_estoque_repo.salvar(item)
            logger.info(f"Item de estoque '{dto.nome}' criado com sucesso")

            return ItemEstoqueResponse(
                id=str(item.id),
                tipo=item.tipo.value,
                nome=item.nome,
                descricao=item.descricao,
                codigo=item.codigo,
                quantidade_disponivel=item.quantidade_disponivel,
                quantidade_reservada=item.quantidade_reservada,
                quantidade_minima=item.quantidade_minima,
                valor_unitario=item.valor_unitario,
                ativo=item.ativo,
            )
