"""
Testes de integração — Confirmação de recebimento de item A_RECEBER da OS.

Rota testada:
  PATCH /api/v1/ordens-servico/{os_id}/itens/{item_id}/confirmar-recebimento

Permissões:
  Administrador e Atendente podem confirmar recebimento.
  Mecânico NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    consultar_item_estoque,
    criar_os_aguardando_itens_com_dois_itens_a_receber,
    criar_os_aguardando_itens_com_item_a_receber_e_item_cancelado,
    criar_os_aguardando_itens_com_um_item_a_receber,
    criar_os_diagnostico_concluido_com_item_a_receber_sem_aprovacao,
    detalhar_os,
    encontrar_item_os_por_id,
    encontrar_item_os_por_item_estoque_id,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_BASE_ITENS = "/api/v1/itens-estoque"


def _url_confirmar(os_id: str, item_os_id: str) -> str:
    return f"{_BASE}/{os_id}/itens/{item_os_id}/confirmar-recebimento"


# ---------------------------------------------------------------------------
# Cenários de sucesso — Atendente
# ---------------------------------------------------------------------------


async def test_atendente_deve_confirmar_recebimento_do_unico_item_a_receber_e_aprovar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code == 200, f"confirmar-recebimento falhou: {r.status_code} — {r.text}"

    # ── Assert: OS virou APROVADA ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    # ── Assert: item virou RESERVADO ──────────────────────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item is not None, "Item não encontrado no detalhe da OS"
    assert item["status"] == "RESERVADO"

    # ── Assert: nenhum item ativo A_RECEBER ──────────────────────────────────
    itens_ativos_a_receber = [
        i for i in os_detalhe["itens"]
        if i["status"] == "A_RECEBER"
    ]
    assert itens_ativos_a_receber == []

    # ── Assert: estoque → disponivel=0, reservado=1 ──────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 0
    assert int(est["quantidade_reservada"]) == 1


async def test_atendente_deve_confirmar_primeiro_item_e_manter_os_aguardando_itens(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_dois_itens_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_1_os_id = dados["ordem_servico_item_1"]["id"]
    item_2_os_id = dados["ordem_servico_item_2"]["id"]
    item_estoque_1_id = dados["item_estoque_1"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act: confirmar apenas o primeiro item ────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_1_os_id), headers=atendente_headers)
    assert r.status_code == 200, f"confirmar-recebimento falhou: {r.status_code} — {r.text}"

    # ── Assert: OS permanece AGUARDANDO_ITENS ────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "AGUARDANDO_ITENS"

    # ── Assert: item 1 RESERVADO, item 2 A_RECEBER ──────────────────────────
    item_1 = encontrar_item_os_por_id(os_detalhe, item_1_os_id)
    item_2 = encontrar_item_os_por_id(os_detalhe, item_2_os_id)
    assert item_1 is not None
    assert item_2 is not None
    assert item_1["status"] == "RESERVADO"
    assert item_2["status"] == "A_RECEBER"

    # ── Assert: estoque item 1 → disponivel=0, reservado=1 ──────────────────
    est_1 = await consultar_item_estoque(client, admin_headers, item_estoque_1_id)
    assert int(est_1["quantidade_disponivel"]) == 0
    assert int(est_1["quantidade_reservada"]) == 1


async def test_atendente_deve_confirmar_ultimo_item_e_aprovar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_dois_itens_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_1_os_id = dados["ordem_servico_item_1"]["id"]
    item_2_os_id = dados["ordem_servico_item_2"]["id"]
    item_estoque_1_id = dados["item_estoque_1"]["id"]
    item_estoque_2_id = dados["item_estoque_2"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act: confirmar os dois itens ─────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_1_os_id), headers=atendente_headers)
    assert r.status_code == 200

    r = await client.patch(_url_confirmar(os_id, item_2_os_id), headers=atendente_headers)
    assert r.status_code == 200, f"confirmar segundo item falhou: {r.status_code} — {r.text}"

    # ── Assert: OS virou APROVADA ─────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    # ── Assert: ambos os itens RESERVADO ─────────────────────────────────────
    item_1 = encontrar_item_os_por_id(os_detalhe, item_1_os_id)
    item_2 = encontrar_item_os_por_id(os_detalhe, item_2_os_id)
    assert item_1["status"] == "RESERVADO"
    assert item_2["status"] == "RESERVADO"

    # ── Assert: nenhum item ativo A_RECEBER ──────────────────────────────────
    assert all(i["status"] != "A_RECEBER" for i in os_detalhe["itens"])

    # ── Assert: estoque item 1 e item 2 → disponivel=0, reservado=1 ─────────
    est_1 = await consultar_item_estoque(client, admin_headers, item_estoque_1_id)
    assert int(est_1["quantidade_disponivel"]) == 0
    assert int(est_1["quantidade_reservada"]) == 1

    est_2 = await consultar_item_estoque(client, admin_headers, item_estoque_2_id)
    assert int(est_2["quantidade_disponivel"]) == 0
    assert int(est_2["quantidade_reservada"]) == 1


# ---------------------------------------------------------------------------
# Cenários de sucesso — Administrador
# ---------------------------------------------------------------------------


async def test_admin_deve_confirmar_recebimento_de_item_a_receber(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]

    # ── Act: confirmar com token admin ───────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=admin_headers)
    assert r.status_code == 200, f"admin confirmar-recebimento falhou: {r.status_code} — {r.text}"

    # ── Assert: OS APROVADA ───────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    # ── Assert: item RESERVADO ────────────────────────────────────────────────
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item["status"] == "RESERVADO"

    # ── Assert: estoque atualizado ────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 1


# ---------------------------------------------------------------------------
# Cenário: quantidade_disponivel não muda
# ---------------------------------------------------------------------------


async def test_confirmar_recebimento_nao_deve_alterar_quantidade_disponivel(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Capturar estoque antes ───────────────────────────────────────────────
    est_antes = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    disp_antes = int(est_antes["quantidade_disponivel"])
    res_antes = int(est_antes["quantidade_reservada"])
    assert disp_antes == 0
    assert res_antes == 0

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code == 200

    # ── Assert: disponivel inalterado, reservado aumentou 1 ─────────────────
    est_depois = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est_depois["quantidade_disponivel"]) == disp_antes
    assert int(est_depois["quantidade_reservada"]) == res_antes + 1


async def test_confirmar_recebimento_com_quantidade_maior_que_1(
    client: AsyncClient, admin_headers: dict
):
    """Valida que quantidade_reservada aumenta pela quantidade do item (não sempre 1)."""
    from tests.integration.ordens_servico.factories import (
        criar_atendente,
        criar_mecanico,
        criar_cliente,
        criar_veiculo,
        criar_servico,
        criar_item_estoque,
        criar_ordem_servico,
        gerar_orcamento,
    )

    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    servico = await criar_servico(client, admin_headers, valor_base="150.00")
    item_estoque = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=0,
        valor_unitario="80.00",
    )

    os_ = await criar_ordem_servico(client, atendente["headers"], cliente["id"], veiculo["id"])
    os_id = os_["id"]

    await client.patch(f"{_BASE}/{os_id}/iniciar-diagnostico", headers=mecanico["headers"])
    await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas velas"},
        headers=mecanico["headers"],
    )
    await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"]},
        headers=mecanico["headers"],
    )

    # Quantidade 2 → A_RECEBER
    r = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item_estoque["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item = r.json()
    assert os_item["status"] == "A_RECEBER"
    assert int(os_item["quantidade"]) == 2

    await client.patch(f"{_BASE}/{os_id}/concluir-diagnostico", headers=mecanico["headers"])
    await gerar_orcamento(client, atendente["headers"], os_id)
    await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente["headers"])

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, os_item["id"]), headers=atendente["headers"])
    assert r.status_code == 200

    # ── Assert: reservado aumentou 2, disponivel continua 0 ─────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque["id"])
    assert int(est["quantidade_disponivel"]) == 0
    assert int(est["quantidade_reservada"]) == 2

    # ── Assert: item RESERVADO, OS APROVADA ───────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente["headers"], os_id)
    assert os_detalhe["status"] == "APROVADA"
    item = encontrar_item_os_por_id(os_detalhe, os_item["id"])
    assert item["status"] == "RESERVADO"


# ---------------------------------------------------------------------------
# Cenário: item CANCELADO não impede OS de virar APROVADA
# ---------------------------------------------------------------------------


async def test_item_cancelado_nao_deve_impedir_os_de_virar_aprovada(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_item_a_receber_e_item_cancelado(
        client, admin_headers
    )
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item_principal"]["id"]
    item_estoque_id = dados["item_estoque_principal"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code == 200, f"confirmar-recebimento falhou: {r.status_code} — {r.text}"

    # ── Assert: OS virou APROVADA (item cancelado não conta como pendente) ───
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    # ── Assert: item principal RESERVADO ─────────────────────────────────────
    item_principal = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item_principal["status"] == "RESERVADO"

    # ── Assert: estoque atualizado ────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 1


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_nao_deve_confirmar_recebimento_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    # ── Act: sem Authorization ────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id))
    assert r.status_code in (401, 403), f"esperado 401/403, recebido {r.status_code}"

    # ── Assert: OS permanece AGUARDANDO_ITENS ────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "AGUARDANDO_ITENS"
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item["status"] == "A_RECEBER"

    # ── Assert: estoque não mudou ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_disponivel"]) == 0
    assert int(est["quantidade_reservada"]) == 0


async def test_mecanico_nao_deve_confirmar_recebimento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act: Mecânico tenta confirmar ────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=mecanico_headers)
    assert r.status_code == 403, f"esperado 403, recebido {r.status_code}"

    # ── Assert: OS permanece AGUARDANDO_ITENS ────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "AGUARDANDO_ITENS"
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item["status"] == "A_RECEBER"

    # ── Assert: estoque não mudou ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 0


# ---------------------------------------------------------------------------
# Cenários de erro de domínio
# ---------------------------------------------------------------------------


async def test_nao_deve_confirmar_recebimento_de_item_ja_reservado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Confirmar recebimento uma vez (sucesso)
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code == 200

    # Verificar estado intermediário
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    # ── Act: tentar confirmar novamente (item já está RESERVADO) ──────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code in (400, 409, 422), f"esperado 4xx, recebido {r.status_code}"

    # ── Assert: OS permanece APROVADA ────────────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"
    item = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item["status"] == "RESERVADO"

    # ── Assert: estoque não duplicou reserva ──────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 1


async def test_nao_deve_confirmar_recebimento_se_os_nao_estiver_aguardando_itens(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_com_item_a_receber_sem_aprovacao(
        client, admin_headers
    )
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Garantir pré-condição
    assert dados["ordem_servico"]["status"] == "DIAGNOSTICO_CONCLUIDO"

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, item_os_id), headers=atendente_headers)
    assert r.status_code in (400, 409, 422), f"esperado 4xx, recebido {r.status_code}"

    # ── Assert: OS permanece DIAGNOSTICO_CONCLUIDO ────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "DIAGNOSTICO_CONCLUIDO"

    # ── Assert: estoque não mudou ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 0


async def test_nao_deve_confirmar_recebimento_de_item_inexistente(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item_os_id = dados["ordem_servico_item"]["id"]
    item_estoque_id = dados["item_estoque"]["id"]
    atendente_headers = dados["atendente_headers"]

    uuid_inexistente = "00000000-0000-0000-0000-000000000099"

    # ── Act: item_id inexistente ──────────────────────────────────────────────
    r = await client.patch(_url_confirmar(os_id, uuid_inexistente), headers=atendente_headers)
    assert r.status_code == 404, f"esperado 404, recebido {r.status_code}"

    # ── Assert: OS permanece AGUARDANDO_ITENS ────────────────────────────────
    os_detalhe = await detalhar_os(client, atendente_headers, os_id)
    assert os_detalhe["status"] == "AGUARDANDO_ITENS"
    item_real = encontrar_item_os_por_id(os_detalhe, item_os_id)
    assert item_real["status"] == "A_RECEBER"

    # ── Assert: estoque não mudou ─────────────────────────────────────────────
    est = await consultar_item_estoque(client, admin_headers, item_estoque_id)
    assert int(est["quantidade_reservada"]) == 0


async def test_nao_deve_confirmar_recebimento_de_item_de_outra_os(
    client: AsyncClient, admin_headers: dict
):
    # Preparar duas OS independentes, cada uma com item A_RECEBER
    dados_os_a = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)
    dados_os_b = await criar_os_aguardando_itens_com_um_item_a_receber(client, admin_headers)

    os_a_id = dados_os_a["ordem_servico"]["id"]
    os_b_id = dados_os_b["ordem_servico"]["id"]
    item_os_a_id = dados_os_a["ordem_servico_item"]["id"]
    item_os_b_id = dados_os_b["ordem_servico_item"]["id"]
    item_estoque_a_id = dados_os_a["item_estoque"]["id"]
    item_estoque_b_id = dados_os_b["item_estoque"]["id"]
    atendente_headers = dados_os_a["atendente_headers"]

    # ── Act: usar os_a_id mas item da OS B ────────────────────────────────────
    r = await client.patch(_url_confirmar(os_a_id, item_os_b_id), headers=atendente_headers)
    assert r.status_code == 404, f"esperado 404, recebido {r.status_code}"

    # ── Assert: OS A permanece AGUARDANDO_ITENS ──────────────────────────────
    os_a_detalhe = await detalhar_os(client, atendente_headers, os_a_id)
    assert os_a_detalhe["status"] == "AGUARDANDO_ITENS"
    item_a = encontrar_item_os_por_id(os_a_detalhe, item_os_a_id)
    assert item_a["status"] == "A_RECEBER"

    # ── Assert: OS B permanece AGUARDANDO_ITENS ──────────────────────────────
    os_b_detalhe = await detalhar_os(client, dados_os_b["atendente_headers"], os_b_id)
    assert os_b_detalhe["status"] == "AGUARDANDO_ITENS"
    item_b = encontrar_item_os_por_id(os_b_detalhe, item_os_b_id)
    assert item_b["status"] == "A_RECEBER"

    # ── Assert: estoques não mudaram ──────────────────────────────────────────
    est_a = await consultar_item_estoque(client, admin_headers, item_estoque_a_id)
    est_b = await consultar_item_estoque(client, admin_headers, item_estoque_b_id)
    assert int(est_a["quantidade_reservada"]) == 0
    assert int(est_b["quantidade_reservada"]) == 0


# ---------------------------------------------------------------------------
# Cenário opcional: OS inexistente
# ---------------------------------------------------------------------------


async def test_nao_deve_confirmar_recebimento_com_os_inexistente(
    client: AsyncClient, admin_headers: dict
):
    uuid_os_inexistente = "00000000-0000-0000-0000-000000000088"
    uuid_item_qualquer = "00000000-0000-0000-0000-000000000077"

    r = await client.patch(
        _url_confirmar(uuid_os_inexistente, uuid_item_qualquer),
        headers=admin_headers,
    )
    assert r.status_code == 404, f"esperado 404, recebido {r.status_code}"
