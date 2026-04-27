from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.iam.application.dtos.usuario import (
    AtualizarUsuario,
    CriarUsuarioRequest,
    UsuarioResponse,
)
from app.modules.iam.application.use_cases.criar_usuario import CriarUsuarioUseCase
from app.modules.iam.application.use_cases.autenticar_usuario import AutenticarUsuarioUseCase
from app.modules.iam.application.use_cases.obter_usuario import ObterUsuarioUseCase
from app.modules.iam.application.use_cases.listar_usuarios import ListarUsuariosUseCase
from app.modules.iam.application.use_cases.atualizar_usuario import AtualizarUsuarioUseCase
from app.modules.iam.application.use_cases.remover_usuario import RemoverUsuarioUseCase
from app.modules.iam.domain.entities.usuario import Usuario
from app.modules.iam.domain.exceptions import (
    AutenticacaoFalhouError,
    InvalidUsuarioError,
    UsuarioJaExisteError,
    UsuarioNaoEncontradoError,
)
from app.modules.iam.domain.filters.usuario import ListarUsuariosFiltro
from app.shared.value_objects.email import Email
from app.shared.value_objects.id import ID
from app.shared.value_objects.password import Password


# --- Fixtures ---

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.salvar = AsyncMock()
    repo.obter_por_email = AsyncMock(return_value=None)
    repo.obter_por_id = AsyncMock(return_value=None)
    repo.listar = AsyncMock(return_value=[])
    repo.remover = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_uow(mock_repo):
    uow = MagicMock()
    uow.usuario_repo = mock_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def mock_hasher():
    hasher = MagicMock()
    hasher.hash.return_value = "senha_hasheada"
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def usuario_existente():
    return Usuario(
        id=ID.generate(),
        nome="João Silva",
        email=Email("joao@example.com"),
        senha=Password("senha_hasheada"),
        criado_em=datetime.now(UTC) - timedelta(days=3),
        atualizado_em=datetime.now(UTC) - timedelta(days=1),
        ativo=True,
    )


# --- CriarUsuarioUseCase ---

async def test_criar_usuario_sucesso(mock_uow, mock_hasher):
    dto = CriarUsuarioRequest(nome="João", email="joao@example.com", senha="senha1234")
    usecase = CriarUsuarioUseCase(uow=mock_uow, hasher=mock_hasher)

    resultado = await usecase.execute(dto)

    assert isinstance(resultado, UsuarioResponse)
    assert resultado.email == "joao@example.com"
    mock_uow.usuario_repo.salvar.assert_called_once()


async def test_criar_usuario_email_invalido(mock_uow, mock_hasher):
    dto = CriarUsuarioRequest(nome="João", email="email-invalido", senha="senha1234")
    usecase = CriarUsuarioUseCase(uow=mock_uow, hasher=mock_hasher)

    with pytest.raises(InvalidUsuarioError):
        await usecase.execute(dto)


async def test_criar_usuario_email_duplicado(mock_uow, mock_hasher, usuario_existente):
    mock_uow.usuario_repo.obter_por_email.return_value = usuario_existente
    dto = CriarUsuarioRequest(nome="Outro", email="joao@example.com", senha="senha1234")
    usecase = CriarUsuarioUseCase(uow=mock_uow, hasher=mock_hasher)

    with pytest.raises(UsuarioJaExisteError):
        await usecase.execute(dto)


# --- AutenticarUsuarioUseCase ---

async def test_autenticar_usuario_sucesso(mock_repo, mock_hasher, usuario_existente):
    mock_repo.obter_por_email.return_value = usuario_existente
    usecase = AutenticarUsuarioUseCase(usuario_repo=mock_repo, hasher=mock_hasher)

    resultado = await usecase.execute("joao@example.com", "senha1234")

    assert isinstance(resultado, UsuarioResponse)


async def test_autenticar_usuario_senha_errada(mock_repo, mock_hasher, usuario_existente):
    mock_repo.obter_por_email.return_value = usuario_existente
    mock_hasher.verify.return_value = False
    usecase = AutenticarUsuarioUseCase(usuario_repo=mock_repo, hasher=mock_hasher)

    with pytest.raises(AutenticacaoFalhouError):
        await usecase.execute("joao@example.com", "senha_errada")


async def test_autenticar_usuario_nao_encontrado(mock_repo, mock_hasher):
    mock_repo.obter_por_email.return_value = None
    usecase = AutenticarUsuarioUseCase(usuario_repo=mock_repo, hasher=mock_hasher)

    with pytest.raises(AutenticacaoFalhouError):
        await usecase.execute("inexistente@example.com", "senha1234")


# --- ObterUsuarioUseCase ---

async def test_obter_usuario_sucesso(mock_repo, usuario_existente):
    mock_repo.obter_por_id.return_value = usuario_existente
    usecase = ObterUsuarioUseCase(usuario_repo=mock_repo)

    resultado = await usecase.execute(str(usuario_existente.id))

    assert resultado.id == str(usuario_existente.id)


async def test_obter_usuario_nao_encontrado(mock_repo):
    mock_repo.obter_por_id.return_value = None
    usecase = ObterUsuarioUseCase(usuario_repo=mock_repo)

    with pytest.raises(UsuarioNaoEncontradoError):
        await usecase.execute(str(ID.generate()))


# --- RemoverUsuarioUseCase ---

########### ?????
async def test_remover_usuario_sucesso(mock_uow):
    usecase = RemoverUsuarioUseCase(uow=mock_uow)
    resultado = await usecase.execute(str(ID.generate()))
    assert resultado is True


# --- ListarUsuariosUseCase ---

async def test_listar_usuarios_sem_filtros(mock_repo, usuario_existente):
    mock_repo.listar.return_value = [usuario_existente]
    usecase = ListarUsuariosUseCase(usuario_repo=mock_repo)

    resultado = await usecase.execute(ListarUsuariosFiltro())

    assert len(resultado) == 1
    assert resultado[0].email == usuario_existente.email.value
    mock_repo.listar.assert_called_once_with(ListarUsuariosFiltro())


async def test_listar_usuarios_filtrar_por_nome(mock_repo, usuario_existente):
    mock_repo.listar.return_value = [usuario_existente]
    usecase = ListarUsuariosUseCase(usuario_repo=mock_repo)

    filtros = ListarUsuariosFiltro(nome="João")
    resultado = await usecase.execute(filtros)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtros)


async def test_listar_usuarios_filtrar_por_email_valido(mock_repo, usuario_existente):
    mock_repo.listar.return_value = [usuario_existente]
    usecase = ListarUsuariosUseCase(usuario_repo=mock_repo)

    await usecase.execute(ListarUsuariosFiltro(email="joao@example.com"))

    mock_repo.listar.assert_called_once_with(
        ListarUsuariosFiltro(email="joao@example.com", nome=None, ativo=None)
    )


async def test_listar_usuarios_email_invalido(mock_repo):
    usecase = ListarUsuariosUseCase(usuario_repo=mock_repo)

    with pytest.raises(InvalidUsuarioError):
        await usecase.execute(ListarUsuariosFiltro(email="email-invalido"))

    mock_repo.listar.assert_not_called()


async def test_listar_usuarios_filtrar_por_ativo(mock_repo, usuario_existente):
    mock_repo.listar.return_value = [usuario_existente]
    usecase = ListarUsuariosUseCase(usuario_repo=mock_repo)

    filtros = ListarUsuariosFiltro(ativo=True)
    resultado = await usecase.execute(filtros)

    assert len(resultado) == 1
    mock_repo.listar.assert_called_once_with(filtros)
