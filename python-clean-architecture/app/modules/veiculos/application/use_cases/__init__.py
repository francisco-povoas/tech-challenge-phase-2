from app.modules.veiculos.application.use_cases.criar_veiculo import CriarVeiculoUseCase
from app.modules.veiculos.application.use_cases.obter_veiculo_por_id import ObterVeiculoPorIdUseCase
from app.modules.veiculos.application.use_cases.obter_veiculo_por_placa import ObterVeiculoPorPlacaUseCase
from app.modules.veiculos.application.use_cases.listar_veiculos import ListarVeiculosUseCase
from app.modules.veiculos.application.use_cases.atualizar_veiculo import AtualizarVeiculoUseCase
from app.modules.veiculos.application.use_cases.remover_veiculo import RemoverVeiculoUseCase

__all__ = [
    "CriarVeiculoUseCase",
    "ObterVeiculoPorIdUseCase",
    "ObterVeiculoPorPlacaUseCase",
    "ListarVeiculosUseCase",
    "AtualizarVeiculoUseCase",
    "RemoverVeiculoUseCase",
]
