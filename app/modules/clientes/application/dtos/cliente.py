from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class CriarClienteRequest:
    tipo_pessoa: str
    nome_razao_social: str
    cpf_cnpj: str
    telefone: str
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class ClienteResponse:
    id: str
    tipo_pessoa: str
    nome_razao_social: str
    cpf_cnpj: str
    telefone: str
    email: Optional[str]
    cep: Optional[str]
    logradouro: Optional[str]
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    ativo: bool


@dataclass(frozen=True)
class AtualizarCliente:
    nome_razao_social: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None

    def __post_init__(self) -> None:
        fields = [
            self.nome_razao_social,
            self.telefone,
            self.email,
            self.cep,
            self.logradouro,
            self.numero,
            self.complemento,
            self.bairro,
            self.cidade,
            self.uf,
        ]
        if all(f is None for f in fields):
            raise ValueError("Pelo menos um campo deve ser informado para atualização.")
