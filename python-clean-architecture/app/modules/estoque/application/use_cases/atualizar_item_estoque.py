from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.estoque.application.dtos.item_estoque import AtualizarItemEstoque, ItemEstoqueResponse
from app.modules.estoque.domain.entities.item_estoque import ItemEstoque
from app.modules.estoque.domain.exceptions import (
    CodigoItemEstoqueJaCadastradoError,
    ItemEstoqueInvalidoError,
    ItemEstoqueNaoEncontradoError,
)
from app.modules.estoque.domain.ports.item_estoque_uow import ItemEstoqueUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtualizarItemEstoqueUseCase:
    uow: ItemEstoqueUnitOfWork

    async def execute(self, item_id: str, dto: AtualizarItemEstoque) -> ItemEstoqueResponse:
        """Atualiza os dados de um item de estoque existente (PATCH — preserva campos não informados).

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ItemEstoqueNaoEncontradoError: Se o item não for encontrado.
            ItemEstoqueInvalidoError: Se os novos dados forem inválidos.
            CodigoItemEstoqueJaCadastradoError: Se o novo código já estiver em uso por outro item.
        """
        id_value = ID.from_string(item_id)

        async with self.uow:
            existente = await self.uow.item_estoque_repo.obter_por_id(id_value)
            if not existente:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque com ID {item_id} não encontrado."
                )

            novo_codigo = dto.codigo if dto.codigo is not None else existente.codigo
            if novo_codigo and novo_codigo != existente.codigo:
                conflito = await self.uow.item_estoque_repo.obter_por_codigo(novo_codigo)
                if conflito:
                    raise CodigoItemEstoqueJaCadastradoError(
                        f"Já existe um item de estoque com o código '{novo_codigo}'."
                    )

            agora = datetime.now(UTC)

            atualizado = await self.uow.item_estoque_repo.atualizar(
                ItemEstoque(
                    id=existente.id,
                    tipo=dto.tipo if dto.tipo is not None else existente.tipo,
                    nome=dto.nome if dto.nome is not None else existente.nome,
                    descricao=dto.descricao if dto.descricao is not None else existente.descricao,
                    codigo=novo_codigo,
                    quantidade_disponivel=dto.quantidade_disponivel if dto.quantidade_disponivel is not None else existente.quantidade_disponivel,
                    quantidade_reservada=existente.quantidade_reservada,
                    quantidade_minima=dto.quantidade_minima if dto.quantidade_minima is not None else existente.quantidade_minima,
                    valor_unitario=Decimal(str(dto.valor_unitario)) if dto.valor_unitario is not None else existente.valor_unitario,
                    ativo=existente.ativo,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ItemEstoqueNaoEncontradoError(
                    f"Item de estoque com ID {item_id} não encontrado."
                )

            logger.info(f"Item de estoque {item_id} atualizado com sucesso")
            return ItemEstoqueResponse(
                id=str(atualizado.id),
                tipo=atualizado.tipo.value,
                nome=atualizado.nome,
                descricao=atualizado.descricao,
                codigo=atualizado.codigo,
                quantidade_disponivel=atualizado.quantidade_disponivel,
                quantidade_reservada=atualizado.quantidade_reservada,
                quantidade_minima=atualizado.quantidade_minima,
                valor_unitario=atualizado.valor_unitario,
                ativo=atualizado.ativo,
            )
