from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.clientes.application.dtos.cliente import ClienteResponse
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_uow import ClienteUnitOfWork

logger = setup_logger(__name__)


@dataclass(frozen=True)
class DesativarClienteUseCase:
    uow: ClienteUnitOfWork

    async def execute(self, cliente_id: str) -> ClienteResponse:
        """Desativa um cliente sem removê-lo fisicamente do banco.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ClienteNaoEncontradoError: Se o cliente não for encontrado.
        """
        id_value = ID.from_string(cliente_id)

        async with self.uow:
            existente = await self.uow.cliente_repo.obter_por_id(id_value)
            if not existente:
                raise ClienteNaoEncontradoError(
                    f"Cliente com ID {cliente_id} não encontrado."
                )

            agora = datetime.now(UTC)

            atualizado = await self.uow.cliente_repo.atualizar(
                Cliente(
                    id=existente.id,
                    tipo_pessoa=existente.tipo_pessoa,
                    nome_razao_social=existente.nome_razao_social,
                    cpf_cnpj=existente.cpf_cnpj,
                    telefone=existente.telefone,
                    email=existente.email,
                    cep=existente.cep,
                    logradouro=existente.logradouro,
                    numero=existente.numero,
                    complemento=existente.complemento,
                    bairro=existente.bairro,
                    cidade=existente.cidade,
                    uf=existente.uf,
                    ativo=False,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ClienteNaoEncontradoError(
                    f"Cliente com ID {cliente_id} não encontrado."
                )

            logger.info(f"Cliente {cliente_id} desativado com sucesso")
            return ClienteResponse(
                id=str(atualizado.id),
                tipo_pessoa=atualizado.tipo_pessoa.value,
                nome_razao_social=atualizado.nome_razao_social,
                cpf_cnpj=atualizado.cpf_cnpj.value,
                telefone=atualizado.telefone.value,
                email=atualizado.email.value if atualizado.email else None,
                cep=atualizado.cep,
                logradouro=atualizado.logradouro,
                numero=atualizado.numero,
                complemento=atualizado.complemento,
                bairro=atualizado.bairro,
                cidade=atualizado.cidade,
                uf=atualizado.uf,
                ativo=atualizado.ativo,
            )
