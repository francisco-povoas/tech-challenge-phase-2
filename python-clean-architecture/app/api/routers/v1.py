from fastapi import APIRouter

from app.modules.iam.presentation.routers import auth, usuario
from app.modules.veiculos.presentation.routers import veiculo
from app.modules.clientes.presentation.routers import cliente
from app.modules.servicos.presentation.routers import servico
from app.modules.estoque.presentation.routers import item_estoque

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])
router.include_router(veiculo.router, prefix="/veiculos", tags=["Veículos"])
router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
router.include_router(servico.router, prefix="/servicos", tags=["Serviços"])
router.include_router(item_estoque.router, prefix="/itens-estoque", tags=["Itens de Estoque"])