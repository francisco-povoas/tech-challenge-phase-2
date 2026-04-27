from dataclasses import dataclass

from app.shared.value_objects.id import ID
from app.modules.veiculos.domain.exceptions import VeiculoInvalidoError


@dataclass(frozen=True, kw_only=True)
class Veiculo:
    """Entidade de domínio representando um veículo."""

    id: ID
    placa: str
    marca: str
    modelo: str
    ano: int
    cliente_id: str  # referência ao cliente — apenas o ID, sem importar o módulo clientes

    def __post_init__(self):
        if not self.placa or not self.placa.strip():
            raise VeiculoInvalidoError("A placa do veículo não pode ser vazia")
        if self.ano < 1886 or self.ano > 2100:
            raise VeiculoInvalidoError(f"Ano de fabricação inválido: {self.ano}")
