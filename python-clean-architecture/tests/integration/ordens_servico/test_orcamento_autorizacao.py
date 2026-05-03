"""
Testes de integração — Autorização das rotas de Orçamento.

Rotas testadas:
  POST /api/v1/ordens-servico/{id}/orcamento
  GET  /api/v1/ordens-servico/{id}/orcamento
  GET  /api/v1/ordens-servico/{id}/orcamento/comunicacoes

Regras:
  - Sem token → 401
  - Mecânico no POST → 403
  - Administrador, Atendente → pode gerar (POST)
  - Administrador, Atendente, Mecânico → pode consultar (GET)

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_diagnostico_concluido_para_orcamento,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# POST /{id}/orcamento
# ---------------------------------------------------------------------------


async def test_post_orcamento_sem_token_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento")

    assert response.status_code == 401


async def test_post_orcamento_mecanico_retorna_403(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=dados["mecanico_headers"]
    )

    assert response.status_code == 403


async def test_post_orcamento_admin_retorna_201(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 201


async def test_post_orcamento_atendente_retorna_201(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=dados["atendente_headers"]
    )

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /{id}/orcamento
# ---------------------------------------------------------------------------


async def test_get_orcamento_sem_token_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento")

    assert response.status_code == 401


async def test_get_orcamento_mecanico_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    """Mecânico pode consultar mas não gerar."""
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento", headers=dados["mecanico_headers"]
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /{id}/orcamento/comunicacoes
# ---------------------------------------------------------------------------


async def test_get_comunicacoes_sem_token_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento/comunicacoes")

    assert response.status_code == 401


async def test_get_comunicacoes_mecanico_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=dados["mecanico_headers"]
    )

    assert response.status_code == 200
