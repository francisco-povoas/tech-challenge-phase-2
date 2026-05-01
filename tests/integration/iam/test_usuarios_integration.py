"""
Testes de integração — módulo IAM — Usuários.

Baseados nos cenários de tests/dev/modules/iam/usuario.http.
Cada teste cria os próprios dados com emails únicos.
Nenhum ID ou JWT é hardcoded.
"""

import uuid

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_email() -> str:
    return f"integ-{uuid.uuid4().hex[:10]}@example.com"


async def _criar_usuario(client: AsyncClient, admin_headers: dict, nome: str, email: str, perfis: list[str]) -> dict:
    """Cria um usuário via API e retorna o body da resposta."""
    response = await client.post(
        "/api/v1/usuarios",
        json={"nome": nome, "email": email, "senha": "senha123", "perfis": perfis},
        headers=admin_headers,
    )
    assert response.status_code in (200, 201), (
        f"Erro ao criar usuário '{email}': {response.status_code} — {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nao_deve_criar_usuario_sem_autenticacao(client: AsyncClient):
    """POST /api/v1/usuarios sem Authorization deve retornar 401 ou 403."""
    response = await client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Sem Auth",
            "email": _unique_email(),
            "senha": "senha123",
            "perfis": ["Atendente"],
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_deve_criar_usuario_atendente(client: AsyncClient, admin_headers: dict):
    """POST /api/v1/usuarios com admin deve criar usuário com perfil Atendente."""
    email = _unique_email()
    body = await _criar_usuario(client, admin_headers, "Francisco Povoas", email, ["Atendente"])
    assert body.get("email") == email or body.get("nome") == "Francisco Povoas"


@pytest.mark.asyncio
async def test_admin_deve_criar_usuario_mecanico(client: AsyncClient, admin_headers: dict):
    """POST /api/v1/usuarios com admin deve criar usuário com perfil Mecanico."""
    email = _unique_email()
    body = await _criar_usuario(client, admin_headers, "Carlos Silva", email, ["Mecanico"])
    assert body.get("email") == email or body.get("nome") == "Carlos Silva"


@pytest.mark.asyncio
async def test_admin_deve_listar_usuarios(client: AsyncClient, admin_headers: dict):
    """GET /api/v1/usuarios com admin deve retornar 200 e uma lista/estrutura paginada."""
    response = await client.get("/api/v1/usuarios", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    # Aceita lista plana ou envelope {"items": [...]}
    assert isinstance(body, list) or isinstance(body, dict)


@pytest.mark.asyncio
async def test_deve_filtrar_usuario_por_email(client: AsyncClient, admin_headers: dict):
    """Cria usuário e filtra por email; deve aparecer no resultado."""
    email = _unique_email()
    await _criar_usuario(client, admin_headers, "Filtro Email", email, ["Atendente"])

    response = await client.get(f"/api/v1/usuarios?email={email}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    items = body if isinstance(body, list) else body.get("items", [])
    emails = [u.get("email") for u in items]
    assert email in emails


@pytest.mark.asyncio
async def test_deve_filtrar_usuario_por_nome(client: AsyncClient, admin_headers: dict):
    """Cria usuário com nome único e filtra por nome; deve aparecer no resultado."""
    unique_suffix = uuid.uuid4().hex[:6]
    nome = f"NomeUnico{unique_suffix}"
    email = _unique_email()
    await _criar_usuario(client, admin_headers, nome, email, ["Mecanico"])

    response = await client.get(f"/api/v1/usuarios?nome={nome}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    items = body if isinstance(body, list) else body.get("items", [])
    nomes = [u.get("nome") for u in items]
    assert any(nome in (n or "") for n in nomes)


@pytest.mark.asyncio
async def test_deve_filtrar_usuario_por_ativo(client: AsyncClient, admin_headers: dict):
    """GET /api/v1/usuarios?ativo=true deve retornar 200."""
    response = await client.get("/api/v1/usuarios?ativo=true", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_deve_buscar_usuario_por_id(client: AsyncClient, admin_headers: dict):
    """Cria usuário, busca por ID e valida dados retornados."""
    email = _unique_email()
    criado = await _criar_usuario(client, admin_headers, "Busca Por ID", email, ["Atendente"])
    usuario_id = criado.get("id")
    assert usuario_id, "Resposta de criação não retornou campo 'id'"

    response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body.get("id") == usuario_id
    assert body.get("email") == email


@pytest.mark.asyncio
async def test_admin_deve_atualizar_email_do_usuario(client: AsyncClient, admin_headers: dict):
    """Cria usuário, atualiza email via PATCH e valida novo email."""
    email_original = _unique_email()
    criado = await _criar_usuario(client, admin_headers, "Atualiza Email", email_original, ["Atendente"])
    usuario_id = criado.get("id")
    assert usuario_id, "Resposta de criação não retornou campo 'id'"

    novo_email = _unique_email()
    response = await client.patch(
        f"/api/v1/usuarios/{usuario_id}",
        json={"email": novo_email},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    # Valida novo email se retornado
    if "email" in body:
        assert body["email"] == novo_email


@pytest.mark.asyncio
async def test_admin_deve_deletar_ou_desativar_usuario(client: AsyncClient, admin_headers: dict):
    """Cria usuário, deleta via DELETE e valida comportamento real da API."""
    email = _unique_email()
    criado = await _criar_usuario(client, admin_headers, "Para Deletar", email, ["Atendente"])
    usuario_id = criado.get("id")
    assert usuario_id, "Resposta de criação não retornou campo 'id'"

    response = await client.delete(f"/api/v1/usuarios/{usuario_id}", headers=admin_headers)
    # API pode retornar 200, 202 ou 204
    assert response.status_code in (200, 202, 204)

    # Após deleção físico, espera 404; após soft delete pode retornar ativo=false
    get_response = await client.get(f"/api/v1/usuarios/{usuario_id}", headers=admin_headers)
    if get_response.status_code == 200:
        body = get_response.json()
        # Soft delete: valida que usuário foi desativado
        assert body.get("ativo") is False, "Usuário deveria estar desativado após deleção"
    else:
        # Deleção física: usuário não encontrado
        assert get_response.status_code == 404
