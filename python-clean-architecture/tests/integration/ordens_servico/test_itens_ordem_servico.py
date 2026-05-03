"""
Testes de integração — Itens de Estoque na Ordem de Serviço.

Rotas testadas:
  POST   /api/v1/ordens-servico/{id}/itens
  DELETE /api/v1/ordens-servico/{id}/itens/{osi_id}
  GET    /api/v1/itens-estoque/{id}  (para verificar saldo)

Permissões:
  Administrador e Mecânico podem adicionar/remover itens.
  Atendente NÃO pode.

Regras de estoque:
  - Se disponível >= solicitado → RESERVADO, estoque atualizado.
  - Se disponível < solicitado  → A_RECEBER, estoque não muda.
  - Sem reserva parcial.
  - Cancelar RESERVADO devolve estoque.
  - Cancelar A_RECEBER não altera estoque.
  - Não pode adicionar o mesmo item ativo duas vezes.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

import uuid

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_item_estoque,
    criar_mecanico,
    criar_os_em_diagnostico,
    criar_os_recebida,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_BASE_ITENS = "/api/v1/itens-estoque"


# ---------------------------------------------------------------------------
# Helpers locais
# ---------------------------------------------------------------------------


async def _adicionar_item(
    client: AsyncClient,
    headers: dict,
    os_id: str,
    item_id: str,
    quantidade: int = 2,
) -> dict:
    """Adiciona item na OS e retorna JSON do vínculo criado."""
    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item_id, "quantidade": quantidade},
        headers=headers,
    )
    assert response.status_code == 201, (
        f"Erro ao adicionar item: {response.status_code} — {response.text}"
    )
    return response.json()


async def _saldo_item(
    client: AsyncClient,
    admin_headers: dict,
    item_id: str,
) -> dict:
    """Busca item de estoque e retorna (disponivel, reservada)."""
    r = await client.get(f"{_BASE_ITENS}/{item_id}", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    return {
        "disponivel": normalizar_numero(data["quantidade_disponivel"]),
        "reservada": normalizar_numero(data["quantidade_reservada"]),
    }


# ---------------------------------------------------------------------------
# Adicionar item com estoque suficiente → RESERVADO
# ---------------------------------------------------------------------------


async def test_mecanico_deve_adicionar_item_com_estoque_suficiente_e_reservar(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=10, quantidade_minima=2
    )

    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=2)

    assert vinculo["status"] == "RESERVADO"
    assert normalizar_numero(vinculo["quantidade"]) == 2

    saldo = await _saldo_item(client, admin_headers, item["id"])
    assert saldo["disponivel"] == 8   # 10 - 2
    assert saldo["reservada"] == 2    # 0 + 2


async def test_admin_deve_adicionar_item_com_estoque_suficiente_e_reservar(
    client: AsyncClient, admin_headers: dict
):
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=5, quantidade_minima=1
    )

    vinculo = await _adicionar_item(client, admin_headers, os_id, item["id"], quantidade=3)

    assert vinculo["status"] == "RESERVADO"
    saldo = await _saldo_item(client, admin_headers, item["id"])
    assert saldo["disponivel"] == 2   # 5 - 3
    assert saldo["reservada"] == 3


# ---------------------------------------------------------------------------
# Adicionar item sem estoque → A_RECEBER
# ---------------------------------------------------------------------------


async def test_mecanico_deve_adicionar_item_sem_estoque_com_status_a_receber(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=0, quantidade_minima=0
    )

    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=1)

    assert vinculo["status"] == "A_RECEBER"

    saldo = await _saldo_item(client, admin_headers, item["id"])
    assert saldo["disponivel"] == 0  # não foi alterado
    assert saldo["reservada"] == 0


# ---------------------------------------------------------------------------
# Sem reserva parcial
# ---------------------------------------------------------------------------


async def test_nao_deve_fazer_reserva_parcial(
    client: AsyncClient, admin_headers: dict
):
    """Disponível=1, solicitado=2 → A_RECEBER, estoque não muda."""
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=1, quantidade_minima=0
    )

    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=2)

    assert vinculo["status"] == "A_RECEBER"

    saldo = await _saldo_item(client, admin_headers, item["id"])
    assert saldo["disponivel"] == 1  # não foi alterado
    assert saldo["reservada"] == 0


# ---------------------------------------------------------------------------
# Restrições de status da OS
# ---------------------------------------------------------------------------


async def test_nao_deve_adicionar_item_em_os_recebida(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_recebida(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_atendente_nao_deve_adicionar_item_na_os(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    dados = await criar_os_em_diagnostico(client, admin_headers)
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": 1},
        headers=atendente["headers"],
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Validações de payload
# ---------------------------------------------------------------------------


async def test_nao_deve_adicionar_item_inexistente(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]

    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": str(uuid.uuid4()), "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert response.status_code == 404


async def test_nao_deve_adicionar_item_com_quantidade_zero(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": 0},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


async def test_nao_deve_adicionar_item_com_quantidade_negativa(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(client, admin_headers)

    response = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": -1},
        headers=mecanico["headers"],
    )
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Duplicidade
# ---------------------------------------------------------------------------


async def test_nao_deve_adicionar_item_duplicado_ativo(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=20
    )

    # Primeira adição — deve funcionar
    r1 = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r1.status_code == 201
    saldo_apos_r1 = await _saldo_item(client, admin_headers, item["id"])

    # Segunda adição com mesmo item — deve falhar
    r2 = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r2.status_code in (400, 409, 422)

    # Estoque não deve ter sido alterado pela segunda tentativa
    saldo_apos_r2 = await _saldo_item(client, admin_headers, item["id"])
    assert saldo_apos_r2["disponivel"] == saldo_apos_r1["disponivel"]
    assert saldo_apos_r2["reservada"] == saldo_apos_r1["reservada"]

    # Detalhar OS — não pode haver dois ativos com o mesmo item_estoque_id
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    itens_ativos = [
        i for i in r_detalhe.json()["itens"]
        if i["item_estoque_id"] == item["id"] and i["status"] != "CANCELADO"
    ]
    assert len(itens_ativos) == 1


# ---------------------------------------------------------------------------
# Cancelar item RESERVADO → devolve estoque
# ---------------------------------------------------------------------------


async def test_mecanico_deve_cancelar_item_reservado_e_devolver_estoque(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=10, quantidade_minima=2
    )

    # Adicionar item (disponível=10, reservar 3)
    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=3)
    assert vinculo["status"] == "RESERVADO"

    saldo_apos_adicao = await _saldo_item(client, admin_headers, item["id"])
    assert saldo_apos_adicao["disponivel"] == 7
    assert saldo_apos_adicao["reservada"] == 3

    # Cancelar item
    r_del = await client.delete(
        f"{_BASE}/{os_id}/itens/{vinculo['id']}",
        headers=mecanico["headers"],
    )
    assert r_del.status_code == 204

    # Estoque deve ter sido devolvido
    saldo_apos_cancel = await _saldo_item(client, admin_headers, item["id"])
    assert saldo_apos_cancel["disponivel"] == 10  # voltou ao original
    assert saldo_apos_cancel["reservada"] == 0


# ---------------------------------------------------------------------------
# Cancelar item A_RECEBER → estoque não muda
# ---------------------------------------------------------------------------


async def test_mecanico_deve_cancelar_item_a_receber_sem_alterar_estoque(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    # Item sem saldo → A_RECEBER
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=0, quantidade_minima=0
    )

    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=2)
    assert vinculo["status"] == "A_RECEBER"

    saldo_antes = await _saldo_item(client, admin_headers, item["id"])

    # Cancelar item A_RECEBER
    r_del = await client.delete(
        f"{_BASE}/{os_id}/itens/{vinculo['id']}",
        headers=mecanico["headers"],
    )
    assert r_del.status_code == 204

    # Estoque não deve ter mudado
    saldo_depois = await _saldo_item(client, admin_headers, item["id"])
    assert saldo_depois["disponivel"] == saldo_antes["disponivel"]
    assert saldo_depois["reservada"] == saldo_antes["reservada"]


# ---------------------------------------------------------------------------
# Erros ao cancelar
# ---------------------------------------------------------------------------


async def test_nao_deve_cancelar_item_inexistente_na_os(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    osi_id_falso = str(uuid.uuid4())

    response = await client.delete(
        f"{_BASE}/{os_id}/itens/{osi_id_falso}",
        headers=mecanico["headers"],
    )
    assert response.status_code == 404


async def test_nao_deve_cancelar_item_ja_cancelado(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(client, admin_headers, quantidade_disponivel=5)

    vinculo = await _adicionar_item(client, mecanico["headers"], os_id, item["id"])
    osi_id = vinculo["id"]

    # Cancelar pela primeira vez
    r1 = await client.delete(f"{_BASE}/{os_id}/itens/{osi_id}", headers=mecanico["headers"])
    assert r1.status_code == 204

    # Tentar cancelar novamente — deve falhar
    r2 = await client.delete(f"{_BASE}/{os_id}/itens/{osi_id}", headers=mecanico["headers"])
    assert r2.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Adicionar item novamente após cancelamento
# ---------------------------------------------------------------------------


async def test_deve_permitir_adicionar_item_novamente_apos_cancelamento(
    client: AsyncClient, admin_headers: dict
):
    mecanico = await criar_mecanico(client, admin_headers)
    dados = await criar_os_em_diagnostico(
        client, admin_headers, mecanico_headers=mecanico["headers"]
    )
    os_id = dados["ordem_servico"]["id"]
    item = await criar_item_estoque(
        client, admin_headers, quantidade_disponivel=10
    )

    # Primeira adição
    v1 = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=2)
    assert v1["status"] == "RESERVADO"

    # Cancelar
    await client.delete(f"{_BASE}/{os_id}/itens/{v1['id']}", headers=mecanico["headers"])

    # Segunda adição — deve funcionar
    v2 = await _adicionar_item(client, mecanico["headers"], os_id, item["id"], quantidade=2)
    assert v2["status"] == "RESERVADO"

    # Detalhe deve conter: 1 cancelado, 1 ativo para o mesmo item_estoque_id
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    itens_do_mesmo = [
        i for i in r_detalhe.json()["itens"]
        if i["item_estoque_id"] == item["id"]
    ]
    cancelados = [i for i in itens_do_mesmo if i["status"] == "CANCELADO"]
    ativos = [i for i in itens_do_mesmo if i["status"] != "CANCELADO"]
    assert len(cancelados) == 1
    assert len(ativos) == 1
