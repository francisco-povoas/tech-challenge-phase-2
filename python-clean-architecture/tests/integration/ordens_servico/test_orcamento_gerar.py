"""
Testes de integração — Gerar Orçamento da Ordem de Serviço.

Rota testada:
  POST /api/v1/ordens-servico/{id}/orcamento

Permissões:
  Administrador e Atendente podem gerar orçamento.
  Mecânico NÃO pode (403).

Pré-condições:
  - OS deve estar em DIAGNOSTICO_CONCLUIDO.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_diagnostico_concluido_para_orcamento,
    criar_os_recebida,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Casos de sucesso
# ---------------------------------------------------------------------------


async def test_admin_gera_orcamento_retorna_201(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 201


async def test_atendente_gera_orcamento_retorna_201(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    atendente_headers = dados["atendente_headers"]

    response = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=atendente_headers
    )

    assert response.status_code == 201


async def test_orcamento_gerado_possui_campos_obrigatorios(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    assert "id" in payload
    assert "ordem_servico_id" in payload
    assert "status" in payload
    assert "total_servicos" in payload
    assert "total_itens" in payload
    assert "total_geral" in payload
    assert "criado_em" in payload


async def test_orcamento_gerado_total_servicos_correto(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    assert normalizar_numero(payload["total_servicos"]) == Decimal("180.00")


async def test_orcamento_gerado_total_itens_correto(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    # 85.00 × 2 + 220.00 × 1 = 390.00
    assert normalizar_numero(payload["total_itens"]) == Decimal("390.00")


async def test_orcamento_gerado_total_geral_correto(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    assert normalizar_numero(payload["total_geral"]) == Decimal("570.00")


async def test_orcamento_gerado_possui_ordem_servico_id_correto(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    assert payload["ordem_servico_id"] == os_id


async def test_orcamento_gerado_com_observacao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    obs = "Recomendamos troca imediata das pastilhas"

    response = await client.post(
        f"{_BASE}/{os_id}/orcamento",
        json={"observacao": obs},
        headers=admin_headers,
    )

    payload = response.json()
    assert payload["observacao"] == obs


async def test_orcamento_gerado_possui_comunicacoes(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    assert "comunicacoes" in payload
    assert isinstance(payload["comunicacoes"], list)
    assert len(payload["comunicacoes"]) >= 1


async def test_orcamento_gerado_comunicacoes_incluem_whatsapp_e_email(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    payload = response.json()
    canais = {c["canal"] for c in payload["comunicacoes"]}
    assert "WHATSAPP" in canais
    assert "EMAIL" in canais


# ---------------------------------------------------------------------------
# Casos de erro
# ---------------------------------------------------------------------------


async def test_gerar_orcamento_duas_vezes_retorna_409(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)
    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 409


async def test_gerar_orcamento_os_nao_em_diagnostico_concluido_retorna_422(
    client: AsyncClient, admin_headers: dict
):
    """OS ainda em RECEBIDA não pode ter orçamento gerado."""
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 422


async def test_gerar_orcamento_os_inexistente_retorna_404(
    client: AsyncClient, admin_headers: dict
):
    import uuid

    os_id = str(uuid.uuid4())
    response = await client.post(f"{_BASE}/{os_id}/orcamento", headers=admin_headers)

    assert response.status_code == 404


async def test_mecanico_nao_pode_gerar_orcamento_retorna_403(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    response = await client.post(
        f"{_BASE}/{os_id}/orcamento", headers=mecanico_headers
    )

    assert response.status_code == 403


async def test_gerar_orcamento_sem_autenticacao_retorna_401(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_diagnostico_concluido_para_orcamento(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(f"{_BASE}/{os_id}/orcamento")

    assert response.status_code == 401
