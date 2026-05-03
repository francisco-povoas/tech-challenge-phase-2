"""
Testes de integração — Iniciar Execução da Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/iniciar-execucao

Permissões:
  Administrador e Mecânico podem iniciar execução.
  Atendente NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    consultar_item_estoque,
    criar_os_aprovada_com_item_reservado,
    criar_os_aguardando_itens_com_um_item_a_receber,
    detalhar_os,
    encontrar_item_os_por_id,
    iniciar_execucao_os,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_mecanico_deve_iniciar_execucao_de_os_aprovada(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=mecanico_headers)
    assert r.status_code == 200, f"iniciar-execucao falhou: {r.status_code} — {r.text}"

    # ── Assert: OS ───────────────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    # ── Assert: item virou EM_USO ────────────────────────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None, "Item não encontrado no detalhe da OS"
    assert item["status"] == "EM_USO"

    # ── Assert: estoque não muda ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_admin_deve_iniciar_execucao_de_os_aprovada(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=admin_headers)
    assert r.status_code == 200, f"admin iniciar-execucao falhou: {r.status_code} — {r.text}"

    # ── Assert: OS ───────────────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    # ── Assert: item virou EM_USO ────────────────────────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_iniciar_execucao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=atendente_headers)
    assert r.status_code == 403, f"esperado 403, obtido {r.status_code}"

    # ── Assert: OS permanece APROVADA ─────────────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "RESERVADO"

    # ── Assert: estoque inalterado ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_nao_deve_iniciar_execucao_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act: sem Authorization ────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao")
    assert r.status_code in (401, 403), f"esperado 401 ou 403, obtido {r.status_code}"

    # ── Assert: OS permanece APROVADA ─────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "RESERVADO"


# ---------------------------------------------------------------------------
# Cenários de domínio inválido
# ---------------------------------------------------------------------------


async def test_nao_deve_iniciar_execucao_de_os_aguardando_itens(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=mecanico_headers)
    assert r.status_code == 422, f"esperado 422, obtido {r.status_code} — {r.text}"

    # ── Assert: OS permanece AGUARDANDO_ITENS ─────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "AGUARDANDO_ITENS"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "A_RECEBER"

    # ── Assert: estoque inalterado ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 0
    assert int(est["quantidade_reservada"]) == 0


async def test_nao_deve_iniciar_execucao_duas_vezes(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Primeira vez: sucesso ─────────────────────────────────────────────────
    r1 = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=mecanico_headers)
    assert r1.status_code == 200

    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    # ── Segunda vez: deve falhar ──────────────────────────────────────────────
    r2 = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=mecanico_headers)
    assert r2.status_code == 422, f"esperado 422, obtido {r2.status_code} — {r2.text}"

    # ── Assert: OS permanece EM_EXECUCAO ─────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    # ── Assert: estoque não mudou ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_iniciar_execucao_nao_deve_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]

    # Capturar estoque antes
    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    disp_antes = int(est_antes["quantidade_disponivel"])
    res_antes = int(est_antes["quantidade_reservada"])

    # Iniciar execução
    r = await client.patch(f"{_BASE}/{os_id}/iniciar-execucao", headers=mecanico_headers)
    assert r.status_code == 200

    # Estoque após deve ser idêntico
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == disp_antes
    assert int(est_depois["quantidade_reservada"]) == res_antes
