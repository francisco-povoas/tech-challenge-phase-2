from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.email import Email, InvalidEmailError
from app.shared.value_objects.id import ID
from app.modules.clientes.application.dtos.cliente import AtualizarCliente, ClienteResponse
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.exceptions import ClienteInvalidoError, ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_uow import ClienteUnitOfWork
from app.modules.clientes.domain.value_objects.telefone import Telefone, TelefoneInvalidoError

logger = setup_logger(__name__)


@dataclass(frozen=True)
class AtualizarClienteUseCase:
    uow: ClienteUnitOfWork

    async def execute(self, cliente_id: str, dto: AtualizarCliente) -> ClienteResponse:
        """Atualiza os dados de um cliente existente (PATCH — preserva campos não informados).

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ClienteNaoEncontradoError: Se o cliente não for encontrado.
            ClienteInvalidoError: Se os novos dados forem inválidos.
        """
        id_value = ID.from_string(cliente_id)

        async with self.uow:
            existente = await self.uow.cliente_repo.obter_por_id(id_value)
            if not existente:
                raise ClienteNaoEncontradoError(
                    f"Cliente com ID {cliente_id} não encontrado."
                )

            # Resolve novo telefone, se informado
            novo_telefone = existente.telefone
            if dto.telefone is not None:
                try:
                    novo_telefone = Telefone(dto.telefone)
                except TelefoneInvalidoError as e:
                    raise ClienteInvalidoError(str(e))

            # Resolve novo e-mail, se informado
            novo_email = existente.email
            if dto.email is not None:
                try:
                    novo_email = Email(dto.email)
                except InvalidEmailError as e:
                    raise ClienteInvalidoError(str(e))

            agora = datetime.now(UTC)

            atualizado = await self.uow.cliente_repo.atualizar(
                Cliente(
                    id=existente.id,
                    tipo_pessoa=existente.tipo_pessoa,
                    nome_razao_social=dto.nome_razao_social or existente.nome_razao_social,
                    cpf_cnpj=existente.cpf_cnpj,
                    telefone=novo_telefone,
                    email=novo_email,
                    cep=dto.cep if dto.cep is not None else existente.cep,
                    logradouro=dto.logradouro if dto.logradouro is not None else existente.logradouro,
                    numero=dto.numero if dto.numero is not None else existente.numero,
                    complemento=dto.complemento if dto.complemento is not None else existente.complemento,
                    bairro=dto.bairro if dto.bairro is not None else existente.bairro,
                    cidade=dto.cidade if dto.cidade is not None else existente.cidade,
                    uf=dto.uf if dto.uf is not None else existente.uf,
                    ativo=existente.ativo,
                    criado_em=existente.criado_em,
                    atualizado_em=agora,
                )
            )

            if not atualizado:
                raise ClienteNaoEncontradoError(
                    f"Cliente com ID {cliente_id} não encontrado."
                )

            logger.info(f"Cliente {cliente_id} atualizado com sucesso")
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
