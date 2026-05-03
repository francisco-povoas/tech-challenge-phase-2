"""
Testes de integração — Autorização e Status Inválido para Aprovação/Recusa de Orçamento.

Rotas testadas:
  PATCH /api/v1/ordens-servico/{id}/orcamento/aprovar
  PATCH /api/v1/ordens-servico/{id}/orcamento/recusar

Permissões verificadas:
  - Sem token → 401
  - Mecânico → 403
  - Admin e Atendente → podem operar (testado nos outros arquivos)

Status inválido:
  - OS sem orçamento → 404 (orçamento não existe)
  - OS em status incompatível (RECEBIDA) → 422

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_mecanico,
    criar_os_com_orcamento_comunicado_todos_itens_reservados,
    criar_os_diagnostico_concluido_para_orcamento,
    criar_os_recebida,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Autenticação — PATCH aprovar
# ---------------------------------------------------------------------------


async def test_nao_deve_aprovar_orcamento_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar")
    assert r.status_code in (401, 403)


async def test_mecanico_nao_deve_aprovar_orcamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=mecanico_headers)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Autenticação — PATCH recusar
# ---------------------------------------------------------------------------


async def test_nao_deve_recusar_orcamento_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/recusar", json={})
    assert r.status_code in (401, 403)


async def test_mecanico_nao_deve_recusar_orcamento(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_com_orcamento_comunicado_todos_itens_reservados(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=mecanico_headers,
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Status inválido — OS sem orçamento gerado (DIAGNOSTICO_CONCLUIDO)
# ---------------------------------------------------------------------------


async def test_nao_deve_aprovar_os_sem_orcamento_comunicado(
    client: AsyncClient, admin_headers: dict
):
    """OS com diagnóstico concluído mas sem orçamento → 404."""
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=atendente_headers)
    # Use case busca orçamento e lança OrcamentoNaoEncontradoError → 404
    # ou valida status da OS primeiro → 422
    assert r.status_code in (404, 422), (
        f"Esperava 404 ou 422, obteve {r.status_code} — {r.text}"
    )


async def test_nao_deve_recusar_os_sem_orcamento_comunicado(
    client: AsyncClient, admin_headers: dict
):
    """OS com diagnóstico concluído mas sem orçamento → 404."""
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=atendente_headers,
    )
    assert r.status_code in (404, 422), (
        f"Esperava 404 ou 422, obteve {r.status_code} — {r.text}"
    )


# ---------------------------------------------------------------------------
# Status inválido — OS RECEBIDA (sem diagnóstico)
# ---------------------------------------------------------------------------


async def test_nao_deve_aprovar_os_recebida(
    client: AsyncClient, admin_headers: dict
):
    """OS recém-criada (status RECEBIDA) não pode ter orçamento aprovado."""
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(f"{_BASE}/{os_id}/orcamento/aprovar", headers=admin_headers)
    # Status RECEBIDA ≠ AGUARDANDO_APROVACAO → 422 ou 404 (sem orçamento)
    assert r.status_code in (404, 422), (
        f"Esperava 404 ou 422, obteve {r.status_code} — {r.text}"
    )


async def test_nao_deve_recusar_os_recebida(
    client: AsyncClient, admin_headers: dict
):
    """OS recém-criada (status RECEBIDA) não pode ter orçamento recusado."""
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    r = await client.patch(
        f"{_BASE}/{os_id}/orcamento/recusar",
        json={},
        headers=admin_headers,
    )
    assert r.status_code in (404, 422), (
        f"Esperava 404 ou 422, obteve {r.status_code} — {r.text}"
    )
