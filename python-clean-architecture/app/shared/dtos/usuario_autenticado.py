from dataclasses import dataclass, field


@dataclass(frozen=True)
class UsuarioAutenticado:
    """DTO com os dados de identidade extraídos do token JWT.

    Compartilhado por todos os módulos que precisam de informação
    sobre o usuário autenticado — sem acoplamento ao módulo IAM.
    """

    id: str
    perfis: list[str] = field(default_factory=list)
