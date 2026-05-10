"""Dependências de autenticação compartilhadas por todos os módulos.

Qualquer router de qualquer módulo pode usar `UsuarioAutenticadoDep`
para exigir que o requisitante esteja autenticado e obter sua identidade.
"""
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.shared.dtos.usuario_autenticado import UsuarioAutenticado
from app.shared.infra.security.jwt import InvalidToken, JWTProvider

_credentials_exception = HTTPException(
    status_code=401,
    detail="Token inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
Oauth2Token = Annotated[str, Depends(oauth2_scheme)]


def get_jwt_provider() -> JWTProvider:
    settings = get_settings()
    return JWTProvider(
        settings.JWT_SECRET_KEY,
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        settings.JWT_ALGORITHM,
    )


TokenProvider = Annotated[JWTProvider, Depends(get_jwt_provider)]


def get_usuario_autenticado(
    token: Oauth2Token,
    token_provider: TokenProvider,
) -> UsuarioAutenticado:
    """Valida o JWT e retorna os dados de identidade do usuário.

    Pode ser usado como `Depends` em qualquer router de qualquer módulo.
    """
    try:
        user_id, perfis = token_provider.get_sub(token)
        return UsuarioAutenticado(id=user_id, perfis=perfis)
    except InvalidToken:
        raise _credentials_exception


UsuarioAutenticadoDep = Annotated[UsuarioAutenticado, Depends(get_usuario_autenticado)]
