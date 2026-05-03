"""
Testes de integração — Listar Comunicações do Orçamento.

Rota testada:
  GET /api/v1/ordens-servico/{id}/orcamento/comunicacoes

Permissões:
  Administrador, Atendente e Mecânico podem listar.

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
# Casos de sucesso
# ---------------------------------------------------------------------------


async def test_admin_lista_comunicacoes_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=admin_headers
    )

    assert response.status_code == 200


async def test_atendente_lista_comunicacoes_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=dados["atendente_headers"]
    )

    assert response.status_code == 200


async def test_mecanico_lista_comunicacoes_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=dados["mecanico_headers"]
    )

    assert response.status_code == 200


async def test_comunicacoes_incluem_whatsapp_e_email(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=admin_headers
    )
    items = response.json()

    assert isinstance(items, list)
    canais = {item["canal"] for item in items}
    assert "WHATSAPP" in canais
    assert "EMAIL" in canais


async def test_comunicacoes_possuem_campos_obrigatorios(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=admin_headers
    )
    items = response.json()

    for item in items:
        assert "id" in item
        assert "orcamento_id" in item
        assert "canal" in item
        assert "destino" in item
        assert "sucesso" in item
        assert "enviado_em" in item


async def test_comunicacoes_mock_marcadas_como_sucesso(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=admin_headers
    )
    items = response.json()

    for item in items:
        assert item["sucesso"] is True


# ---------------------------------------------------------------------------
# Casos de erro
# ---------------------------------------------------------------------------


async def test_listar_comunicacoes_os_sem_orcamento_retorna_404(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=admin_headers
    )

    assert response.status_code == 404


async def test_listar_comunicacoes_sem_autenticacao_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento/comunicacoes")

    assert response.status_code == 401
