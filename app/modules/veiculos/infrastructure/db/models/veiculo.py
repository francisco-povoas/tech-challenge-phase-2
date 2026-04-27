from uuid import UUID

from sqlmodel import Field, SQLModel


class VeiculoModel(SQLModel, table=True):
    """Modelo ORM da tabela de veículos."""

    __tablename__ = "veiculo"

    id: UUID = Field(primary_key=True)
    placa: str = Field(unique=True, index=True)
    marca: str
    modelo: str
    ano: int
    cliente_id: str  # FK para a tabela cliente (sem FK declarada — desacoplamento entre módulos)
