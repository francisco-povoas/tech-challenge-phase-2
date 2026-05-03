"""
Testes de integração — Registrar Tempo Executado em Serviço da OS.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/servicos/{os_servico_id}/tempo-executado

Permissões:
  Administrador e Mecânico podem registrar tempo.
  Atendente NÃO pode (403).
  Sem token → 401.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_aprovada_com_item_reservado,
    criar_os_em_execucao_com_um_servico_sem_tempo,
    detalhar_os,
    encontrar_servico_os_por_id,
    iniciar_execucao_os,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_UUID_INEXISTENTE = "00000000-0000-0000-0000-000000000099"


def _url_tempo(os_id: str, os_servico_id: str) -> str:
    return f"{_BASE}/{os_id}/servicos/{os_servico_id}/tempo-executado"


# ---------------------------------------------------------------------------
# Cenários de sucesso
# ---------------------------------------------------------------------------


async def test_mecanico_deve_registrar_tempo_executado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 75},
        headers=mecanico_headers,
    )
    assert r.status_code == 200, f"registrar tempo falhou: {r.status_code} — {r.text}"

    # ── Assert: GET OS ────────────────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "EM_EXECUCAO"

    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None, "Serviço não encontrado no detalhe da OS"
    assert int(servico["tempo_executado_minutos"]) == 75


async def test_admin_deve_registrar_tempo_executado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]

    # ── Act: com admin ────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 75},
        headers=admin_headers,
    )
    assert r.status_code == 200, f"admin registrar tempo falhou: {r.status_code} — {r.text}"

    os_detalhe = await detalhar_os(client, admin_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert int(servico["tempo_executado_minutos"]) == 75


async def test_deve_sobrescrever_tempo_executado_enquanto_os_em_execucao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # Registrar 60 min
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 60},
        headers=mecanico_headers,
    )
    assert r.status_code == 200

    # Sobrescrever com 90 min
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 90},
        headers=mecanico_headers,
    )
    assert r.status_code == 200

    # ── Assert: tempo final = 90 ──────────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert int(servico["tempo_executado_minutos"]) == 90


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_registrar_tempo_executado(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 75},
        headers=atendente_headers,
    )
    assert r.status_code == 403, f"esperado 403, obtido {r.status_code}"

    # ── Assert: tempo permanece null ──────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


async def test_nao_deve_registrar_tempo_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act: sem Authorization ────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 75},
    )
    assert r.status_code in (401, 403), f"esperado 401 ou 403, obtido {r.status_code}"

    # ── Assert: tempo permanece null ──────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


# ---------------------------------------------------------------------------
# Cenários de validação de domínio
# ---------------------------------------------------------------------------


async def test_nao_deve_registrar_tempo_zero(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 0},
        headers=mecanico_headers,
    )
    assert r.status_code == 422, f"esperado 422, obtido {r.status_code} — {r.text}"

    # ── Assert: tempo permanece null ──────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


async def test_nao_deve_registrar_tempo_negativo(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": -10},
        headers=mecanico_headers,
    )
    assert r.status_code == 422, f"esperado 422, obtido {r.status_code} — {r.text}"

    # ── Assert: tempo permanece null ──────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


async def test_nao_deve_registrar_tempo_em_os_fora_de_em_execucao(
    client: AsyncClient, admin_headers: dict
):
    # OS ainda APROVADA, não iniciamos execução
    dados = await criar_os_aprovada_com_item_reservado(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act ───────────────────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, os_servico_id),
        json={"tempo_executado_minutos": 30},
        headers=mecanico_headers,
    )
    assert r.status_code == 422, f"esperado 422, obtido {r.status_code} — {r.text}"

    # ── Assert: OS permanece APROVADA ─────────────────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    assert os_detalhe["status"] == "APROVADA"

    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


async def test_nao_deve_registrar_tempo_em_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    os_servico_id_real = dados["ordem_servico_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Act: UUID fictício ────────────────────────────────────────────────────
    r = await client.patch(
        _url_tempo(os_id, _UUID_INEXISTENTE),
        json={"tempo_executado_minutos": 30},
        headers=mecanico_headers,
    )
    assert r.status_code == 404, f"esperado 404, obtido {r.status_code} — {r.text}"

    # ── Assert: serviço real permanece sem tempo ──────────────────────────────
    os_detalhe = await detalhar_os(client, mecanico_headers, os_id)
    servico = encontrar_servico_os_por_id(os_detalhe, os_servico_id_real)
    assert servico is not None
    assert servico["tempo_executado_minutos"] is None


async def test_nao_deve_registrar_tempo_em_servico_de_outra_os(
    client: AsyncClient, admin_headers: dict
):
    # Preparar duas OS independentes em EM_EXECUCAO
    dados_1 = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)
    dados_2 = await criar_os_em_execucao_com_um_servico_sem_tempo(client, admin_headers)

    os_1_id = dados_1["ordem_servico"]["id"]
    os_2_id = dados_2["ordem_servico"]["id"]
    servico_da_os_2_id = dados_2["ordem_servico_servico"]["id"]
    servico_da_os_1_id = dados_1["ordem_servico_servico"]["id"]
    mecanico_headers = dados_1["mecanico_headers"]

    # ── Act: passar serviço da OS2 como se fosse da OS1 ───────────────────────
    r = await client.patch(
        _url_tempo(os_1_id, servico_da_os_2_id),
        json={"tempo_executado_minutos": 30},
        headers=mecanico_headers,
    )
    assert r.status_code == 404, f"esperado 404, obtido {r.status_code} — {r.text}"

    # ── Assert: OS 1 — serviço sem tempo ─────────────────────────────────────
    detalhe_1 = await detalhar_os(client, mecanico_headers, os_1_id)
    s1 = encontrar_servico_os_por_id(detalhe_1, servico_da_os_1_id)
    assert s1 is not None
    assert s1["tempo_executado_minutos"] is None

    # ── Assert: OS 2 — serviço sem tempo ─────────────────────────────────────
    detalhe_2 = await detalhar_os(client, admin_headers, os_2_id)
    s2 = encontrar_servico_os_por_id(detalhe_2, servico_da_os_2_id)
    assert s2 is not None
    assert s2["tempo_executado_minutos"] is None
