from fastapi import APIRouter, HTTPException

from app.modules.iam.application.dtos.auth import TokenResponse
from app.modules.iam.application.dtos.usuario import UsuarioResponseWithPerfis
from app.modules.iam.domain.exceptions import AutenticacaoFalhouError
from app.modules.iam.presentation.dependencies import AutenticarUsuario
from app.shared.infra.api.dependencies.erro_response import ErrorResponse
from app.modules.iam.presentation.dependencies.auth import (
    Oauth2Form,
    TokenProvider,
    UsuarioAtual,
)

router = APIRouter()


@router.post(
    "/token",
    summary="Gera token de acesso",
    description="""
    Autentica um usuário e retorna um token JWT.

    Esta rota espera `application/x-www-form-urlencoded`.

    Campos obrigatórios:
    - `username`: e-mail do usuário
    - `password`: senha do usuário

    Exemplo:
    `username=admin@example.com&password=admin123`
    """,
    responses={
        200: {"description": "Autenticado com sucesso", "model": TokenResponse},
        401: {"description": "Credenciais inválidas", "model": ErrorResponse},
    },
    operation_id="Credentials",
)
async def token(
    usecase: AutenticarUsuario,
    form_data: Oauth2Form,
    token_provider: TokenProvider,
) -> TokenResponse:
    try:
        usuario = await usecase.execute(form_data.username, form_data.password)
        token_data = token_provider.create_access_token({
            "sub": str(usuario.id),
            "perfis": usuario.perfis          
            })
        return TokenResponse(
            expire=token_data["expire"],
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
        )
    except AutenticacaoFalhouError:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    summary="Retorna dados do usuário autenticado",
    responses={
        200: {"description": "Dados do usuário"},
        401: {"description": "Não autenticado"},
    },
)
async def me(usuario_atual: UsuarioAtual) -> UsuarioResponseWithPerfis:
    return usuario_atual
