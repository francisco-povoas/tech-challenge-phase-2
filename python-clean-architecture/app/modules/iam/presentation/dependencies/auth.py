"""Dependências de autenticação do módulo IAM.

Validação de token JWT fica centralizada em `app.shared.infra.api.dependencies.auth`.
"""
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.iam.application.dtos.usuario import UsuarioResponse, UsuarioResponseWithPerfis
from app.modules.iam.presentation.dependencies import ObterUsuario
from app.shared.infra.api.dependencies.auth import TokenProvider, UsuarioAutenticadoDep


_credentials_exception = HTTPException(
    status_code=401,
    detail="Token inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)

Oauth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


async def get_usuario_atual(
    usecase: ObterUsuario,
    usuario_autenticado: UsuarioAutenticadoDep,
) -> UsuarioResponseWithPerfis:
    usuario = await usecase.execute(usuario_autenticado.id)
    if usuario is None:
        raise _credentials_exception
    return usuario


UsuarioAtual = Annotated[UsuarioResponseWithPerfis, Depends(get_usuario_atual)]
