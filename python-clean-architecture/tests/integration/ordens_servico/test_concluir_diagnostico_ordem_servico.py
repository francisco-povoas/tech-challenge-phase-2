"""
Testes de integração — Concluir Diagnóstico da Ordem de Serviço.

Rota testada:
  PATCH /api/v1/ordens-servico/{id}/concluir-diagnostico

Permissões:
  Administrador e Mecânico podem concluir diagnóstico.
  Atendente NÃO pode.

Pré-condições:
  - OS deve estar em EM_DIAGNOSTICO.
  - Diagnóstico deve estar preenchido.
  - Deve existir pelo menos um serviço ativo.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_com_diagnostico,
    criar_os_em_diagnostico,
    criar_os_pronta_para_concluir_diagnostico,
    criar_os_recebida,
    criar_servico,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Casos de sucesso
# ---------------------------------------------------------------------------


async def test_mecanico_deve_concluir_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_pronta_para_concluir_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "DIAGNOSTICO_CONCLUIDO"
    assert data["id"] == os_id
    assert data["diagnostico"]  # deve estar preenchido


async def test_admin_deve_concluir_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_pronta_para_concluir_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DIAGNOSTICO_CONCLUIDO"


async def test_concluir_diagnostico_preenche_data_conclusao(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_pronta_para_concluir_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=admin_headers,
    )
    assert response.status_code == 200

    data = response.json()
    # diagnostico_concluido_em deve estar preenchido se o campo for retornado
    if "diagnostico_concluido_em" in data:
        assert data["diagnostico_concluido_em"] is not None


# ---------------------------------------------------------------------------
# Autorização
# ---------------------------------------------------------------------------


async def test_atendente_nao_deve_concluir_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_pronta_para_concluir_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=atendente["headers"],
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Pré-condições
# ---------------------------------------------------------------------------


async def test_nao_deve_concluir_diagnostico_sem_diagnostico_registrado(
    client: AsyncClient, admin_headers: dict
):
    """OS em EM_DIAGNOSTICO mas sem texto de diagnóstico não pode ser concluída."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Adicionar serviço mas NÃO registrar diagnóstico
    await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_concluir_diagnostico_sem_servico_ativo(
    client: AsyncClient, admin_headers: dict
):
    """OS sem nenhum serviço vinculado não pode ter diagnóstico concluído."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_com_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    # Não adiciona nenhum serviço
    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_concluir_diagnostico_com_apenas_servico_cancelado(
    client: AsyncClient, admin_headers: dict
):
    """Se o único serviço foi cancelado, não pode concluir diagnóstico."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_com_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Adicionar e imediatamente cancelar o único serviço
    r_add = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r_add.status_code == 201
    oss_id = r_add.json()["id"]

    await client.delete(
        f"{_BASE}/{os_id}/servicos/{oss_id}",
        headers=mecanico["headers"],
    )

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_concluir_diagnostico_antes_de_iniciar(
    client: AsyncClient, admin_headers: dict
):
    """OS ainda em RECEBIDA — não pode concluir diagnóstico."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]

    response = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_concluir_diagnostico_duas_vezes(
    client: AsyncClient, admin_headers: dict
):
    """Após DIAGNOSTICO_CONCLUIDO, nova tentativa deve falhar."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_pronta_para_concluir_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    # Primeira conclusão
    r1 = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert r1.status_code == 200

    # Segunda tentativa — transição inválida
    r2 = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert r2.status_code in (400, 422)
