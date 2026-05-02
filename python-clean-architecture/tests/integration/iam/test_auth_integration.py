"""
Testes de integração — módulo IAM — Autenticação.

Baseados nos cenários de tests/dev/modules/iam/auth.http.
Nenhum JWT é hardcoded; os tokens são obtidos via endpoint real.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deve_autenticar_admin_seedado(client: AsyncClient):
    """POST /api/v1/auth/token com credenciais do admin seedado deve retornar 200 e access_token."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body.get("token_type", "bearer").lower() == "bearer"


@pytest.mark.asyncio
async def test_deve_retornar_me_com_token_admin(client: AsyncClient, admin_headers: dict):
    """GET /api/v1/auth/me com token do admin deve retornar 200 e dados do admin autenticado."""
    response = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    # Valida apenas campos presentes na resposta real — não assume estrutura fixa
    assert isinstance(body, dict)
    # O admin possui perfil Administrador
    perfis = body.get("perfis", [])
    nomes_perfis = [
        (p.get("nome") if isinstance(p, dict) else p)
        for p in perfis
    ]
    assert any("Administrador" in str(p) for p in nomes_perfis)


@pytest.mark.asyncio
async def test_nao_deve_autenticar_com_senha_errada(client: AsyncClient):
    """POST /api/v1/auth/token com senha errada deve retornar 400 ou 401."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "senha_errada"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in (400, 401)


@pytest.mark.asyncio
async def test_nao_deve_acessar_me_sem_token(client: AsyncClient):
    """GET /api/v1/auth/me sem token deve retornar 401 ou 403."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
