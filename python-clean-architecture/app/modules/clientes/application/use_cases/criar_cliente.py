from dataclasses import dataclass
from datetime import UTC, datetime

from app.logger import setup_logger
from app.shared.value_objects.email import Email, InvalidEmailError
from app.shared.value_objects.id import ID
from app.modules.clientes.application.dtos.cliente import CriarClienteRequest, ClienteResponse
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.exceptions import (
    ClienteInvalidoError,
    CpfCnpjJaCadastradoError,
)
from app.modules.clientes.domain.ports.cliente_uow import ClienteUnitOfWork
from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj, CpfCnpjInvalidoError
from app.modules.clientes.domain.value_objects.telefone import Telefone, TelefoneInvalidoError
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa, TipoPessoaInvalidoError

logger = setup_logger(__name__)


@dataclass(frozen=True)
class CriarClienteUseCase:
    uow: ClienteUnitOfWork

    async def execute(self, dto: CriarClienteRequest) -> ClienteResponse:
        """Cria um novo cliente, garantindo unicidade de CPF/CNPJ.

        Raises:
            ClienteInvalidoError: Se os dados fornecidos forem inválidos.
            CpfCnpjJaCadastradoError: Se já existir cliente com o mesmo CPF/CNPJ.
        """
        try:
            tipo_pessoa = TipoPessoa(dto.tipo_pessoa)
        except ValueError:
            raise ClienteInvalidoError(
                f"Tipo de pessoa inválido: '{dto.tipo_pessoa}'. "
                f"Deve ser um dos seguintes: {', '.join(TipoPessoa.tipos())}."
            )

        try:
            cpf_cnpj = CpfCnpj(dto.cpf_cnpj)
        except CpfCnpjInvalidoError as e:
            raise ClienteInvalidoError(str(e))

        try:
            telefone = Telefone(dto.telefone)
        except TelefoneInvalidoError as e:
            raise ClienteInvalidoError(str(e))

        email: Email | None = None
        if dto.email:
            try:
                email = Email(dto.email)
            except InvalidEmailError as e:
                raise ClienteInvalidoError(str(e))

        async with self.uow:
            if await self.uow.cliente_repo.obter_por_cpf_cnpj(cpf_cnpj.value):
                logger.warning(f"CPF/CNPJ {cpf_cnpj.value} já cadastrado")
                raise CpfCnpjJaCadastradoError(
                    f"Já existe um cliente com o CPF/CNPJ {cpf_cnpj.value}."
                )

            agora = datetime.now(UTC)

            cliente = Cliente(
                id=ID.generate(),
                tipo_pessoa=tipo_pessoa,
                nome_razao_social=dto.nome_razao_social,
                cpf_cnpj=cpf_cnpj,
                telefone=telefone,
                email=email,
                cep=dto.cep,
                logradouro=dto.logradouro,
                numero=dto.numero,
                complemento=dto.complemento,
                bairro=dto.bairro,
                cidade=dto.cidade,
                uf=dto.uf,
                ativo=True,
                criado_em=agora,
                atualizado_em=agora,
            )

            await self.uow.cliente_repo.salvar(cliente)
            logger.info(f"Cliente {cpf_cnpj.value} criado com sucesso")

            return ClienteResponse(
                id=str(cliente.id),
                tipo_pessoa=cliente.tipo_pessoa.value,
                nome_razao_social=cliente.nome_razao_social,
                cpf_cnpj=cliente.cpf_cnpj.value,
                telefone=cliente.telefone.value,
                email=cliente.email.value if cliente.email else None,
                cep=cliente.cep,
                logradouro=cliente.logradouro,
                numero=cliente.numero,
                complemento=cliente.complemento,
                bairro=cliente.bairro,
                cidade=cliente.cidade,
                uf=cliente.uf,
                ativo=cliente.ativo,
            )
