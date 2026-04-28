from dataclasses import dataclass

from app.logger import setup_logger
from app.modules.clientes.application.dtos.cliente import ClienteResponse
from app.modules.clientes.domain.filters.cliente import ListarClientesFiltro
from app.modules.clientes.domain.ports.cliente_repo import ClienteRepo

logger = setup_logger(__name__)


@dataclass(frozen=True)
class ListarClientesUseCase:
    cliente_repo: ClienteRepo

    async def execute(self, filtros: ListarClientesFiltro) -> list[ClienteResponse]:
        """Lista clientes com filtros opcionais por nome, CPF/CNPJ e status ativo."""
        clientes = await self.cliente_repo.listar(filtros)

        logger.info(
            "Listagem de clientes executada com filtros nome=%s cpf_cnpj=%s ativo=%s",
            filtros.nome,
            filtros.cpf_cnpj,
            filtros.ativo,
        )
        return [
            ClienteResponse(
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
            for cliente in clientes
        ]
