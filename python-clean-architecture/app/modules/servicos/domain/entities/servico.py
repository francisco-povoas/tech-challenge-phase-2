from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.shared.value_objects.id import ID
from app.modules.servicos.domain.exceptions import ServicoInvalidoError


@dataclass(frozen=True, kw_only=True)
class Servico:
    """Entidade de domínio representando um serviço do catálogo da oficina."""

    id: ID
    nome: str
    descricao: Optional[str]
    valor_base: Decimal
    tempo_medio_minutos: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ServicoInvalidoError("O nome do serviço não pode ser vazio.")

        if len(self.nome) > 100:
            raise ServicoInvalidoError(
                "O nome do serviço deve ter no máximo 100 caracteres."
            )

        if self.descricao is not None and len(self.descricao) > 255:
            raise ServicoInvalidoError(
                "A descrição do serviço deve ter no máximo 255 caracteres."
            )

        if self.valor_base < Decimal("0"):
            raise ServicoInvalidoError(
                "O valor base do serviço não pode ser negativo."
            )

        if self.tempo_medio_minutos <= 0:
            raise ServicoInvalidoError(
                "O tempo médio em minutos deve ser maior que zero."
            )
