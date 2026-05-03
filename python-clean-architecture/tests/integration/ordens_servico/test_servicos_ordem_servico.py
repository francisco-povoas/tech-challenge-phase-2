"""
Testes de integração — Serviços na Ordem de Serviço.

Rotas testadas:
  POST   /api/v1/ordens-servico/{id}/servicos
  DELETE /api/v1/ordens-servico/{id}/servicos/{oss_id}

Permissões:
  Administrador e Mecânico podem adicionar/remover serviços.
  Atendente NÃO pode.

Regras:
  - Só adiciona serviço se OS estiver EM_DIAGNOSTICO.
  - Copia snapshot do serviço (nome, descricao, valor_unitario, tempo_estimado).
  - Não pode adicionar o mesmo serviço ativo duas vezes.
  - Cancelamento é soft-delete (cancelado=true).
  - Após cancelamento, pode adicionar o mesmo serviço novamente.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_com_diagnostico,
    criar_os_em_diagnostico,
    criar_os_recebida,
    criar_servico,
    extrair_items,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"


# ---------------------------------------------------------------------------
# Adicionar serviço
# ---------------------------------------------------------------------------


async def test_mecanico_deve_adicionar_servico_na_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": "Urgente"},
        headers=mecanico["headers"],
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"]
    assert data["servico_id"] == servico["id"]
    assert data["nome_servico"] == servico["nome"]
    assert data["cancelado"] is False
    assert data["tempo_executado_minutos"] is None
    assert data["observacao"] == "Urgente"


async def test_admin_deve_adicionar_servico_na_os(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["nome_servico"] == servico["nome"]


async def test_adicionar_servico_valida_snapshot(
    client: AsyncClient, admin_headers: dict
):
    """Snapshot deve refletir os dados do serviço no momento da inclusão."""
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(
        client, admin_headers,
        nome="Troca de correia dentada",
        descricao="Substituição completa",
        valor_base="380.00",
        tempo_medio_minutos=120,
    )

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=admin_headers,
    )
    assert response.status_code == 201

    data = response.json()
    assert data["nome_servico"] == "Troca de correia dentada"
    assert data["descricao_servico"] == "Substituição completa"
    assert data["tempo_estimado_minutos"] == 120
    assert data["tempo_executado_minutos"] is None
    assert data["cancelado"] is False


async def test_atendente_nao_deve_adicionar_servico_na_os(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=atendente["headers"],
    )
    assert response.status_code == 403


async def test_nao_deve_adicionar_servico_em_os_recebida(
    client: AsyncClient, admin_headers: dict
):
    """OS em status RECEBIDA não permite adicionar serviço."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_adicionar_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico_id_falso = str(uuid.uuid4())

    response = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico_id_falso, "observacao": None},
        headers=mecanico["headers"],
    )
    assert response.status_code == 404


async def test_nao_deve_adicionar_servico_duplicado_ativo(
    client: AsyncClient, admin_headers: dict
):
    """Dois vínculos ativos com o mesmo servico_id não são permitidos."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Primeira adição — deve funcionar
    r1 = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r1.status_code == 201

    # Segunda adição com mesmo serviço — deve falhar
    r2 = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r2.status_code in (400, 409, 422)

    # Detalhar OS e validar que há apenas um vínculo ativo com esse servico_id
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    assert r_detalhe.status_code == 200
    servicos_ativos = [
        s for s in r_detalhe.json()["servicos"]
        if not s["cancelado"] and s["servico_id"] == servico["id"]
    ]
    assert len(servicos_ativos) == 1


# ---------------------------------------------------------------------------
# Cancelar serviço
# ---------------------------------------------------------------------------


async def test_mecanico_deve_cancelar_servico_da_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Adicionar serviço
    r_add = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r_add.status_code == 201
    oss_id = r_add.json()["id"]

    # Cancelar serviço
    r_del = await client.delete(
        f"{_BASE}/{os_id}/servicos/{oss_id}",
        headers=mecanico["headers"],
    )
    assert r_del.status_code == 204

    # Detalhar OS e validar cancelado=true
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    assert r_detalhe.status_code == 200
    servicos = r_detalhe.json()["servicos"]
    vinculo = next((s for s in servicos if s["id"] == oss_id), None)
    assert vinculo is not None
    assert vinculo["cancelado"] is True


async def test_nao_deve_cancelar_servico_inexistente_na_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    oss_id_falso = str(uuid.uuid4())

    response = await client.delete(
        f"{_BASE}/{os_id}/servicos/{oss_id_falso}",
        headers=mecanico["headers"],
    )
    assert response.status_code == 404


async def test_nao_deve_cancelar_servico_ja_cancelado(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Adicionar e então cancelar
    r_add = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r_add.status_code == 201
    oss_id = r_add.json()["id"]

    await client.delete(f"{_BASE}/{os_id}/servicos/{oss_id}", headers=mecanico["headers"])

    # Tentar cancelar novamente — deve falhar
    r2 = await client.delete(
        f"{_BASE}/{os_id}/servicos/{oss_id}",
        headers=mecanico["headers"],
    )
    assert r2.status_code in (400, 422)


async def test_deve_permitir_adicionar_servico_novamente_apos_cancelamento(
    client: AsyncClient, admin_headers: dict
):
    """Após cancelar, pode adicionar o mesmo serviço novamente."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Primeira adição
    r1 = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r1.status_code == 201
    oss_id_1 = r1.json()["id"]

    # Cancelar
    await client.delete(f"{_BASE}/{os_id}/servicos/{oss_id_1}", headers=mecanico["headers"])

    # Segunda adição — deve funcionar porque não há vínculo ativo
    r2 = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r2.status_code == 201

    # Detalhe deve conter um cancelado e um ativo para o mesmo servico_id
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    servicos = r_detalhe.json()["servicos"]
    do_mesmo_servico = [s for s in servicos if s["servico_id"] == servico["id"]]
    cancelados = [s for s in do_mesmo_servico if s["cancelado"]]
    ativos = [s for s in do_mesmo_servico if not s["cancelado"]]
    assert len(cancelados) == 1
    assert len(ativos) == 1


async def test_servico_cancelado_nao_deve_permitir_concluir_diagnostico(
    client: AsyncClient, admin_headers: dict
):
    """Se o único serviço foi cancelado, não pode concluir diagnóstico."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_com_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    servico = await criar_servico(client, admin_headers)

    # Adicionar e cancelar o único serviço
    r_add = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r_add.status_code == 201
    oss_id = r_add.json()["id"]
    await client.delete(f"{_BASE}/{os_id}/servicos/{oss_id}", headers=mecanico["headers"])

    # Tentar concluir diagnóstico sem serviço ativo — deve falhar
    r_concluir = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert r_concluir.status_code in (400, 422)
