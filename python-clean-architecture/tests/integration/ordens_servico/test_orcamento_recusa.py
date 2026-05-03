"""
Testes de integração — Recusa do Orçamento da Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/orcamento/recusar

Permissões:
  Administrador e Atendente podem recusar.
  Mecânico NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_com_orcamento_comunicado_com_item_a_receber,
    criar_os_com_orcamento_comunicado_misto,
    criar_os_com_orcamento_comunicado_todos_itens_reservados,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_BASE_ITENS = "/api/v1/itens-estoque"


# ---------------------------------------------------------------------------
# Cenários de sucesso — recusa básica
# ---------------------------------------------------------------------------


async def test_atendente_deve_recusar_orcamento_e_encerrar_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_misto(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_com_saldo = dados["item_com_saldo"]

    # ── Act: recusar ──────────────────────────────────────────────────────────
    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={"motivo_recusa": "Cliente nao aprovou o valor do orcamento."},
        headers=atendente_headers,
    )
    assert r.status_code == 200, f"recusar falhou: {r.status_code} — {r.text}"

    # ── Assert: orçamento ────────────────────────────────────────────────────
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.status_code == 200
    orc = r_orc.json()
    assert orc["status"] == "RECUSADO"
    assert orc["respondido_em"] is not None
    assert orc["motivo_recusa"] == "Cliente nao aprovou o valor do orcamento."

    # ── Assert: OS ENCERRADA ─────────────────────────────────────────────────
    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.status_code == 200
    detalhe = r_os.json()
    assert detalhe["status"] == "ENCERRADA"

    # ── Assert: itens cancelados ──────────────────────────────────────────────
    itens = detalhe.get("itens", [])
    for item in itens:
        assert item["status"] == "CANCELADO", (
            f"Item {item['id']} esperava CANCELADO, encontrou {item['status']}"
        )

    # ── Assert: serviço não cancelado ─────────────────────────────────────────
    servicos = detalhe.get("servicos", [])
    assert len(servicos) >= 1
    for srv in servicos:
        assert srv.get("cancelado") is False, (
            f"Serviço {srv['id']} não deveria estar cancelado após recusa"
        )

    # ── Assert: estoque do item reservado liberado ────────────────────────────
    r_est = await client.get(f"{_BASE_ITENS}/{item_com_saldo['id']}", headers=admin_headers)
    assert r_est.status_code == 200
    est = r_est.json()
    assert int(est["quantidade_disponivel"]) == 10  # 8 + 2
    assert int(est["quantidade_reservada"]) == 0    # 2 - 2


async def test_admin_deve_recusar_orcamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={"motivo_recusa": "Recusa pelo admin."},
        headers=admin_headers,
    )
    assert r.status_code == 200, f"recusar com admin falhou: {r.status_code} — {r.text}"

    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)
    assert r_orc.json()["status"] == "RECUSADO"

    r_os = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    assert r_os.json()["status"] == "ENCERRADA"


async def test_recusa_sem_motivo_deve_funcionar(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Body vazio — motivo_recusa é opcional
    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r.status_code == 200, f"recusar sem motivo falhou: {r.status_code} — {r.text}"

    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    orc = r_orc.json()
    assert orc["status"] == "RECUSADO"
    assert orc["motivo_recusa"] is None

    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.json()["status"] == "ENCERRADA"


# ---------------------------------------------------------------------------
# Liberação de estoque
# ---------------------------------------------------------------------------


async def test_recusa_deve_cancelar_item_reservado_e_liberar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_com_saldo"]["id"]
    os_item_id = dados["ordem_servico_item_reservado"]["id"]

    # Confirmar estado antes
    r_est_antes = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    assert int(r_est_antes.json()["quantidade_disponivel"]) == 8
    assert int(r_est_antes.json()["quantidade_reservada"]) == 2

    # Recusar
    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r.status_code == 200

    # Item da OS deve ser CANCELADO
    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    itens = r_os.json().get("itens", [])
    item = next((i for i in itens if i["id"] == os_item_id), None)
    assert item is not None, "Item não encontrado no detalhe da OS"
    assert item["status"] == "CANCELADO"

    # Estoque liberado
    r_est_depois = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    est = r_est_depois.json()
    assert int(est["quantidade_disponivel"]) == 10  # 8 + 2
    assert int(est["quantidade_reservada"]) == 0    # 2 - 2


async def test_recusa_deve_cancelar_item_a_receber_sem_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_com_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_sem_saldo"]["id"]
    os_item_id = dados["ordem_servico_item_a_receber"]["id"]

    # Confirmar estoque antes (disponível=0, reservado=0)
    r_est_antes = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    assert int(r_est_antes.json()["quantidade_disponivel"]) == 0
    assert int(r_est_antes.json()["quantidade_reservada"]) == 0

    # Recusar
    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r.status_code == 200

    # Item da OS deve ser CANCELADO
    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    itens = r_os.json().get("itens", [])
    item = next((i for i in itens if i["id"] == os_item_id), None)
    assert item is not None, "Item A_RECEBER não encontrado no detalhe da OS"
    assert item["status"] == "CANCELADO"

    # Estoque permanece intocado
    r_est_depois = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    est = r_est_depois.json()
    assert int(est["quantidade_disponivel"]) == 0
    assert int(est["quantidade_reservada"]) == 0


# ---------------------------------------------------------------------------
# Serviços não cancelados
# ---------------------------------------------------------------------------


async def test_recusa_nao_deve_cancelar_servicos_da_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    servico_id = dados["servico"]["id"]

    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r.status_code == 200

    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    detalhe = r_os.json()
    servicos = detalhe.get("servicos", [])

    # Deve haver pelo menos o serviço criado
    assert len(servicos) >= 1

    # O serviço criado no cenário deve estar presente e não cancelado
    srv = next((s for s in servicos if s["servico_id"] == servico_id), None)
    assert srv is not None, "Serviço não encontrado no detalhe da OS após recusa"
    assert srv.get("cancelado") is False, "Serviço não deve ser cancelado na recusa do orçamento"


# ---------------------------------------------------------------------------
# Idempotência / fluxo inválido
# ---------------------------------------------------------------------------


async def test_nao_deve_recusar_orcamento_ja_recusado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Primeira recusa
    r1 = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r1.status_code == 200

    # Segunda tentativa deve falhar
    r2 = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r2.status_code in (400, 409, 422), (
        f"Segunda recusa deveria falhar, mas retornou {r2.status_code}"
    )

    # Estado permanece RECUSADO e ENCERRADA
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.json()["status"] == "RECUSADO"

    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.json()["status"] == "ENCERRADA"


async def test_nao_deve_recusar_orcamento_aprovado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Aprovar primeiro
    r_apr = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r_apr.status_code == 200

    # Tentar recusar orçamento já aprovado
    r_rec = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={"motivo_recusa": "Tentativa inválida"},
        headers=atendente_headers,
    )
    assert r_rec.status_code in (400, 409, 422), (
        f"Recusa de orçamento aprovado deveria falhar, mas retornou {r_rec.status_code}"
    )

    # Estado permanece APROVADO
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.json()["status"] == "APROVADO"
