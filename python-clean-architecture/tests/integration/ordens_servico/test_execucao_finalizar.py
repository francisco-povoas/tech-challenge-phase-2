"""
Testes de integração — Finalizar Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/finalizar

Permissões:
  Administrador e Mecânico podem finalizar.
  Atendente NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    consultar_item_estoque,
    criar_os_em_execucao_com_dois_servicos_um_sem_tempo,
    criar_os_em_execucao_com_tempo_registrado,
    detalhar_os,
    encontrar_item_os_por_id,
    encontrar_servico_os_por_id,
    registrar_tempo_executado_servico,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_mecanico_deve_finalizar_os_em_execucao_com_todos_servicos_com_tempo(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    tempo = dados["tempo_executado_minutos"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 200, f"finalizar falhou: {r.status_code} — {r.text}"

    # ── Assert: OS FINALIZADA ─────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"

    # ── Assert: serviço mantém tempo ─────────────────────────────────────────
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert int(servico["tempo_executado_minutos"]) == tempo

    # ── Assert: item permanece EM_USO, não CONSUMIDO ──────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    # ── Assert: estoque inalterado ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_admin_deve_finalizar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=admin_headers)
    assert r.status_code == 200, f"admin finalizar falhou: {r.status_code} — {r.text}"

    # ── Assert: OS FINALIZADA ─────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_finalizar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    mecanico_headers = dados["mecanico_headers"]
    item_os_id = dados["ordem_servico_item"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    tempo = dados["tempo_executado_minutos"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=atendente_headers)
    assert r.status_code == 403, f"esperado 403, obtido {r.status_code}"

    # ── Assert: OS permanece EM_EXECUCAO ─────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert int(servico["tempo_executado_minutos"]) == tempo

    # ── Assert: estoque inalterado ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_nao_deve_finalizar_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act: sem Authorization ────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/finalizar")
    assert r.status_code in (401, 403), f"esperado 401 ou 403, obtido {r.status_code}"

    # ── Assert: OS permanece EM_EXECUCAO ─────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"


# ---------------------------------------------------------------------------
# Cenários de domínio inválido
# ---------------------------------------------------------------------------


async def test_nao_deve_finalizar_os_com_servico_ativo_sem_tempo(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_dois_servicos_um_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    oss_1_id = dados["ordem_servico_servico_1"]["id"]
    oss_2_id = dados["ordem_servico_servico_2"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act: tentar finalizar com serviço 2 sem tempo ─────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 422, f"esperado 422, obtido {r.status_code} — {r.text}"

    # ── Assert: OS permanece EM_EXECUCAO ─────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    s1 = encontrar_servico_os_por_id(os_detalhe, oss_1_id)
    assert s1 is not None
    assert int(s1["tempo_executado_minutos"]) == 50

    s2 = encontrar_servico_os_por_id(os_detalhe, oss_2_id)
    assert s2 is not None
    assert s2["tempo_executado_minutos"] is None

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    # ── Act: registrar tempo no serviço 2 e finalizar ─────────────────────────
    await registrar_tempo_executado_servico(
        client, mecanico_headers, os_id, oss_2_id, 40
    )

    r2 = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r2.status_code == 200, f"finalizar após registrar tempo falhou: {r2.status_code} — {r2.text}"

    os_detalhe_final = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe_final["status"] == "FINALIZADA"


async def test_nao_deve_finalizar_duas_vezes(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Primeira vez: sucesso ─────────────────────────────────────────────────
    r1 = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r1.status_code == 200

    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"

    # ── Segunda vez: deve falhar ──────────────────────────────────────────────
    r2 = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r2.status_code == 422, f"esperado 422, obtido {r2.status_code} — {r2.text}"

    # ── Assert: OS permanece FINALIZADA ──────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"


# ---------------------------------------------------------------------------
# Garantias de não-consumo de itens e não-alteração de estoque
# ---------------------------------------------------------------------------


async def test_finalizar_nao_deve_consumir_itens(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # Finalizar
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 200

    # ── Assert: item permanece EM_USO ─────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO", f"item deveria ser EM_USO, mas é {item['status']}"


async def test_finalizar_nao_deve_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_tempo_registrado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]

    # Capturar estoque antes
    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    disp_antes = int(est_antes["quantidade_disponivel"])
    res_antes = int(est_antes["quantidade_reservada"])

    # Finalizar
    r = await client.patch(f"{_BASE}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 200

    # Estoque após deve ser idêntico
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == disp_antes
    assert int(est_depois["quantidade_reservada"]) == res_antes
