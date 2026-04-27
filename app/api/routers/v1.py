from fastapi import APIRouter

from app.modules.iam.presentation.routers import auth, usuario
from app.modules.veiculos.presentation.routers import veiculo

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])
router.include_router(veiculo.router, prefix="/veiculos", tags=["Veículos"])
