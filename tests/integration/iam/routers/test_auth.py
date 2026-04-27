"""Testes de integração dos endpoints de autenticação (módulo IAM)."""
import pytest


@pytest.fixture
def rota_auth():
    return "/api/v1/auth"


@pytest.fixture
def rota_usuarios():
    return "/api/v1/usuarios"


@pytest.fixture
def payload_usuario():
    return {"nome": "Teste", "email": "teste@gmail.com", "senha": "senha1234"}


@pytest.fixture
def payload_token(payload_usuario):
    return {"username": payload_usuario["email"], "password": payload_usuario["senha"]}


async def test_token_usuario_inexistente(client, rota_auth):
    resp = await client.post(f"{rota_auth}/token", data={"username": "x@x.com", "password": "abc123456"})
    assert resp.status_code == 401


async def test_token_com_credenciais_corretas(client, rota_auth, rota_usuarios, payload_usuario, payload_token):
    await client.post(rota_usuarios, json=payload_usuario)
    resp = await client.post(f"{rota_auth}/token", data=payload_token)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_me_retorna_usuario_autenticado(client, rota_auth, rota_usuarios, payload_usuario, payload_token):
    await client.post(rota_usuarios, json=payload_usuario)
    token_resp = await client.post(f"{rota_auth}/token", data=payload_token)
    token = token_resp.json()["access_token"]

    resp = await client.get(f"{rota_auth}/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == payload_usuario["email"]
