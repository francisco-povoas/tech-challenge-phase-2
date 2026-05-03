"""
Teste de integração — Fluxo completo de Diagnóstico.

Jornada principal da primeira fase:

  1.  Criar Atendente
  2.  Criar Mecânico
  3.  Criar cliente
  4.  Criar veículo
  5.  Criar serviço
  6.  Criar item com saldo suficiente
  7.  Criar item sem saldo
  8.  Criar OS com Atendente  → RECEBIDA
  9.  Iniciar diagnóstico com Mecânico  → EM_DIAGNOSTICO
  10. Registrar diagnóstico
  11. Adicionar serviço
  12. Adicionar item com saldo  → RESERVADO, estoque decrementado
  13. Adicionar item sem saldo  → A_RECEBER, estoque inalterado
  14. Concluir diagnóstico  → DIAGNOSTICO_CONCLUIDO
  15. Detalhar OS e validar estado final

Cada etapa valida seu próprio resultado antes de prosseguir.
"""

import pytest
from httpx import AsyncClient

from tests.integration.ordens_servico.factories import (
    autenticar,
    criar_atendente,
    criar_cliente,
    criar_item_estoque,
    criar_mecanico,
    criar_ordem_servico,
    criar_servico,
    criar_veiculo,
    normalizar_numero,
)

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/ordens-servico"
_BASE_ITENS = "/api/v1/itens-estoque"


async def test_fluxo_completo_ate_diagnostico_concluido(
    client: AsyncClient, admin_headers: dict
):
    # -----------------------------------------------------------------------
    # 1. Criar Atendente e Mecânico
    # -----------------------------------------------------------------------
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    # -----------------------------------------------------------------------
    # 2. Criar cliente e veículo (via atendente)
    # -----------------------------------------------------------------------
    cliente = await criar_cliente(client, atendente["headers"])
    veiculo = await criar_veiculo(client, atendente["headers"], cliente["id"])

    # -----------------------------------------------------------------------
    # 3. Criar serviço e itens de estoque (via admin)
    # -----------------------------------------------------------------------
    servico = await criar_servico(
        client, admin_headers,
        nome="Troca de pastilhas de freio",
        descricao="Substituição das pastilhas dianteiras",
        valor_base="180.00",
        tempo_medio_minutos=90,
    )

    item_com_saldo = await criar_item_estoque(
        client, admin_headers,
        nome="Pastilha de freio dianteira",
        quantidade_disponivel=10,
        quantidade_minima=2,
        valor_unitario="85.00",
    )

    item_sem_saldo = await criar_item_estoque(
        client, admin_headers,
        nome="Disco de freio especial",
        quantidade_disponivel=0,
        quantidade_minima=1,
        valor_unitario="220.00",
    )

    # -----------------------------------------------------------------------
    # 4. Criar OS com Atendente → deve nascer RECEBIDA
    # -----------------------------------------------------------------------
    os_ = await criar_ordem_servico(
        client,
        atendente["headers"],
        cliente["id"],
        veiculo["id"],
        queixa_inicial="Freio vibrando ao parar",
    )
    assert os_["status"] == "RECEBIDA"
    assert os_["cliente_id"] == cliente["id"]
    assert os_["veiculo_id"] == veiculo["id"]
    assert os_["queixa_inicial"] == "Freio vibrando ao parar"
    assert os_["diagnostico"] is None
    os_id = os_["id"]

    # -----------------------------------------------------------------------
    # 5. Mecânico inicia diagnóstico → EM_DIAGNOSTICO
    # -----------------------------------------------------------------------
    r_iniciar = await client.patch(
        f"{_BASE}/{os_id}/iniciar-diagnostico",
        headers=mecanico["headers"],
    )
    assert r_iniciar.status_code == 200
    os_ = r_iniciar.json()
    assert os_["status"] == "EM_DIAGNOSTICO"
    if "iniciado_diagnostico_em" in os_:
        assert os_["iniciado_diagnostico_em"] is not None

    # -----------------------------------------------------------------------
    # 6. Mecânico registra diagnóstico
    # -----------------------------------------------------------------------
    r_diag = await client.patch(
        f"{_BASE}/{os_id}/diagnostico",
        json={"diagnostico": "Pastilhas de freio com desgaste excessivo"},
        headers=mecanico["headers"],
    )
    assert r_diag.status_code == 200
    assert r_diag.json()["diagnostico"] == "Pastilhas de freio com desgaste excessivo"
    assert r_diag.json()["status"] == "EM_DIAGNOSTICO"

    # -----------------------------------------------------------------------
    # 7. Mecânico adiciona serviço
    # -----------------------------------------------------------------------
    r_add_servico = await client.post(
        f"{_BASE}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": "Substituir as 4 rodas"},
        headers=mecanico["headers"],
    )
    assert r_add_servico.status_code == 201
    oss = r_add_servico.json()
    assert oss["servico_id"] == servico["id"]
    assert oss["nome_servico"] == servico["nome"]
    assert oss["descricao_servico"] == servico["descricao"]
    assert oss["cancelado"] is False
    assert oss["tempo_executado_minutos"] is None
    assert oss["observacao"] == "Substituir as 4 rodas"

    # -----------------------------------------------------------------------
    # 8. Mecânico adiciona item COM saldo → RESERVADO
    # -----------------------------------------------------------------------
    r_add_item_com = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item_com_saldo["id"], "quantidade": 4},
        headers=mecanico["headers"],
    )
    assert r_add_item_com.status_code == 201
    osi_com = r_add_item_com.json()
    assert osi_com["status"] == "RESERVADO"
    assert normalizar_numero(osi_com["quantidade"]) == 4

    # Verificar estoque após reserva
    r_estoque_com = await client.get(
        f"{_BASE_ITENS}/{item_com_saldo['id']}", headers=admin_headers
    )
    assert r_estoque_com.status_code == 200
    estoque_com = r_estoque_com.json()
    assert normalizar_numero(estoque_com["quantidade_disponivel"]) == 6   # 10 - 4
    assert normalizar_numero(estoque_com["quantidade_reservada"]) == 4    # 0 + 4

    # -----------------------------------------------------------------------
    # 9. Mecânico adiciona item SEM saldo → A_RECEBER
    # -----------------------------------------------------------------------
    r_add_item_sem = await client.post(
        f"{_BASE}/{os_id}/itens",
        json={"item_estoque_id": item_sem_saldo["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r_add_item_sem.status_code == 201
    osi_sem = r_add_item_sem.json()
    assert osi_sem["status"] == "A_RECEBER"

    # Verificar estoque — não deve ter mudado
    r_estoque_sem = await client.get(
        f"{_BASE_ITENS}/{item_sem_saldo['id']}", headers=admin_headers
    )
    estoque_sem = r_estoque_sem.json()
    assert normalizar_numero(estoque_sem["quantidade_disponivel"]) == 0
    assert normalizar_numero(estoque_sem["quantidade_reservada"]) == 0

    # -----------------------------------------------------------------------
    # 10. Mecânico conclui diagnóstico → DIAGNOSTICO_CONCLUIDO
    # -----------------------------------------------------------------------
    r_concluir = await client.patch(
        f"{_BASE}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert r_concluir.status_code == 200
    os_final = r_concluir.json()
    assert os_final["status"] == "DIAGNOSTICO_CONCLUIDO"
    if "diagnostico_concluido_em" in os_final:
        assert os_final["diagnostico_concluido_em"] is not None

    # -----------------------------------------------------------------------
    # 11. Detalhar OS e validar estado final completo
    # -----------------------------------------------------------------------
    r_detalhe = await client.get(f"{_BASE}/{os_id}", headers=admin_headers)
    assert r_detalhe.status_code == 200
    detalhe = r_detalhe.json()

    assert detalhe["status"] == "DIAGNOSTICO_CONCLUIDO"
    assert detalhe["queixa_inicial"] == "Freio vibrando ao parar"
    assert detalhe["diagnostico"] == "Pastilhas de freio com desgaste excessivo"

    # Serviço deve estar ativo e com snapshot correto
    assert len(detalhe["servicos"]) >= 1
    oss_detalhe = next(
        (s for s in detalhe["servicos"] if s["servico_id"] == servico["id"]), None
    )
    assert oss_detalhe is not None
    assert oss_detalhe["cancelado"] is False
    assert oss_detalhe["nome_servico"] == servico["nome"]
    assert oss_detalhe["tempo_executado_minutos"] is None

    # Item RESERVADO deve aparecer corretamente
    osi_com_detalhe = next(
        (i for i in detalhe["itens"] if i["item_estoque_id"] == item_com_saldo["id"]), None
    )
    assert osi_com_detalhe is not None
    assert osi_com_detalhe["status"] == "RESERVADO"
    assert normalizar_numero(osi_com_detalhe["quantidade"]) == 4

    # Item A_RECEBER deve aparecer corretamente
    osi_sem_detalhe = next(
        (i for i in detalhe["itens"] if i["item_estoque_id"] == item_sem_saldo["id"]), None
    )
    assert osi_sem_detalhe is not None
    assert osi_sem_detalhe["status"] == "A_RECEBER"
