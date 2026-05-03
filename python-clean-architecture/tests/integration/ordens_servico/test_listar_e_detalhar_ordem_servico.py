"""
Testes de integração — Listar e Detalhar Ordem de Serviço.

Rotas testadas:
  GET /api/v1/ordens-servico
  GET /api/v1/ordens-servico/{id}

Permissões: Administrador, Atendente e Mecânico podem listar e detalhar.

Filtros suportados pela API:
  status, cliente_id, veiculo_id, data_inicio, data_fim

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_recebida,
    extrair_items,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------


async def test_atendente_deve_listar_os(client: AsyncClient, admin_headers: dict):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(_BASE, headers=atendente["headers"])
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids


async def test_admin_deve_listar_os(client: AsyncClient, admin_headers: dict):
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids


async def test_mecanico_deve_listar_os(client: AsyncClient, admin_headers: dict):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(_BASE, headers=mecanico["headers"])
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids


# ---------------------------------------------------------------------------
# Detalhe
# ---------------------------------------------------------------------------


async def test_atendente_deve_detalhar_os(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(f"{_BASE}/{os_id}", headers=atendente["headers"])
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == os_id
    assert data["status"] == "RECEBIDA"
    assert "servicos" in data
    assert "itens" in data


async def test_mecanico_deve_detalhar_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(f"{_BASE}/{os_id}", headers=mecanico["headers"])
    assert response.status_code == 200
    assert response.json()["id"] == os_id


async def test_deve_retornar_404_para_os_inexistente(
    client: AsyncClient, admin_headers: dict
):
    id_inexistente = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{id_inexistente}", headers=admin_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


async def test_deve_filtrar_os_por_status(
    client: AsyncClient, admin_headers: dict
):
    """Filtra por status=RECEBIDA — a OS criada deve aparecer."""
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(
        _BASE, params={"status": "RECEBIDA"}, headers=admin_headers
    )
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids
    # Todos os resultados devem ter status RECEBIDA
    assert all(i["status"] == "RECEBIDA" for i in items)


async def test_deve_filtrar_os_por_cliente_id(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    cliente_id = dados["cliente"]["id"]

    response = await client.get(
        _BASE, params={"cliente_id": cliente_id}, headers=admin_headers
    )
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids


async def test_deve_filtrar_os_por_veiculo_id(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    veiculo_id = dados["veiculo"]["id"]

    response = await client.get(
        _BASE, params={"veiculo_id": veiculo_id}, headers=admin_headers
    )
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert os_id in ids
