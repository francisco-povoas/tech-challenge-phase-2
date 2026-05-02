from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.modules.clientes.domain.exceptions import ClienteInvalidoError
from app.modules.clientes.domain.value_objects.cpf_cnpj import CpfCnpj
from app.modules.clientes.domain.value_objects.telefone import Telefone
from app.modules.clientes.domain.value_objects.tipo_pessoa import TipoPessoa


@dataclass(frozen=True, kw_only=True)
class Cliente:
    """Entidade de domínio representando um cliente da oficina."""

    id: ID
    tipo_pessoa: TipoPessoa
    nome_razao_social: str
    cpf_cnpj: CpfCnpj
    telefone: Telefone
    email: Email
    cep: Optional[str]
    logradouro: Optional[str]
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    def __post_init__(self) -> None:
        if not self.nome_razao_social or not self.nome_razao_social.strip():
            raise ClienteInvalidoError("O nome/razão social do cliente não pode ser vazio.")

        if self.tipo_pessoa == TipoPessoa.PF and len(self.cpf_cnpj.value) != 11:
            raise ClienteInvalidoError(
                "Para pessoa física (PF) o CPF deve conter exatamente 11 dígitos."
            )

        if self.tipo_pessoa == TipoPessoa.PJ and len(self.cpf_cnpj.value) != 14:
            raise ClienteInvalidoError(
                "Para pessoa jurídica (PJ) o CNPJ deve conter exatamente 14 dígitos."
            )

        if self.uf is not None and len(self.uf) != 2:
            raise ClienteInvalidoError("UF deve ter exatamente 2 caracteres.")

        if self.cep is not None and len(self.cep) != 8:
            raise ClienteInvalidoError("CEP deve ter exatamente 8 dígitos.")
