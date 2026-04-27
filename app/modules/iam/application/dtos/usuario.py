from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class CriarUsuarioRequest:
    nome: str
    email: str
    senha: str
    perfis: list[str] = field(default_factory=lambda: ["Atendente"])

@dataclass(frozen=True, kw_only=True)
class UsuarioResponse:
    id: str
    nome: str
    email: str
    # perfis: list[str] = field(default_factory=list)

@dataclass(frozen=True, kw_only=True)
class UsuarioResponseWithPerfis:
    id: str
    nome: str
    email: str
    perfis: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AtualizarUsuario:
    nome: Optional[str] = None
    email: Optional[str] = None

    def __post_init__(self):
        if not self.nome and not self.email:
            raise ValueError("Pelo menos um campo deve ser informado para atualização")
