"""
Testes de integração — Aprovação do Orçamento da Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/orcamento/aprovar

Permissões:
  Administrador e Atendente podem aprovar.
  Mecânico NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_com_orcamento_comunicado_com_item_a_receber,
    criar_os_com_orcamento_comunicado_todos_itens_reservados,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_BASE_ITENS = "/api/v1/itens-estoque"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_atendente_deve_aprovar_orcamento_com_todos_itens_reservados(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_com_saldo"]["id"]

    # ── Act: aprovar ──────────────────────────────────────────────────────────
    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r.status_code == 200, f"aprovar falhou: {r.status_code} — {r.text}"

    # ── Assert: orçamento ────────────────────────────────────────────────────
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.status_code == 200
    orc = r_orc.json()
    assert orc["status"] == "APROVADO"
    assert orc["respondido_em"] is not None
    assert orc["motivo_recusa"] is None

    # ── Assert: OS ───────────────────────────────────────────────────────────
    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.status_code == 200
    assert r_os.json()["status"] == "APROVADA"

    # ── Assert: estoque inalterado ────────────────────────────────────────────
    r_est = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    assert r_est.status_code == 200
    est = r_est.json()
    assert int(est["quantidade_disponivel"]) == 8
    assert int(est["quantidade_reservada"]) == 2


async def test_admin_deve_aprovar_orcamento_com_todos_itens_reservados(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=admin_headers)
    assert r.status_code == 200, f"aprovar com admin falhou: {r.status_code} — {r.text}"

    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)
    assert r_orc.json()["status"] == "APROVADO"

    r_os = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    assert r_os.json()["status"] == "APROVADA"


async def test_atendente_deve_aprovar_orcamento_com_item_a_receber_e_os_fica_aguardando_itens(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_com_item_a_receber(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r.status_code == 200, f"aprovar falhou: {r.status_code} — {r.text}"

    # Orçamento deve ser APROVADO
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.status_code == 200
    orc = r_orc.json()
    assert orc["status"] == "APROVADO"
    assert orc["respondido_em"] is not None

    # OS deve ir para AGUARDANDO_ITENS (há item A_RECEBER)
    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.status_code == 200
    assert r_os.json()["status"] == "AGUARDANDO_ITENS"

    # Item A_RECEBER continua A_RECEBER
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    itens = r_detalhe.json().get("itens", [])
    item_arec = next(
        (i for i in itens if i["item_estoque_id"] == dados["item_sem_saldo"]["id"]),
        None,
    )
    assert item_arec is not None, "Item A_RECEBER não encontrado no detalhe da OS"
    assert item_arec["status"] == "A_RECEBER"


async def test_aprovacao_nao_deve_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    item_estoque_id = dados["item_com_saldo"]["id"]

    # Capturar estoque antes
    r_antes = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    assert r_antes.status_code == 200
    disp_antes = int(r_antes.json()["quantidade_disponivel"])
    res_antes = int(r_antes.json()["quantidade_reservada"])

    # Aprovar
    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r.status_code == 200

    # Estoque após aprovação deve ser idêntico
    r_depois = await client.get(f"{_BASE_ITENS}/{item_estoque_id}", headers=admin_headers)
    assert r_depois.status_code == 200
    assert int(r_depois.json()["quantidade_disponivel"]) == disp_antes
    assert int(r_depois.json()["quantidade_reservada"]) == res_antes


# ---------------------------------------------------------------------------
# Idempotência / fluxo inválido
# ---------------------------------------------------------------------------


async def test_nao_deve_aprovar_orcamento_ja_aprovado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Primeira aprovação
    r1 = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r1.status_code == 200

    # Segunda tentativa deve falhar com erro de domínio
    r2 = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r2.status_code in (400, 409, 422), (
        f"Segunda aprovação deveria falhar, mas retornou {r2.status_code}"
    )

    # Estado permanece APROVADO
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.json()["status"] == "APROVADO"


async def test_nao_deve_aprovar_orcamento_recusado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    # Recusar primeiro
    r_rec = await client.patch(f"{_BASE}/{os_id}/orcamento/recusar", headers=atendente_headers)
    assert r_rec.status_code == 200

    # Tentar aprovar orçamento já recusado
    r_apr = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    assert r_apr.status_code in (400, 409, 422), (
        f"Aprovação de orçamento recusado deveria falhar, mas retornou {r_apr.status_code}"
    )

    # Estado permanece RECUSADO e OS ENCERRADA
    r_orc = await client.get(f"{_BASE}/{os_id}/orcamento", headers=atendente_headers)
    assert r_orc.json()["status"] == "RECUSADO"

    r_os = await client.get(f"{_BASE}/{os_id}", headers=atendente_headers)
    assert r_os.json()["status"] == "ENCERRADA"
