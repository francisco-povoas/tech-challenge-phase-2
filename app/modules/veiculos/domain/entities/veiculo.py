from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.exceptions import VeiculoInvalidoError
from app.modules.veiculos.domain.value_objects.placa import Placa

_ANO_MINIMO = 1900


@dataclass(frozen=True, kw_only=True)
class Veiculo:
    """Entidade de domínio representando um veículo da oficina."""

    id: ID
    cliente_id: UUID
    placa: Placa
    marca: str
    modelo: str
    ano_fabricacao: Optional[int]
    ano_modelo: Optional[int]
    cor: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

    def __post_init__(self) -> None:
        if not self.marca or not self.marca.strip():
            raise VeiculoInvalidoError("A marca do veículo não pode ser vazia.")
        if len(self.marca) > 60:
            raise VeiculoInvalidoError("A marca deve ter no máximo 60 caracteres.")

        if not self.modelo or not self.modelo.strip():
            raise VeiculoInvalidoError("O modelo do veículo não pode ser vazio.")
        if len(self.modelo) > 60:
            raise VeiculoInvalidoError("O modelo deve ter no máximo 60 caracteres.")

        if self.cor is not None and len(self.cor) > 30:
            raise VeiculoInvalidoError("A cor deve ter no máximo 30 caracteres.")

        if self.ano_fabricacao is not None and self.ano_fabricacao < _ANO_MINIMO:
            raise VeiculoInvalidoError(
                f"Ano de fabricação deve ser maior ou igual a {_ANO_MINIMO}."
            )

        if self.ano_modelo is not None and self.ano_modelo < _ANO_MINIMO:
            raise VeiculoInvalidoError(
                f"Ano do modelo deve ser maior ou igual a {_ANO_MINIMO}."
            )
