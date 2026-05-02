import re
from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.clientes.application.dtos.cliente import ClienteResponse
from app.modules.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ObterClientePorCpfCnpjUseCase:
    cliente_repo: ClienteRepo

    async def execute(self, cpf_cnpj: str) -> ClienteResponse:
        """Retorna os dados de um cliente pelo CPF/CNPJ.

        O valor informado é normalizado (apenas dígitos) antes da busca.

        Raises:
            ClienteNaoEncontradoError: Se o cliente não for encontrado.
        """
        normalized = re.sub(r"\D", "", cpf_cnpj)
        cliente = await self.cliente_repo.obter_por_cpf_cnpj(normalized)

        if not cliente:
            raise ClienteNaoEncontradoError(
                f"Cliente com CPF/CNPJ {normalized} não encontrado."
            )

        logger.info(f"Cliente com CPF/CNPJ {normalized} obtido com sucesso")
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
