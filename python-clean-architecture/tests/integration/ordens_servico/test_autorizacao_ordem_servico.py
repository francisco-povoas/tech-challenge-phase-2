"""
Testes de integração — Autorização transversal de Ordens de Serviço.

Cobre cenários de autorização que não se encaixam nos arquivos específicos,
evitando duplicação excessiva.

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
# Sem token — endpoints principais
# ---------------------------------------------------------------------------


async def test_sem_token_nao_deve_listar_os(client: AsyncClient):
    response = await client.get(_BASE)
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_detalhar_os(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{id_qualquer}")
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_iniciar_diagnostico(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.patch(f"{_BASE}/{id_qualquer}/iniciar-diagnostico")
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_registrar_diagnostico(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.patch(
        f"{_BASE}/{id_qualquer}/diagnostico",
        json={"diagnostico": "Qualquer texto"},
    )
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_adicionar_servico(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.post(
        f"{_BASE}/{id_qualquer}/servicos",
        json={"servico_id": str(uuid.uuid4()), "observacao": None},
    )
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_adicionar_item(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.post(
        f"{_BASE}/{id_qualquer}/itens",
        json={"item_estoque_id": str(uuid.uuid4()), "quantidade": 1},
    )
    assert response.status_code in (401, 403)


async def test_sem_token_nao_deve_concluir_diagnostico(client: AsyncClient):
    id_qualquer = str(uuid.uuid4())
    response = await client.patch(f"{_BASE}/{id_qualquer}/concluir-diagnostico")
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Atendente não pode executar ações de Mecânico
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_executar_acoes_de_mecanico(
    client: AsyncClient, admin_headers: dict
):
    """
    Testa que Atendente não consegue realizar nenhuma das ações restritas
    a Mecânico/Administrador em uma única OS.
    """
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # Não pode iniciar diagnóstico
    r1 = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=atendente["headers"],
    )
    assert r1.status_code == 403

    # Não pode registrar diagnóstico
    r2 = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Tentativa não autorizada"},
        headers=atendente["headers"],
    )
    assert r2.status_code == 403

    # Não pode concluir diagnóstico
    r3 = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=atendente["headers"],
    )
    assert r3.status_code == 403


# ---------------------------------------------------------------------------
# Mecânico não pode criar OS
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_criar_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)

    response = await client.post(
        _BASE,
        json={
            "cliente_id": dados["cliente"]["id"],
            "veiculo_id": dados["veiculo"]["id"],
            "queixa_inicial": "Tentativa não autorizada",
        },
        headers=mecanico["headers"],
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Mecânico não pode adicionar/remover itens de estoque
# (confirma que acesso ao módulo estoque é bloqueado)
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_remover_servico_da_os(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    oss_id_falso = str(uuid.uuid4())

    response = await client.delete(
        f"{_BASE}/{os_id}/servicos/{oss_id_falso}",
        headers=atendente["headers"],
    )
    assert response.status_code == 403


async def test_atendente_nao_deve_remover_item_da_os(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    osi_id_falso = str(uuid.uuid4())

    response = await client.delete(
        f"{_BASE}/{os_id}/itens/{osi_id_falso}",
        headers=atendente["headers"],
    )
    assert response.status_code == 403
