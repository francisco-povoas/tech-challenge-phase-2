"""
Testes de integração — Consultar Orçamento da Ordem de Serviço.

Rota testada:
  GET /api/v1/ordens-servico/{id}/orcamento

Permissões:
  Administrador, Atendente e Mecânico podem consultar.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_diagnostico_concluido_para_orcamento,
    criar_os_recebida,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Casos de sucesso
# ---------------------------------------------------------------------------


async def test_admin_consulta_orcamento_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 200


async def test_atendente_consulta_orcamento_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento", headers=dados["atendente_headers"]
    )

    assert response.status_code == 200


async def test_mecanico_consulta_orcamento_retorna_200(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(
        f"{_BASE}/{os_id}/orcamento", headers=dados["mecanico_headers"]
    )

    assert response.status_code == 200


async def test_orcamento_consultado_totais_corretos(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)
    payload = response.json()

    assert normalizar_numero(payload["total_servicos"]) == Decimal("180.00")
    assert normalizar_numero(payload["total_itens"]) == Decimal("390.00")
    assert normalizar_numero(payload["total_geral"]) == Decimal("570.00")


async def test_orcamento_consultado_inclui_comunicacoes(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)
    payload = response.json()

    assert "comunicacoes" in payload
    assert len(payload["comunicacoes"]) >= 1


# ---------------------------------------------------------------------------
# Casos de erro
# ---------------------------------------------------------------------------


async def test_consultar_orcamento_inexistente_retorna_404(
    client: AsyncClient, admin_headers: dict
):
    """OS existe mas ainda não tem orçamento."""
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 404


async def test_consultar_orcamento_os_inexistente_retorna_404(
    client: AsyncClient, admin_headers: dict
):
    import uuid

    os_id = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 404


async def test_consultar_orcamento_sem_autenticacao_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    response = await client.get(f"{_BASE}/{os_id}/orcamento")

    assert response.status_code == 401
