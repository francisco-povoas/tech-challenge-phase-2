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

from datetime import UTC, datetime, timedelta
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.integration.ordens_servico.factories import (
    criar_os_aprovada_com_item_reservado,
    criar_os_aguardando_itens_com_um_item_a_receber,
    criar_os_com_orcamento_comunicado_todos_itens_reservados,
    criar_os_diagnostico_concluido_para_orcamento,
    criar_os_em_diagnostico,
    criar_os_em_execucao_com_tempo_registrado,
    criar_os_finalizada_com_pagamento,
    criar_os_finalizada_para_pagamento_entrega,
    criar_atendente,
    criar_mecanico,
    criar_os_recebida,
    entregar_os,
    extrair_items,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


async def _atualizar_criado_em(db_url: str, os_id: str, criado_em: datetime) -> None:
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    UPDATE ordem_servico
                    SET criado_em = :criado_em,
                        atualizado_em = :criado_em
                    WHERE id = :os_id
                """),
                {"os_id": os_id, "criado_em": criado_em},
            )
    finally:
        await engine.dispose()


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


async def test_deve_listar_ordenado_por_status_prioritario_e_data_criacao(
    client: AsyncClient,
    admin_headers: dict,
    integration_settings,
):
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    recebida_antiga = await criar_os_recebida(client, admin_headers)
    recebida_recente = await criar_os_recebida(client, admin_headers)
    em_diag_antiga = await criar_os_em_diagnostico(client, admin_headers)
    em_diag_recente = await criar_os_em_diagnostico(client, admin_headers)
    diag_concluida = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    aguardando_aprov_antiga = await criar_os_com_orcamento_comunicado_todos_itens_reservados(
        client, admin_headers
    )
    aguardando_aprov_recente = await criar_os_com_orcamento_comunicado_todos_itens_reservados(
        client, admin_headers
    )
    aprovada = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    aguardando_itens = await criar_os_aguardando_itens_com_um_item_a_receber(
        client, admin_headers
    )
    em_exec_antiga = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    em_exec_recente = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    finalizada = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    entregue = await criar_os_finalizada_com_pagamento(client, admin_headers)
    encerrada = await criar_os_com_orcamento_comunicado_todos_itens_reservados(
        client, admin_headers
    )

    await entregar_os(
        client,
        entregue["atendente_headers"],
        entregue["ordem_servico"]["id"],
    )
    recusa_response = await client.patch(
        f"{_BASE}/{encerrada['ordem_servico']['id']}/orcamento/recusar",
        json={"motivo_recusa": "Cliente recusou o orçamento."},
        headers=encerrada["atendente_headers"],
    )
    assert recusa_response.status_code == 200

    casos = [
        (em_exec_antiga["ordem_servico"]["id"], base + timedelta(days=1)),
        (em_exec_recente["ordem_servico"]["id"], base + timedelta(days=2)),
        (aguardando_aprov_antiga["ordem_servico"]["id"], base + timedelta(days=3)),
        (aguardando_aprov_recente["ordem_servico"]["id"], base + timedelta(days=4)),
        (em_diag_antiga["ordem_servico"]["id"], base + timedelta(days=5)),
        (em_diag_recente["ordem_servico"]["id"], base + timedelta(days=6)),
        (recebida_antiga["ordem_servico"]["id"], base + timedelta(days=7)),
        (recebida_recente["ordem_servico"]["id"], base + timedelta(days=8)),
        (diag_concluida["ordem_servico"]["id"], base + timedelta(days=9)),
        (aprovada["ordem_servico"]["id"], base + timedelta(days=10)),
        (aguardando_itens["ordem_servico"]["id"], base + timedelta(days=11)),
        (finalizada["ordem_servico"]["id"], base + timedelta(days=12)),
        (entregue["ordem_servico"]["id"], base + timedelta(days=13)),
        (encerrada["ordem_servico"]["id"], base + timedelta(days=14)),
    ]
    for os_id, criado_em in casos:
        await _atualizar_criado_em(integration_settings.DB_URL, os_id, criado_em)

    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    expected = [
        em_exec_antiga["ordem_servico"]["id"],
        em_exec_recente["ordem_servico"]["id"],
        aguardando_aprov_antiga["ordem_servico"]["id"],
        aguardando_aprov_recente["ordem_servico"]["id"],
        em_diag_antiga["ordem_servico"]["id"],
        em_diag_recente["ordem_servico"]["id"],
        recebida_antiga["ordem_servico"]["id"],
        recebida_recente["ordem_servico"]["id"],
        diag_concluida["ordem_servico"]["id"],
        aprovada["ordem_servico"]["id"],
        aguardando_itens["ordem_servico"]["id"],
        finalizada["ordem_servico"]["id"],
    ]

    assert ids == expected
    assert entregue["ordem_servico"]["id"] not in ids
    assert encerrada["ordem_servico"]["id"] not in ids


async def test_deve_listar_status_filtrado_ordenado_da_mais_antiga_para_mais_nova(
    client: AsyncClient,
    admin_headers: dict,
    integration_settings,
):
    base = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)

    recebida = await criar_os_recebida(client, admin_headers)
    em_diag_antiga = await criar_os_em_diagnostico(client, admin_headers)
    em_diag_meio = await criar_os_em_diagnostico(client, admin_headers)
    em_diag_recente = await criar_os_em_diagnostico(client, admin_headers)

    await _atualizar_criado_em(
        integration_settings.DB_URL,
        recebida["ordem_servico"]["id"],
        base + timedelta(days=10),
    )
    await _atualizar_criado_em(
        integration_settings.DB_URL,
        em_diag_antiga["ordem_servico"]["id"],
        base + timedelta(days=1),
    )
    await _atualizar_criado_em(
        integration_settings.DB_URL,
        em_diag_meio["ordem_servico"]["id"],
        base + timedelta(days=2),
    )
    await _atualizar_criado_em(
        integration_settings.DB_URL,
        em_diag_recente["ordem_servico"]["id"],
        base + timedelta(days=3),
    )

    response = await client.get(
        _BASE,
        params={"status": "EM_DIAGNOSTICO"},
        headers=admin_headers,
    )
    assert response.status_code == 200

    items = extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert ids == [
        em_diag_antiga["ordem_servico"]["id"],
        em_diag_meio["ordem_servico"]["id"],
        em_diag_recente["ordem_servico"]["id"],
    ]
    assert all(i["status"] == "EM_DIAGNOSTICO" for i in items)


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
