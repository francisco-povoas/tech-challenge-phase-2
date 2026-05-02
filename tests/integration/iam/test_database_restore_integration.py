"""
Testes de verificação da restauração do banco entre testes.

Garantem que:
- dados criados num teste não vazam para o próximo;
- admin@example.com permanece após cada restauração.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cria_usuario_e_confirma_existencia(client: AsyncClient, admin_headers: dict):
    """Cria um usuário e confirma que ele existe — setup para o próximo teste."""
    email = "restore-check@example.com"
    response = await client.post(
        "/api/v1/usuarios",
        json={"nome": "Restore Check", "email": email, "senha": "senha123", "perfis": ["Atendente"]},
        headers=admin_headers,
    )
    assert response.status_code in (200, 201)

    lista = await client.get(f"/api/v1/usuarios?email={email}", headers=admin_headers)
    assert lista.status_code == 200
    items = lista.json() if isinstance(lista.json(), list) else lista.json().get("items", [])
    assert any(u.get("email") == email for u in items), "Usuário deveria existir neste teste"


@pytest.mark.asyncio
async def test_usuario_do_teste_anterior_nao_existe_mais(client: AsyncClient, admin_headers: dict):
    """Após restauração, o usuário criado no teste anterior não deve existir."""
    email = "restore-check@example.com"
    response = await client.get(f"/api/v1/usuarios?email={email}", headers=admin_headers)
    assert response.status_code == 200
    items = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
    assert not any(u.get("email") == email for u in items), (
        f"Usuário '{email}' não deveria existir após restauração do banco"
    )


@pytest.mark.asyncio
async def test_admin_continua_autenticando_apos_restauracao(client: AsyncClient):
    """Admin seedado deve continuar autenticando após qualquer restauração."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
