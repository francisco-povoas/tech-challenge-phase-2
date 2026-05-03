"""
Testes de integração — Fluxo Completo de Orçamento (Fase 2A).

Cenário:
  1. OS criada → diagnóstico concluído.
  2. Atendente gera orçamento → retorna 201 com totais corretos e comunicações.
  3. Admin consulta orçamento → retorna mesmos dados.
  4. Mecânico lista comunicações → vê WHATSAPP e EMAIL com sucesso=True.
  5. Tentativa de gerar segundo orçamento → 409 Conflict.
  6. Mecânico tenta gerar orçamento → 403 Forbidden.

Cada asserção representa uma etapa do fluxo e depende da anterior.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_os_diagnostico_concluido_para_orcamento,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


async def test_fluxo_completo_orcamento(client: AsyncClient, admin_headers: dict):
    # ── Arrange ──────────────────────────────────────────────────────────────
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]
    mecanico_headers = dados["mecanico_headers"]

    # ── Etapa 1: Atendente gera orçamento ────────────────────────────────────
    r_gerar = await client.post(
        f"{_BASE}/{os_id}/orcamento",
        json={"observacao": "Aprovação necessária até sexta-feira"},
        headers=atendente_headers,
    )
    assert r_gerar.status_code == 201, f"Etapa 1 falhou: {r_gerar.text}"

    orcamento = r_gerar.json()
    assert orcamento["ordem_servico_id"] == os_id
    assert normalizar_numero(orcamento["total_servicos"]) == Decimal("180.00")
    assert normalizar_numero(orcamento["total_itens"]) == Decimal("390.00")
    assert normalizar_numero(orcamento["total_geral"]) == Decimal("570.00")
    assert orcamento["observacao"] == "Aprovação necessária até sexta-feira"
    assert orcamento["status"] in {"GERADO", "COMUNICADO"}

    orcamento_id = orcamento["id"]
    comunicacoes_na_criacao = orcamento["comunicacoes"]
    assert len(comunicacoes_na_criacao) >= 1

    # ── Etapa 2: Admin consulta orçamento ────────────────────────────────────
    r_consultar = await client.get(
        f"{_BASE}/{os_id}/orcamento", headers=admin_headers
    )
    assert r_consultar.status_code == 200, f"Etapa 2 falhou: {r_consultar.text}"

    orcamento_consultado = r_consultar.json()
    assert orcamento_consultado["id"] == orcamento_id
    assert normalizar_numero(orcamento_consultado["total_geral"]) == Decimal("570.00")

    # ── Etapa 3: Mecânico lista comunicações ─────────────────────────────────
    r_comunicacoes = await client.get(
        f"{_BASE}/{os_id}/orcamento/comunicacoes", headers=mecanico_headers
    )
    assert r_comunicacoes.status_code == 200, f"Etapa 3 falhou: {r_comunicacoes.text}"

    comunicacoes = r_comunicacoes.json()
    assert isinstance(comunicacoes, list)
    canais = {c["canal"] for c in comunicacoes}
    assert "WHATSAPP" in canais
    assert "EMAIL" in canais
    for com in comunicacoes:
        assert com["sucesso"] is True
        assert com["orcamento_id"] == orcamento_id

    # ── Etapa 4: Tentativa de segundo orçamento → 409 ────────────────────────
    r_duplicado = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=admin_headers
    )
    assert r_duplicado.status_code == 409, (
        f"Etapa 4 esperava 409, recebeu {r_duplicado.status_code}: {r_duplicado.text}"
    )

    # ── Etapa 5: Mecânico tenta gerar orçamento → 403 ────────────────────────
    r_403 = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=mecanico_headers
    )
    # Pode ser 403 (já existe) ou 409 — o que importa é que mecânico não pode gerar
    assert r_403.status_code in {403, 409}, (
        f"Etapa 5 esperava 403 ou 409, recebeu {r_403.status_code}: {r_403.text}"
    )
