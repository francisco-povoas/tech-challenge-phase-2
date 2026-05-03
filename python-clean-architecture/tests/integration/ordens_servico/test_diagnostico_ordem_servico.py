"""
Testes de integração — Diagnóstico da Ordem de Serviço.

Rotas testadas:
  PATCH /api/v1/ordens-servico/{id}/iniciar-diagnostico
  PATCH /api/v1/ordens-servico/{id}/diagnostico

Permissões:
  Administrador e Mecânico podem iniciar e registrar diagnóstico.
  Atendente NÃO pode.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_em_diagnostico,
    criar_os_recebida,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Iniciar diagnóstico
# ---------------------------------------------------------------------------


async def test_mecanico_deve_iniciar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "EM_DIAGNOSTICO"
    assert data["id"] == os_id


async def test_admin_deve_iniciar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "EM_DIAGNOSTICO"


async def test_atendente_nao_deve_iniciar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=atendente["headers"],
    )
    assert response.status_code == 403


async def test_nao_deve_iniciar_diagnostico_duas_vezes(
    client: AsyncClient, admin_headers: dict
):
    """OS já está em EM_DIAGNOSTICO — segunda tentativa deve falhar."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # Primeira vez — deve funcionar
    r1 = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=mecanico["headers"],
    )
    assert r1.status_code == 200

    # Segunda vez — transição inválida
    r2 = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=mecanico["headers"],
    )
    assert r2.status_code in (400, 422)


async def test_iniciar_diagnostico_em_os_inexistente_retorna_404(
    client: AsyncClient, admin_headers: dict
):
    id_inexistente = str(uuid.uuid4())
    response = await client.patch(
        f"{_BASE}/{id_inexistente}/iniciar-diagnostico",
        headers=admin_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Registrar diagnóstico
# ---------------------------------------------------------------------------


async def test_mecanico_deve_registrar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas de freio"},
        headers=mecanico["headers"],
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "EM_DIAGNOSTICO"
    assert data["diagnostico"] == "Desgaste nas pastilhas de freio"


async def test_admin_deve_registrar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Problema no sistema de freio ABS"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["diagnostico"] == "Problema no sistema de freio ABS"


async def test_atendente_nao_deve_registrar_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Diagnóstico não autorizado"},
        headers=atendente["headers"],
    )
    assert response.status_code == 403


async def test_nao_deve_registrar_diagnostico_antes_de_iniciar(
    client: AsyncClient, admin_headers: dict
):
    """OS ainda em RECEBIDA — registrar diagnóstico deve falhar."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Diagnóstico sem iniciar"},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_registrar_diagnostico_vazio(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": ""},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_pode_atualizar_diagnostico_multiplas_vezes(
    client: AsyncClient, admin_headers: dict
):
    """Registrar diagnóstico é idempotente — pode ser chamado várias vezes."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Diagnóstico inicial"},
        headers=mecanico["headers"],
    )
    r2 = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Diagnóstico revisado"},
        headers=mecanico["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["diagnostico"] == "Diagnóstico revisado"
