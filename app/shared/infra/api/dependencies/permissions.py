
from typing import Annotated

from fastapi import Depends, HTTPException

from app.shared.infra.api.dependencies.auth import get_usuario_autenticado
from app.shared.dtos.usuario_autenticado import UsuarioAutenticado
from app.modules.iam.domain.entities.perfil import PerfilTipos


class RequireRoles:
    def __init__(self, *roles: PerfilTipos):
        self.roles = {role.value for role in roles}

    async def __call__(
        self,
        usuario: Annotated[UsuarioAutenticado, Depends(get_usuario_autenticado)],
    ) -> UsuarioAutenticado:
        if not self.roles.intersection(usuario.perfis):
            raise HTTPException(status_code=403, detail="Permissão insuficiente")

        return usuario


# Utilizar quando precisar do usuario autenticado
AdminDep = Annotated[
    UsuarioAutenticado,
    Depends(RequireRoles(PerfilTipos.ADMINISTRADOR)),
]

AtendenteDep = Annotated[
    UsuarioAutenticado,
    Depends(RequireRoles(PerfilTipos.ATENDENTE)),
]

MecanicoDep = Annotated[
    UsuarioAutenticado,
    Depends(RequireRoles(PerfilTipos.MECANICO)),
]