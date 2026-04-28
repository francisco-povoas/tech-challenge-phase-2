from typing import Optional

from sqlmodel import select

from app.shared.infra.db import DBSession
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.modules.clientes.domain.entities.cliente import Cliente
from app.modules.clientes.domain.filters.cliente import ListarClientesFiltro
from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj
from app.modules.clientes.domain.value_objects.telefone import Telefone
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa
from app.modules.clientes.infrastructure.db.models.cliente import ClienteModel


class ClienteRepo:
    """Implementação concreta do repositório de clientes (SQLModel + PostgreSQL)."""

    def __init__(self, session: DBSession) -> None:
        self.session = session

    async def salvar(self, cliente: Cliente) -> None:
        model = ClienteModel(
            id=cliente.id.value,
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
            criado_em=cliente.criado_em,
            atualizado_em=cliente.atualizado_em,
        )
        self.session.add(model)

    async def obter_por_id(self, _id: ID) -> Optional[Cliente]:
        model = await self.session.get(ClienteModel, _id.value)
        if not model:
            return None
        return self._to_entity(model)

    async def obter_por_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Cliente]:
        result = await self.session.exec(
            select(ClienteModel).where(ClienteModel.cpf_cnpj == cpf_cnpj)
        )
        model = result.first()
        if not model:
            return None
        return self._to_entity(model)

    async def atualizar(self, cliente: Cliente) -> Optional[Cliente]:
        model = await self.session.get(ClienteModel, cliente.id.value)
        if not model:
            return None
        model.nome_razao_social = cliente.nome_razao_social
        model.telefone = cliente.telefone.value
        model.email = cliente.email.value if cliente.email else None
        model.cep = cliente.cep
        model.logradouro = cliente.logradouro
        model.numero = cliente.numero
        model.complemento = cliente.complemento
        model.bairro = cliente.bairro
        model.cidade = cliente.cidade
        model.uf = cliente.uf
        model.ativo = cliente.ativo
        model.atualizado_em = cliente.atualizado_em
        self.session.add(model)
        return cliente

    async def remover(self, _id: ID) -> bool:
        model = await self.session.get(ClienteModel, _id.value)
        if not model:
            return False
        await self.session.delete(model)
        return True

    async def listar(self, filtros: ListarClientesFiltro) -> list[Cliente]:
        query = select(ClienteModel)

        if filtros.nome:
            query = query.where(
                ClienteModel.nome_razao_social.ilike(f"%{filtros.nome}%")
            )
        if filtros.cpf_cnpj:
            query = query.where(ClienteModel.cpf_cnpj == filtros.cpf_cnpj)
        if filtros.ativo is not None:
            query = query.where(ClienteModel.ativo == filtros.ativo)

        result = await self.session.exec(query)
        return [self._to_entity(model) for model in result.all()]

    @staticmethod
    def _to_entity(model: ClienteModel) -> Cliente:
        return Cliente(
            id=ID.from_string(str(model.id)),
            tipo_pessoa=TipoPessoa(model.tipo_pessoa),
            nome_razao_social=model.nome_razao_social,
            cpf_cnpj=CpfCnpj(model.cpf_cnpj),
            telefone=Telefone(model.telefone),
            email=Email(model.email) if model.email else None,
            cep=model.cep,
            logradouro=model.logradouro,
            numero=model.numero,
            complemento=model.complemento,
            bairro=model.bairro,
            cidade=model.cidade,
            uf=model.uf,
            ativo=model.ativo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )
