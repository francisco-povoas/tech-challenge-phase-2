"""
Testes de integração — Métricas de tempo de execução por serviço do catálogo.

Rotas testadas:
  GET /api/v1/ordens-servico/metricas/servicos/{servico_id}/tempo-execucao
  GET /api/v1/ordens-servico/metricas/servicos/{servico_id}/execucoes

Permissões:
  Administrador e Atendente podem consultar.
  Mecânico NÃO pode (403).
  Sem token → 401 ou 403.

Cada teste cria seus próprios dados. Nenhum teste depende de outro.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    criar_atendente,
    criar_mecanico,
    criar_os_em_execucao_com_servico_e_tempo,
    criar_os_finalizada_com_servico_e_tempo,
    criar_servico,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_SERVICO_INEXISTENTE = "00000000-0000-0000-0000-000000000099"


# ---------------------------------------------------------------------------
# Helpers locais
# ---------------------------------------------------------------------------

def _url_estatistica(servico_id: str) -> str:
    return f"{_BASE}/metricas/servicos/{servico_id}/tempo-execucao"


def _url_execucoes(servico_id: str) -> str:
    return f"{_BASE}/metricas/servicos/{servico_id}/execucoes"


def _dec(value) -> Decimal:
    """Converte qualquer representação numérica para Decimal para comparação segura."""
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Cenários de sucesso — estatística
# ---------------------------------------------------------------------------


async def test_atendente_deve_obter_estatistica_de_servico_com_execucoes(
    client: AsyncClient, admin_headers: dict
):
    """
    Dois OS FINALIZADAS com o mesmo serviço (tempos 60 e 75).
    Estatística deve retornar quantidade=2, média=67.5, menor=60, maior=75.
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(
        client, atendente_headers,
        tempo_medio_minutos=60,
        valor_base="180.00",
    )
    servico_id = servico["id"]

    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=60,
    )
    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=75,
    )

    r = await client.get(_url_estatistica(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["servico_id"] == servico_id
    assert body["nome_servico"] == servico["nome"]
    assert int(body["tempo_estimado_minutos"]) == 60
    assert int(body["quantidade_ordens_servico"]) == 2
    assert _dec(body["tempo_medio_minutos"]) == _dec("67.5")
    assert int(body["menor_tempo_minutos"]) == 60
    assert int(body["maior_tempo_minutos"]) == 75


async def test_atendente_deve_listar_execucoes_de_servico_com_execucoes(
    client: AsyncClient, admin_headers: dict
):
    """
    Dois OS FINALIZADAS com o mesmo serviço.
    Listagem deve retornar 2 execuções com tempos 60 e 75 e status FINALIZADA.
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(
        client, atendente_headers,
        tempo_medio_minutos=60,
        valor_base="180.00",
    )
    servico_id = servico["id"]

    dados1 = await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=60,
    )
    dados2 = await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=75,
    )

    r = await client.get(_url_execucoes(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["servico_id"] == servico_id
    assert body["nome_servico"] == servico["nome"]
    assert int(body["tempo_estimado_minutos"]) == 60
    assert int(body["quantidade_ordens_servico"]) == 2

    execucoes = body["execucoes"]
    assert len(execucoes) == 2

    tempos = {int(e["tempo_executado_minutos"]) for e in execucoes}
    assert tempos == {60, 75}

    assert all(e["status_os"] == "FINALIZADA" for e in execucoes)

    os_ids = {e["ordem_servico_id"] for e in execucoes}
    assert dados1["ordem_servico"]["id"] in os_ids
    assert dados2["ordem_servico"]["id"] in os_ids

    for e in execucoes:
        assert "ordem_servico_id" in e
        assert "ordem_servico_servico_id" in e
        assert "tempo_executado_minutos" in e
        assert "status_os" in e


async def test_admin_deve_obter_estatistica_de_servico(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers, tempo_medio_minutos=60)
    servico_id = servico["id"]

    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=50,
    )

    r = await client.get(_url_estatistica(servico_id), headers=admin_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    assert _dec(body["tempo_medio_minutos"]) == _dec("50")
    assert int(body["menor_tempo_minutos"]) == 50
    assert int(body["maior_tempo_minutos"]) == 50


async def test_admin_deve_listar_execucoes_de_servico(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers)
    servico_id = servico["id"]

    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=45,
    )

    r = await client.get(_url_execucoes(servico_id), headers=admin_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    assert len(body["execucoes"]) == 1


# ---------------------------------------------------------------------------
# Cenários de serviço existente sem execuções
# ---------------------------------------------------------------------------


async def test_deve_retornar_estatistica_vazia_para_servico_existente_sem_execucoes(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    atendente_headers = atendente["headers"]

    servico = await criar_servico(
        client, atendente_headers,
        tempo_medio_minutos=45,
    )
    servico_id = servico["id"]

    r = await client.get(_url_estatistica(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["servico_id"] == servico_id
    assert int(body["tempo_estimado_minutos"]) == 45
    assert int(body["quantidade_ordens_servico"]) == 0
    assert body["tempo_medio_minutos"] is None
    assert body["menor_tempo_minutos"] is None
    assert body["maior_tempo_minutos"] is None


async def test_deve_retornar_execucoes_vazias_para_servico_existente_sem_execucoes(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    atendente_headers = atendente["headers"]

    servico = await criar_servico(client, atendente_headers)
    servico_id = servico["id"]

    r = await client.get(_url_execucoes(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 0
    assert body["execucoes"] == []


# ---------------------------------------------------------------------------
# Cenários de filtros — OS EM_EXECUCAO é ignorada
# ---------------------------------------------------------------------------


async def test_estatistica_deve_ignorar_os_em_execucao(
    client: AsyncClient, admin_headers: dict
):
    """
    Uma OS FINALIZADA (tempo=60) + uma OS EM_EXECUCAO (tempo=999).
    Estatística deve considerar apenas a FINALIZADA.
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers)
    servico_id = servico["id"]

    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=60,
    )
    await criar_os_em_execucao_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=999,
    )

    r = await client.get(_url_estatistica(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    assert _dec(body["tempo_medio_minutos"]) == _dec("60")
    assert int(body["menor_tempo_minutos"]) == 60
    assert int(body["maior_tempo_minutos"]) == 60


async def test_execucoes_deve_ignorar_os_em_execucao(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers)
    servico_id = servico["id"]

    dados_fin = await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=60,
    )
    await criar_os_em_execucao_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_id, tempo_executado_minutos=999,
    )

    r = await client.get(_url_execucoes(servico_id), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    execucoes = body["execucoes"]
    assert len(execucoes) == 1
    assert int(execucoes[0]["tempo_executado_minutos"]) == 60
    assert execucoes[0]["ordem_servico_id"] == dados_fin["ordem_servico"]["id"]

    tempos = {int(e["tempo_executado_minutos"]) for e in execucoes}
    assert 999 not in tempos


# ---------------------------------------------------------------------------
# Cenários de filtros — outros serviços são ignorados
# ---------------------------------------------------------------------------


async def test_estatistica_deve_ignorar_outros_servicos(
    client: AsyncClient, admin_headers: dict
):
    """
    OS FINALIZADA com serviço A (tempo=60) e OS FINALIZADA com serviço B (tempo=999).
    Consulta do serviço A deve retornar apenas tempo=60.
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico_a = await criar_servico(client, atendente_headers)
    servico_b = await criar_servico(client, atendente_headers)

    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_a["id"], tempo_executado_minutos=60,
    )
    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_b["id"], tempo_executado_minutos=999,
    )

    r = await client.get(_url_estatistica(servico_a["id"]), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    assert _dec(body["tempo_medio_minutos"]) == _dec("60")
    assert int(body["menor_tempo_minutos"]) == 60
    assert int(body["maior_tempo_minutos"]) == 60


async def test_execucoes_deve_ignorar_outros_servicos(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico_a = await criar_servico(client, atendente_headers)
    servico_b = await criar_servico(client, atendente_headers)

    dados_a = await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_a["id"], tempo_executado_minutos=60,
    )
    await criar_os_finalizada_com_servico_e_tempo(
        client, admin_headers, atendente_headers, mecanico_headers,
        servico_id=servico_b["id"], tempo_executado_minutos=999,
    )

    r = await client.get(_url_execucoes(servico_a["id"]), headers=atendente_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert int(body["quantidade_ordens_servico"]) == 1
    execucoes = body["execucoes"]
    assert len(execucoes) == 1
    assert execucoes[0]["ordem_servico_id"] == dados_a["ordem_servico"]["id"]

    tempos = {int(e["tempo_executado_minutos"]) for e in execucoes}
    assert 999 not in tempos


# ---------------------------------------------------------------------------
# Cenários de filtros — serviço cancelado é ignorado
# ---------------------------------------------------------------------------


async def test_estatistica_deve_ignorar_servico_cancelado(
    client: AsyncClient, admin_headers: dict
):
    """
    OS FINALIZADA em que o serviço alvo foi adicionado e depois removido/cancelado.
    Um segundo serviço é adicionado para permitir a finalização da OS.
    Estatística do serviço cancelado deve retornar quantidade=0.
    """
    from tests.integration.ordens_servico.factories import (
        criar_cliente,
        criar_veiculo,
        criar_item_estoque,
        criar_ordem_servico,
        gerar_orcamento,
        aprovar_orcamento,
        iniciar_execucao_os,
        registrar_tempo_executado_servico,
        detalhar_os,
    )

    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    # Serviço que será cancelado e serviço ativo para permitir finalizar
    servico_cancelado = await criar_servico(client, atendente_headers)
    servico_ativo = await criar_servico(client, atendente_headers)

    cliente = await criar_cliente(
        client, atendente_headers,
        email=f"cliente-canc-svc-{__import__('uuid').uuid4().hex[:8]}@example.com",
    )
    veiculo = await criar_veiculo(client, atendente_headers, cliente["id"])
    item_estoque = await criar_item_estoque(
        client, atendente_headers,
        quantidade_disponivel=10,
        valor_unitario="50.00",
    )

    _BASE_OS_LOCAL = "/api/v1/ordens-servico"

    os_ = await criar_ordem_servico(client, atendente_headers, cliente["id"], veiculo["id"])
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/iniciar-diagnostico", headers=mecanico_headers)
    assert r.status_code == 200

    r = await client.patch(
        f"{_BASE_OS_LOCAL}/{os_id}/diagnostico",
        json={"diagnostico": "Falha detectada."},
        headers=mecanico_headers,
    )
    assert r.status_code == 200

    # Adicionar serviço que será cancelado
    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos",
        json={"servico_id": servico_cancelado["id"]},
        headers=mecanico_headers,
    )
    assert r.status_code == 201
    os_servico_cancelado = r.json()

    # Adicionar serviço ativo (permanecerá)
    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos",
        json={"servico_id": servico_ativo["id"]},
        headers=mecanico_headers,
    )
    assert r.status_code == 201
    os_servico_ativo = r.json()

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/itens",
        json={"item_estoque_id": item_estoque["id"], "quantidade": 1},
        headers=mecanico_headers,
    )
    assert r.status_code == 201

    # Cancelar/remover o serviço alvo via DELETE
    r = await client.delete(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos/{os_servico_cancelado['id']}",
        headers=mecanico_headers,
    )
    assert r.status_code == 204, f"remover serviço falhou: {r.status_code} — {r.text}"

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/concluir-diagnostico", headers=mecanico_headers)
    assert r.status_code == 200

    await gerar_orcamento(client, atendente_headers, os_id)
    await aprovar_orcamento(client, atendente_headers, os_id)
    await iniciar_execucao_os(client, mecanico_headers, os_id)

    await registrar_tempo_executado_servico(
        client, mecanico_headers, os_id, os_servico_ativo["id"], 80
    )

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 200

    # Estatística do serviço CANCELADO deve ser vazia
    r = await client.get(
        _url_estatistica(servico_cancelado["id"]), headers=atendente_headers
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert int(body["quantidade_ordens_servico"]) == 0
    assert body["tempo_medio_minutos"] is None


async def test_execucoes_deve_ignorar_servico_cancelado(
    client: AsyncClient, admin_headers: dict
):
    from tests.integration.ordens_servico.factories import (
        criar_cliente,
        criar_veiculo,
        criar_item_estoque,
        criar_ordem_servico,
        gerar_orcamento,
        aprovar_orcamento,
        iniciar_execucao_os,
        registrar_tempo_executado_servico,
    )

    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico_cancelado = await criar_servico(client, atendente_headers)
    servico_ativo = await criar_servico(client, atendente_headers)

    cliente = await criar_cliente(
        client, atendente_headers,
        email=f"cliente-canc2-{__import__('uuid').uuid4().hex[:8]}@example.com",
    )
    veiculo = await criar_veiculo(client, atendente_headers, cliente["id"])
    item_estoque = await criar_item_estoque(
        client, atendente_headers,
        quantidade_disponivel=10,
        valor_unitario="50.00",
    )

    _BASE_OS_LOCAL = "/api/v1/ordens-servico"

    os_ = await criar_ordem_servico(client, atendente_headers, cliente["id"], veiculo["id"])
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/iniciar-diagnostico", headers=mecanico_headers)
    assert r.status_code == 200
    r = await client.patch(
        f"{_BASE_OS_LOCAL}/{os_id}/diagnostico",
        json={"diagnostico": "Falha detectada."},
        headers=mecanico_headers,
    )
    assert r.status_code == 200

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos",
        json={"servico_id": servico_cancelado["id"]},
        headers=mecanico_headers,
    )
    assert r.status_code == 201
    os_servico_cancelado = r.json()

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos",
        json={"servico_id": servico_ativo["id"]},
        headers=mecanico_headers,
    )
    assert r.status_code == 201
    os_servico_ativo = r.json()

    r = await client.post(
        f"{_BASE_OS_LOCAL}/{os_id}/itens",
        json={"item_estoque_id": item_estoque["id"], "quantidade": 1},
        headers=mecanico_headers,
    )
    assert r.status_code == 201

    r = await client.delete(
        f"{_BASE_OS_LOCAL}/{os_id}/servicos/{os_servico_cancelado['id']}",
        headers=mecanico_headers,
    )
    assert r.status_code == 204

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/concluir-diagnostico", headers=mecanico_headers)
    assert r.status_code == 200

    await gerar_orcamento(client, atendente_headers, os_id)
    await aprovar_orcamento(client, atendente_headers, os_id)
    await iniciar_execucao_os(client, mecanico_headers, os_id)
    await registrar_tempo_executado_servico(
        client, mecanico_headers, os_id, os_servico_ativo["id"], 80
    )

    r = await client.patch(f"{_BASE_OS_LOCAL}/{os_id}/finalizar", headers=mecanico_headers)
    assert r.status_code == 200

    # Execuções do serviço CANCELADO devem ser vazias
    r = await client.get(
        _url_execucoes(servico_cancelado["id"]), headers=atendente_headers
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert int(body["quantidade_ordens_servico"]) == 0
    assert body["execucoes"] == []


# ---------------------------------------------------------------------------
# Cenários de autorização
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_obter_estatistica(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers)

    r = await client.get(_url_estatistica(servico["id"]), headers=mecanico_headers)
    assert r.status_code == 403, r.text


async def test_mecanico_nao_deve_listar_execucoes(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)
    atendente_headers = atendente["headers"]
    mecanico_headers = mecanico["headers"]

    servico = await criar_servico(client, atendente_headers)

    r = await client.get(_url_execucoes(servico["id"]), headers=mecanico_headers)
    assert r.status_code == 403, r.text


async def test_nao_deve_obter_estatistica_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    servico = await criar_servico(client, atendente["headers"])

    r = await client.get(_url_estatistica(servico["id"]))
    assert r.status_code in (401, 403), r.text


async def test_nao_deve_listar_execucoes_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    servico = await criar_servico(client, atendente["headers"])

    r = await client.get(_url_execucoes(servico["id"]))
    assert r.status_code in (401, 403), r.text


# ---------------------------------------------------------------------------
# Cenários de erro — serviço inexistente
# ---------------------------------------------------------------------------


async def test_deve_retornar_404_ao_obter_estatistica_de_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    atendente_headers = atendente["headers"]

    r = await client.get(_url_estatistica(_SERVICO_INEXISTENTE), headers=atendente_headers)
    assert r.status_code == 404, r.text


async def test_deve_retornar_404_ao_listar_execucoes_de_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    atendente = await criar_atendente(client, admin_headers)
    atendente_headers = atendente["headers"]

    r = await client.get(_url_execucoes(_SERVICO_INEXISTENTE), headers=atendente_headers)
    assert r.status_code == 404, r.text
