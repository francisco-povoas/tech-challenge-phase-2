"""
Testes de integração — Entregar Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/entregar

Permissões:
  Administrador e Atendente podem entregar OS.
  Mecânico NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    consultar_item_estoque,
    criar_os_aprovada_com_item_reservado,
    criar_os_finalizada_com_pagamento,
    criar_os_finalizada_para_pagamento_entrega,
    detalhar_os,
    encontrar_item_os_por_id,
    registrar_pagamento_os,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_UUID_INEXISTENTE = "00000000-0000-0000-0000-000000000099"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_atendente_deve_entregar_os_finalizada_e_paga(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Assert: estado antes da entrega ───────────────────────────────────────
    os_antes = await detalhar_os(client, atendente_headers, os_id)
    assert os_antes["status"] == "FINALIZADA"
    assert os_antes["pagamento_registrado_em"] is not None
    item_antes = encontrar_item_os_por_id(os_antes, item_os_id)
    assert item_antes is not None
    assert item_antes["status"] == "EM_USO"

    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_antes["quantidade_disponivel"]) == 8
    assert int(est_antes["quantidade_reservada"]) == 2

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code == 200, f"entregar falhou: {r.status_code} — {r.text}"

    # ── Assert: OS ENTREGUE ───────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "ENTREGUE"
    assert os_detalhe["pagamento_registrado_em"] is not None
    assert os_detalhe["forma_pagamento"] == "PIX"
    assert Decimal(str(os_detalhe["valor_pago"])) == Decimal("270.00")

    # ── Assert: item CONSUMIDO ────────────────────────────────────────────────
    item_depois = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item_depois is not None
    assert item_depois["status"] == "CONSUMIDO"

    # ── Assert: estoque reservado zerado, disponivel inalterado ───────────────
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == 8
    assert int(est_depois["quantidade_reservada"]) == 0


async def test_admin_deve_entregar_os_finalizada_e_paga(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=admin_headers)
    assert r.status_code == 200, f"admin entregar falhou: {r.status_code} — {r.text}"

    # ── Assert ────────────────────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "ENTREGUE"

    item_depois = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item_depois is not None
    assert item_depois["status"] == "CONSUMIDO"

    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == 8
    assert int(est_depois["quantidade_reservada"]) == 0


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_entregar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=mecanico_headers)
    assert r.status_code == 403, f"esperado 403, obtido {r.status_code}"

    # ── Assert: estado inalterado ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 2


async def test_nao_deve_entregar_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar")
    assert r.status_code in (401, 403), f"esperado 401 ou 403, obtido {r.status_code}"

    # ── Assert: estado inalterado ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"


# ---------------------------------------------------------------------------
# Cenários de negócio — negativos
# ---------------------------------------------------------------------------


async def test_nao_deve_entregar_os_inexistente(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(f"{_BASE}/{_UUID_INEXISTENTE}/entregar", headers=atendente_headers)
    assert r.status_code == 404, f"esperado 404, obtido {r.status_code}"


async def test_nao_deve_entregar_os_fora_de_finalizada(
    client: AsyncClient, admin_headers: dict
):
    # OS APROVADA — não pode ser entregue
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    # ── Assert: status original permanece ────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"


async def test_nao_deve_entregar_os_sem_pagamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_para_pagamento_entrega(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    # ── Assert: estado inalterado ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "FINALIZADA"
    assert os_detalhe["pagamento_registrado_em"] is None

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "EM_USO"

    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 2


async def test_nao_deve_entregar_duas_vezes(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # Primeira entrega — sucesso
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code == 200

    # ── Act: segunda entrega — deve ser recusada ───────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code in (400, 409, 422), f"esperado 400/409/422, obtido {r.status_code}"

    # ── Assert: estado permanece como ENTREGUE ────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "ENTREGUE"

    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None
    assert item["status"] == "CONSUMIDO"

    # ── Assert: estoque não é baixado duas vezes ──────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 0


# ---------------------------------------------------------------------------
# Cenários de validação do estado do estoque
# ---------------------------------------------------------------------------


async def test_entrega_nao_deve_alterar_quantidade_disponivel(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_estoque"]["id"]

    # Estoque antes
    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_antes["quantidade_disponivel"]) == 8
    assert int(est_antes["quantidade_reservada"]) == 2

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code == 200

    # ── Assert: disponivel inalterado, reservado zerado ───────────────────────
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == 8
    assert int(est_depois["quantidade_reservada"]) == 0


async def test_entrega_deve_consumir_item_em_uso(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_finalizada_com_pagamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_os_id = dados["ordem_servico_item"]["id"]

    # Assert: item EM_USO antes da entrega
    os_antes = await detalhar_os(client, atendente_headers, os_id)
    item_antes = encontrar_item_os_por_id(os_antes, item_os_id)
    assert item_antes is not None
    assert item_antes["status"] == "EM_USO"

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/entregar", headers=atendente_headers)
    assert r.status_code == 200

    # ── Assert: item CONSUMIDO ────────────────────────────────────────────────
    os_depois = await detalhar_os(client, atendente_headers, os_id)
    item_depois = encontrar_item_os_por_id(os_depois, item_os_id)
    assert item_depois is not None
    assert item_depois["status"] == "CONSUMIDO"


# ---------------------------------------------------------------------------
# Cenário de item cancelado (via cancelamento durante diagnóstico)
# ---------------------------------------------------------------------------


async def test_entrega_deve_ignorar_item_cancelado(
    client: AsyncClient, admin_headers: dict
):
    """
    Prepara OS com dois itens:
      - item principal: EM_USO → deve virar CONSUMIDO
      - item cancelado durante diagnóstico (DELETE antes de concluir)

    Verifica que a entrega:
      - consome apenas o item EM_USO
      - não tenta baixar estoque do item cancelado
      - OS vira ENTREGUE
    """
    from tests.integration.ordens_servico.factories import (
        criar_atendente,
        criar_cliente,
        criar_item_estoque,
        criar_mecanico,
        criar_ordem_servico,
        criar_servico,
        criar_veiculo,
        gerar_orcamento,
        iniciar_execucao_os,
        registrar_tempo_executado_servico,
        aprovar_orcamento,
        detalhar_os as _detalhar_os,
    )

    _BASE_OS_LOCAL = "/api/v1/ordens-servico"

    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    servico = await criar_servico(client, admin_headers, valor_base="180.00", tempo_medio_minutos=60)

    item_principal = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=10, valor_unitario="45.00"
    )
    item_a_cancelar = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=10, valor_unitario="30.00"
    )

    os_ = await criar_ordem_servico(
        client, atendente["headers"], cliente["id"], veiculo["id"]
    )
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/iniciar-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200

    r = await client.patch(
        f"{_BASE_OS_LOCAL}/{os_id}/diagnostico",
        json={"diagnostico": "Pastilhas e filtro desgastados"},
        headers=mecanico["headers"],
    )
    assert r.status_code == 200

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_servico = r.json()

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/itens",
        json={"item_estoque_id": item_principal["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_principal = r.json()
    assert os_item_principal["status"] == "RESERVADO"

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/itens",
        json={"item_estoque_id": item_a_cancelar["id"], "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_cancelar = r.json()

    # Cancelar o segundo item antes de concluir o diagnóstico
    r = await client.delete(
        f"{_BASE_OS_LOCAL}/{os_id}/itens/{os_item_cancelar['id']}",
        headers=mecanico["headers"],
    )
    assert r.status_code == 204, f"cancelar item falhou: {r.status_code} — {r.text}"

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/concluir-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200

    orcamento = await gerar_orcamento(client, atendente["headers"], os_id)
    await aprovar_orcamento(client, atendente["headers"], os_id)

    await iniciar_execucao_os(client, mecanico["headers"], os_id)

    await registrar_tempo_executado_servico(
        client, mecanico["headers"], os_id, os_servico["id"], 60
    )

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/finalizar", headers=mecanico["headers"])
    assert r.status_code == 200

    # Registrar pagamento
    # total = servico 180 + item 2×45 = 270
    await registrar_pagamento_os(
        client, atendente["headers"], os_id,
        forma_pagamento="PIX", valor_pago="270.00",
    )

    # ── Act: entregar ─────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/entregar", headers=atendente["headers"])
    assert r.status_code == 200, f"entregar falhou: {r.status_code} — {r.text}"

    # ── Assert: OS ENTREGUE ───────────────────────────────────────────────────
    os_detalhe = await _detalhar_os(client, atendente["headers"], os_id)
    assert os_detalhe["status"] == "ENTREGUE"

    # ── Assert: item principal CONSUMIDO ─────────────────────────────────────
    item_p = encontrar_item_os_por_id(os_detalhe, os_item_principal["id"])
    assert item_p is not None
    assert item_p["status"] == "CONSUMIDO"

    # ── Assert: item cancelado permanece CANCELADO ────────────────────────────
    item_c = encontrar_item_os_por_id(os_detalhe, os_item_cancelar["id"])
    if item_c is not None:
        assert item_c["status"] == "CANCELADO"

    # ── Assert: estoque do item cancelado não foi alterado ────────────────────
    est_cancelado = await consultar_item_estoque(client, admin_headers, item_a_cancelar["id"])
    # item_a_cancelar nunca foi para EM_USO, portanto quantidade_reservada = 0
    assert int(est_cancelado["quantidade_reservada"]) == 0

    # ── Assert: estoque do item principal baixou reservado ────────────────────
    est_principal = await consultar_item_estoque(client, admin_headers, item_principal["id"])
    assert int(est_principal["quantidade_disponivel"]) == 8
    assert int(est_principal["quantidade_reservada"]) == 0
