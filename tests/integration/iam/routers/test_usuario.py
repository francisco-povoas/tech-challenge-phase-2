"""Testes de integração dos endpoints de usuário (módulo IAM)."""
from uuid import uuid4

import pytest


@pytest.fixture
def rota_usuarios():
    return "/api/v1/usuarios"


@pytest.fixture
def payload_criar_usuario():
    return {"nome": "Teste", "email": "teste@gmail.com", "senha": "senha1234"}


@pytest.fixture
def payload_atualizar():
    return {"nome": "Atualizado", "email": "atualizado@gmail.com"}


async def test_usuario_nao_encontrado(client, rota_usuarios):
    response = await client.get(f"{rota_usuarios}/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"


async def test_criar_usuario_sucesso(client, rota_usuarios, payload_criar_usuario):
    response = await client.post(rota_usuarios, json=payload_criar_usuario)
    data = response.json()
    assert response.status_code == 201
    assert data["email"] == payload_criar_usuario["email"]
    assert "id" in data


async def test_criar_usuario_email_duplicado(client, rota_usuarios, payload_criar_usuario):
    await client.post(rota_usuarios, json=payload_criar_usuario)
    response = await client.post(rota_usuarios, json=payload_criar_usuario)
    assert response.status_code == 409


async def test_obter_usuario_criado(client, rota_usuarios, payload_criar_usuario):
    criar_resp = await client.post(rota_usuarios, json=payload_criar_usuario)
    usuario_id = criar_resp.json()["id"]

    response = await client.get(f"{rota_usuarios}/{usuario_id}")
    assert response.status_code == 200
    assert response.json()["id"] == usuario_id


async def test_remover_usuario(client, rota_usuarios, payload_criar_usuario):
    criar_resp = await client.post(rota_usuarios, json=payload_criar_usuario)
    usuario_id = criar_resp.json()["id"]

    response = await client.delete(f"{rota_usuarios}/{usuario_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"{rota_usuarios}/{usuario_id}")
    assert get_resp.status_code == 404
