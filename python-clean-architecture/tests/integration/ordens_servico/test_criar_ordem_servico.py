"""
Testes de integração — Criar Ordem de Serviço.

Rotas testadas:
  POST /api/v1/ordens-servico

Permissões:
  Administrador e Atendente podem criar OS.
  Mecânico NÃO pode criar OS.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    autenticar,
    criar_atendente,
    criar_cliente,
    criar_mecanico,
    criar_ordem_servico,
    criar_veiculo,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Sem autenticação
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_os_sem_autenticacao(client: AsyncClient):
    payload = {
        "cliente_id": str(uuid.uuid4()),
        "veiculo_id": str(uuid.uuid4()),
        "queixa_inicial": "Barulho no motor",
    }
    response = await client.post(_BASE, json=payload)
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Atendente cria OS
# ---------------------------------------------------------------------------


async def test_atendente_deve_criar_os(client: AsyncClient, admin_headers: dict):
    atendente = await criar_atendente(client, admin_headers)
    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])

    response = await client.post(
        _BASE,
        json={
            "cliente_id": cliente["id"],
            "veiculo_id": veiculo["id"],
            "queixa_inicial": "Motor fazendo barulho ao acelerar",
        },
        headers=atendente["headers"],
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"]
    assert data["status"] == "RECEBIDA"
    assert data["cliente_id"] == cliente["id"]
    assert data["veiculo_id"] == veiculo["id"]
    assert data["queixa_inicial"] == "Motor fazendo barulho ao acelerar"
    assert data["diagnostico"] is None


# ---------------------------------------------------------------------------
# Admin cria OS
# ---------------------------------------------------------------------------


async def test_admin_deve_criar_os(client: AsyncClient, admin_headers: dict):
    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])

    os_ = await criar_ordem_servico(
        client, admin_headers, cliente["id"], veiculo["id"],
        queixa_inicial="Freio falhando ao parar",
    )

    assert os_["id"]
    assert os_["status"] == "RECEBIDA"
    assert os_["cliente_id"] == cliente["id"]
    assert os_["veiculo_id"] == veiculo["id"]
    assert os_["queixa_inicial"] == "Freio falhando ao parar"


# ---------------------------------------------------------------------------
# Cliente inexistente
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_os_com_cliente_inexistente(
    client: AsyncClient, admin_headers: dict
):
    cliente_id_falso = str(uuid.uuid4())
    veiculo_id_falso = str(uuid.uuid4())

    response = await client.post(
        _BASE,
        json={
            "cliente_id": cliente_id_falso,
            "veiculo_id": veiculo_id_falso,
            "queixa_inicial": "Qualquer queixa",
        },
        headers=admin_headers,
    )
    assert response.status_code in (404, 422)


# ---------------------------------------------------------------------------
# Veículo inexistente
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_os_com_veiculo_inexistente(
    client: AsyncClient, admin_headers: dict
):
    cliente = await criar_cliente(client, admin_headers)
    veiculo_id_falso = str(uuid.uuid4())

    response = await client.post(
        _BASE,
        json={
            "cliente_id": cliente["id"],
            "veiculo_id": veiculo_id_falso,
            "queixa_inicial": "Qualquer queixa",
        },
        headers=admin_headers,
    )
    assert response.status_code in (404, 422)


# ---------------------------------------------------------------------------
# Veículo de outro cliente
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_os_com_veiculo_de_outro_cliente(
    client: AsyncClient, admin_headers: dict
):
    cliente_a = await criar_cliente(client, admin_headers)
    cliente_b = await criar_cliente(client, admin_headers)
    veiculo_b = await criar_veiculo(client, admin_headers, cliente_b["id"])

    # Tentativa de criar OS para cliente_a com veículo do cliente_b
    response = await client.post(
        _BASE,
        json={
            "cliente_id": cliente_a["id"],
            "veiculo_id": veiculo_b["id"],
            "queixa_inicial": "Qualquer queixa",
        },
        headers=admin_headers,
    )
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Mecânico não pode criar OS
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_criar_os(client: AsyncClient, admin_headers: dict):
    mecanico = await criar_mecanico(client, admin_headers)
    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])

    response = await client.post(
        _BASE,
        json={
            "cliente_id": cliente["id"],
            "veiculo_id": veiculo["id"],
            "queixa_inicial": "Qualquer queixa",
        },
        headers=mecanico["headers"],
    )
    assert response.status_code == 403
