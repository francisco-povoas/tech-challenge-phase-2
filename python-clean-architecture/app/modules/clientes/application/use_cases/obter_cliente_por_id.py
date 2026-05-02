from dataclasses import dataclass

from app.logger import setup_logger
from app.shared.value_objects.id import ID
from app.modules.clientes.application.dtos.cliente import ClienteResponse
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterClientePorIdUseCase:
    cliente_repo: ClienteRepo

    async def execute(self, cliente_id: str) -> ClienteResponse:
        """Retorna os dados de um cliente pelo ID.

        Raises:
            InvalidIDError: Se o formato do ID for inválido.
            ClienteNaoEncontradoError: Se o cliente não for encontrado.
        """
        id_value = ID.from_string(cliente_id)
        cliente = await self.cliente_repo.obter_por_id(id_value)

        if not cliente:
            raise ClienteNaoEncontradoError(f"Cliente com ID {cliente_id} não encontrado.")

        logger.info(f"Cliente {cliente_id} obtido com sucesso")
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
