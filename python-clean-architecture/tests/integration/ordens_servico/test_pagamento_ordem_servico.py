"""
Testes de integração — Registrar Pagamento da Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/registrar-pagamento

Permissões:
  Administrador e Atendente podem registrar pagamento.
  Mecânico NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    consultar_item_estoque,
    criar_os_aprovada_com_item_reservado,
    criar_os_finalizada_para_pagamento_entrega,
    detalhar_os,
    encontrar_item_os_por_id,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_UUID_INEXISTENTE = "00000000-0000-0000-0000-000000000099"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_atendente_deve_registrar_pagamento_de_os_finalizada(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00", "observacao": "Pagamento recebido via PIX."},
        headers=atendente_headers,
    )
    assert r.status_code == 200, f"registrar-pagamento falhou: {r.status_code} — {r.text}"

    # ── Assert: campos de pagamento preenchidos ───────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"
    assert os_detalhe["pagamento_registrado_em"] is not None
    assert os_detalhe["forma_pagamento"] == "PIX"
    from decimal import Decimal
    assert Decimal(str(os_detalhe["valor_pago"])) == Decimal("270.00")
    assert os_detalhe["pagamento_observacao"] == "Pagamento recebido via PIX."

    # ── Assert: item permanece EM_USO ─────────────────────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    # ── Assert: estoque inalterado ────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_admin_deve_registrar_pagamento_de_os_finalizada(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "DINHEIRO", "valor_pago": "270.00"},
        headers=admin_headers,
    )
    assert r.status_code == 200, f"admin registrar-pagamento falhou: {r.status_code} — {r.text}"

    # ── Assert ────────────────────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"
    assert os_detalhe["pagamento_registrado_em"] is not None
    assert os_detalhe["forma_pagamento"] == "DINHEIRO"


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_registrar_pagamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00"},
        headers=mecanico_headers,
    )
    assert r.status_code == 403, f"esperado 403, obtido {r.status_code}"

    # ── Assert: estado inalterado ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None
    assert os_detalhe["status"] == "FINALIZADA"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 2


async def test_nao_deve_registrar_pagamento_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00"},
    )
    assert r.status_code in (401, 403), f"esperado 401 ou 403, obtido {r.status_code}"

    # ── Assert: pagamento continua null ───────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None


# ---------------------------------------------------------------------------
# Cenários de negócio — negativos
# ---------------------------------------------------------------------------


async def test_nao_deve_registrar_pagamento_de_os_inexistente(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(
        f"{_BASE}/{_UUID_INEXISTENTE}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00"},
        headers=atendente_headers,
    )
    assert r.status_code == 404, f"esperado 404, obtido {r.status_code}"


async def test_nao_deve_registrar_pagamento_de_os_fora_de_finalizada(
    client: AsyncClient, admin_headers: dict
):
    # OS APROVADA — não está finalizada ainda
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "450.00"},
        headers=atendente_headers,
    )
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    # ── Assert: pagamento continua null ───────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None
    assert os_detalhe["status"] == "APROVADA"


async def test_nao_deve_registrar_pagamento_duplicado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Primeiro pagamento — sucesso
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00", "observacao": "Primeiro pagamento."},
        headers=atendente_headers,
    )
    assert r.status_code == 200

    # ── Act: segundo pagamento — deve ser recusado ─────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "DINHEIRO", "valor_pago": "300.00"},
        headers=atendente_headers,
    )
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    # ── Assert: pagamento original permanece ──────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["forma_pagamento"] == "PIX"
    assert os_detalhe["pagamento_observacao"] == "Primeiro pagamento."
    assert os_detalhe["status"] == "FINALIZADA"


async def test_nao_deve_registrar_pagamento_com_valor_zero(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "0.00", "observacao": "Valor zero."},
        headers=atendente_headers,
    )
    assert r.status_code in (400, 422), f"esperado 400 ou 422, obtido {r.status_code}"

    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None


async def test_nao_deve_registrar_pagamento_com_valor_negativo(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "-1.00", "observacao": "Valor negativo."},
        headers=atendente_headers,
    )
    assert r.status_code in (400, 422), f"esperado 400 ou 422, obtido {r.status_code}"

    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None


async def test_nao_deve_registrar_pagamento_menor_que_total_do_orcamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    # total_geral esperado = 270.00 (serviço 180 + item 2×45)

    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "269.99", "observacao": "Valor insuficiente."},
        headers=atendente_headers,
    )
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["pagamento_registrado_em"] is None
    assert os_detalhe["status"] == "FINALIZADA"


async def test_registrar_pagamento_nao_deve_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]

    # Estoque antes
    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    disp_antes = int(est_antes["quantidade_disponivel"])
    res_antes = int(est_antes["quantidade_reservada"])

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/registrar-pagamento",
        json={"forma_pagamento": "PIX", "valor_pago": "270.00"},
        headers=atendente_headers,
    )
    assert r.status_code == 200

    # Estoque depois
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == disp_antes
    assert int(est_depois["quantidade_reservada"]) == res_antes
