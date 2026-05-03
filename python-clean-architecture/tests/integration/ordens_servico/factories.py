"""
Factories e helpers de integração para o módulo Ordens de Serviço.

Funções auxiliares reutilizáveis — não são fixtures pytest.
Cada teste importa explicitamente as factories que precisa.
"""

import random
import string
import uuid
from decimal import Decimal

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_BASE_OS = "/api/v1/ordens-servico"
_BASE_CLIENTES = "/api/v1/clientes"
_BASE_VEICULOS = "/api/v1/veiculos"
_BASE_SERVICOS = "/api/v1/servicos"
_BASE_ITENS = "/api/v1/itens-estoque"
_BASE_USUARIOS = "/api/v1/usuarios"
_BASE_AUTH = "/api/v1/auth/token"

_SENHA_PADRAO = "Senha@1234"


# ---------------------------------------------------------------------------
# Helpers gerais
# ---------------------------------------------------------------------------


def _cpf_aleatorio() -> str:
    """Gera 11 dígitos aleatórios."""
    return "".join(str(random.randint(0, 9)) for _ in range(11))


def _placa_aleatoria() -> str:
    """Gera placa Mercosul: ABC1D23."""
    letras = string.ascii_uppercase
    return (
        random.choice(letras)
        + random.choice(letras)
        + random.choice(letras)
        + str(random.randint(0, 9))
        + random.choice(letras)
        + str(random.randint(0, 9))
        + str(random.randint(0, 9))
    )


def _nome_unico(base: str = "Item") -> str:
    return f"{base} {uuid.uuid4().hex[:8]}"


def _codigo_unico() -> str:
    return f"COD-{uuid.uuid4().hex[:10].upper()}"


def extrair_items(payload) -> list:
    """Normaliza resposta de listagem para lista de itens."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    raise AssertionError(f"Formato inesperado de resposta de listagem: {payload}")


def normalizar_numero(value) -> Decimal:
    """Converte qualquer representação numérica para Decimal."""
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------


async def autenticar(client: AsyncClient, email: str, senha: str) -> dict:
    """Autentica e retorna headers Authorization Bearer."""
    response = await client.post(
        _BASE_AUTH,
        data={"username": email, "password": senha},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, (
        f"Falha ao autenticar {email}: {response.status_code} — {response.text}"
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Criação de usuários
# ---------------------------------------------------------------------------


async def criar_usuario_com_perfil(
    client: AsyncClient,
    admin_headers: dict,
    perfil: str,
    nome: str | None = None,
) -> dict:
    """
    Cria usuário com perfil informado via admin, autentica e retorna dict com:
    {email, senha, headers, usuario}
    """
    email = f"usuario-{uuid.uuid4().hex[:8]}@example.com"
    senha = _SENHA_PADRAO
    nome = nome or f"Usuario {perfil} {uuid.uuid4().hex[:6]}"
    payload = {
        "nome": nome,
        "email": email,
        "senha": senha,
        "perfis": [perfil],
    }
    response = await client.post(_BASE_USUARIOS, json=payload, headers=admin_headers)
    assert response.status_code in (200, 201), (
        f"Erro ao criar usuário {perfil}: {response.status_code} — {response.text}"
    )
    usuario = response.json()
    headers = await autenticar(client, email, senha)
    return {"email": email, "senha": senha, "headers": headers, "usuario": usuario}


async def criar_atendente(client: AsyncClient, admin_headers: dict) -> dict:
    """Cria usuário Atendente e retorna dict com headers e dados."""
    return await criar_usuario_com_perfil(client, admin_headers, "Atendente")


async def criar_mecanico(client: AsyncClient, admin_headers: dict) -> dict:
    """Cria usuário Mecânico e retorna dict com headers e dados."""
    return await criar_usuario_com_perfil(client, admin_headers, "Mecanico")


# ---------------------------------------------------------------------------
# Criação de clientes
# ---------------------------------------------------------------------------


async def criar_cliente(client: AsyncClient, headers: dict, **overrides) -> dict:
    """Cria cliente PF e retorna JSON criado."""
    payload = {
        "tipo_pessoa": "PF",
        "nome_razao_social": _nome_unico("Cliente OS"),
        "cpf_cnpj": _cpf_aleatorio(),
        "telefone": "11999998888",
        "email": f"cliente-{uuid.uuid4().hex[:8]}@example.com",
    }
    payload.update(overrides)
    response = await client.post(_BASE_CLIENTES, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar cliente: {response.status_code} — {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Criação de veículos
# ---------------------------------------------------------------------------


async def criar_veiculo(
    client: AsyncClient,
    headers: dict,
    cliente_id: str,
    **overrides,
) -> dict:
    """Cria veículo associado ao cliente e retorna JSON criado."""
    payload = {
        "cliente_id": cliente_id,
        "placa": _placa_aleatoria(),
        "marca": "Toyota",
        "modelo": "Corolla",
        "ano_fabricacao": 2020,
        "ano_modelo": 2021,
        "cor": "Prata",
    }
    payload.update(overrides)
    response = await client.post(_BASE_VEICULOS, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar veículo: {response.status_code} — {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Criação de serviços
# ---------------------------------------------------------------------------


async def criar_servico(
    client: AsyncClient,
    headers: dict,
    **overrides,
) -> dict:
    """Cria serviço e retorna JSON criado."""
    payload = {
        "nome": _nome_unico("Serviço OS"),
        "descricao": "Serviço de teste para OS",
        "valor_base": "150.00",
        "tempo_medio_minutos": 60,
        "ativo": True,
    }
    payload.update(overrides)
    response = await client.post(_BASE_SERVICOS, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar serviço: {response.status_code} — {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Criação de itens de estoque
# ---------------------------------------------------------------------------


async def criar_item_estoque(
    client: AsyncClient,
    headers: dict,
    **overrides,
) -> dict:
    """Cria item de estoque e retorna JSON criado."""
    payload = {
        "tipo": "PECA",
        "nome": _nome_unico("Item OS"),
        "descricao": "Item de estoque para OS",
        "codigo": _codigo_unico(),
        "quantidade_disponivel": 10,
        "quantidade_minima": 2,
        "valor_unitario": "35.00",
    }
    payload.update(overrides)
    response = await client.post(_BASE_ITENS, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar item de estoque: {response.status_code} — {response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# Criação de Ordens de Serviço
# ---------------------------------------------------------------------------


async def criar_ordem_servico(
    client: AsyncClient,
    headers: dict,
    cliente_id: str,
    veiculo_id: str,
    **overrides,
) -> dict:
    """Cria OS e retorna JSON criado."""
    payload = {
        "cliente_id": cliente_id,
        "veiculo_id": veiculo_id,
        "queixa_inicial": "Barulho estranho ao frear",
    }
    payload.update(overrides)
    response = await client.post(_BASE_OS, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar OS: {response.status_code} — {response.text}"
    )
    return response.json()


async def criar_os_recebida(
    client: AsyncClient,
    admin_headers: dict,
) -> dict:
    """
    Cria cliente, veículo e OS.
    Retorna: {cliente, veiculo, ordem_servico}
    """
    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    os_ = await criar_ordem_servico(
        client, admin_headers, cliente["id"], veiculo["id"]
    )
    return {"cliente": cliente, "veiculo": veiculo, "ordem_servico": os_}


async def criar_os_em_diagnostico(
    client: AsyncClient,
    admin_headers: dict,
    mecanico_headers: dict | None = None,
) -> dict:
    """
    Cria OS recebida e inicia diagnóstico.
    Retorna: {cliente, veiculo, ordem_servico, mecanico_headers}
    """
    dados = await criar_os_recebida(client, admin_headers)

    if mecanico_headers is None:
        mec = await criar_mecanico(client, admin_headers)
        mecanico_headers = mec["headers"]

    os_id = dados["ordem_servico"]["id"]
    response = await client.patch(
        f"{_BASE_OS}/{os_id}/iniciar-diagnostico",
        headers=mecanico_headers,
    )
    assert response.status_code == 200, (
        f"Erro ao iniciar diagnóstico: {response.status_code} — {response.text}"
    )
    dados["ordem_servico"] = response.json()
    dados["mecanico_headers"] = mecanico_headers
    return dados


async def criar_os_com_diagnostico(
    client: AsyncClient,
    admin_headers: dict,
    mecanico_headers: dict | None = None,
) -> dict:
    """
    Cria OS em diagnóstico e registra o texto do diagnóstico.
    Retorna: {cliente, veiculo, ordem_servico, mecanico_headers}
    """
    dados = await criar_os_em_diagnostico(client, admin_headers, mecanico_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    response = await client.patch(
        f"{_BASE_OS}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas de freio"},
        headers=mecanico_headers,
    )
    assert response.status_code == 200, (
        f"Erro ao registrar diagnóstico: {response.status_code} — {response.text}"
    )
    dados["ordem_servico"] = response.json()
    return dados


async def criar_os_com_servico(
    client: AsyncClient,
    admin_headers: dict,
    mecanico_headers: dict | None = None,
) -> dict:
    """
    Cria OS com diagnóstico registrado e adiciona um serviço.
    Retorna: {cliente, veiculo, ordem_servico, servico, ordem_servico_servico, mecanico_headers}
    """
    dados = await criar_os_com_diagnostico(client, admin_headers, mecanico_headers)
    os_id = dados["ordem_servico"]["id"]
    mecanico_headers = dados["mecanico_headers"]

    servico = await criar_servico(client, admin_headers)
    response = await client.post(
        f"{_BASE_OS}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico_headers,
    )
    assert response.status_code == 201, (
        f"Erro ao adicionar serviço: {response.status_code} — {response.text}"
    )
    dados["servico"] = servico
    dados["ordem_servico_servico"] = response.json()
    return dados


async def criar_os_pronta_para_concluir_diagnostico(
    client: AsyncClient,
    admin_headers: dict,
    mecanico_headers: dict | None = None,
) -> dict:
    """
    Cria OS com diagnóstico e pelo menos um serviço ativo — pronta para concluir.
    Retorna: {cliente, veiculo, ordem_servico, servico, ordem_servico_servico, mecanico_headers}
    """
    return await criar_os_com_servico(client, admin_headers, mecanico_headers)


async def criar_os_diagnostico_concluido_para_orcamento(
    client: AsyncClient,
    admin_headers: dict,
) -> dict:
    """
    Cria uma OS completa com diagnóstico concluído, pronta para geração de orçamento.

    Fluxo:
      1. Cria atendente e mecânico dedidados.
      2. Cria cliente (com telefone e e-mail) e veículo.
      3. Cria serviço com valor_base=180.00.
      4. Cria dois itens de estoque:
         - item_com_saldo:  quantidade_disponivel=10, valor_unitario=85.00
         - item_sem_saldo:  quantidade_disponivel=0,  valor_unitario=220.00
      5. Cria OS → inicia diagnóstico → registra diagnóstico → adiciona serviço
         → adiciona item_com_saldo (qtd=2, status RESERVADO)
         → adiciona item_sem_saldo (qtd=1, status A_RECEBER)
         → conclui diagnóstico.

    Totais esperados:
      total_servicos = 180.00
      total_itens    = 85.00 × 2 + 220.00 × 1 = 390.00
      total_geral    = 570.00

    Retorna:
      {
        atendente, atendente_headers,
        mecanico, mecanico_headers,
        cliente, veiculo,
        servico,
        item_com_saldo, item_sem_saldo,
        ordem_servico,
        ordem_servico_servico,
        ordem_servico_item_reservado,
        ordem_servico_item_a_receber,
      }
    """
    from tests.integration.ordens_servico.factories import (
        criar_atendente,
        criar_mecanico,
        criar_cliente,
        criar_veiculo,
        criar_servico,
        criar_item_estoque,
        criar_ordem_servico,
    )

    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    cliente = await criar_cliente(client, admin_headers)
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])

    servico = await criar_servico(
        client, admin_headers, valor_base="180.00", tempo_medio_minutos=60
    )
    item_com_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=10, valor_unitario="85.00"
    )
    item_sem_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=0, valor_unitario="220.00"
    )

    os_id_response = await criar_ordem_servico(
        client, atendente["headers"], cliente["id"], veiculo["id"]
    )
    os_id = os_id_response["id"]

    # Iniciar diagnóstico
    r = await client.patch(
        f"{_BASE_OS}/{os_id}/iniciar-diagnostico",
        headers=mecanico["headers"],
    )
    assert r.status_code == 200, f"iniciar-diagnostico: {r.status_code} — {r.text}"

    # Registrar texto do diagnóstico
    r = await client.patch(
        f"{_BASE_OS}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas de freio"},
        headers=mecanico["headers"],
    )
    assert r.status_code == 200, f"registrar-diagnostico: {r.status_code} — {r.text}"

    # Adicionar serviço
    r = await client.post(
        f"{_BASE_OS}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201, f"adicionar-servico: {r.status_code} — {r.text}"
    os_servico = r.json()

    # Adicionar item com saldo (quantidade=2 → RESERVADO)
    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_com_saldo["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201, f"adicionar-item-com-saldo: {r.status_code} — {r.text}"
    os_item_reservado = r.json()

    # Adicionar item sem saldo (quantidade=1 → A_RECEBER)
    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_sem_saldo["id"], "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201, f"adicionar-item-sem-saldo: {r.status_code} — {r.text}"
    os_item_a_receber = r.json()

    # Concluir diagnóstico
    r = await client.patch(
        f"{_BASE_OS}/{os_id}/concluir-diagnostico",
        headers=mecanico["headers"],
    )
    assert r.status_code == 200, f"concluir-diagnostico: {r.status_code} — {r.text}"
    ordem_servico = r.json()

    return {
        "atendente": atendente,
        "atendente_headers": atendente["headers"],
        "mecanico": mecanico,
        "mecanico_headers": mecanico["headers"],
        "cliente": cliente,
        "veiculo": veiculo,
        "servico": servico,
        "item_com_saldo": item_com_saldo,
        "item_sem_saldo": item_sem_saldo,
        "ordem_servico": ordem_servico,
        "ordem_servico_servico": os_servico,
        "ordem_servico_item_reservado": os_item_reservado,
        "ordem_servico_item_a_receber": os_item_a_receber,
    }


# ---------------------------------------------------------------------------
# Helpers para aprovação / recusa de orçamento
# ---------------------------------------------------------------------------


async def gerar_orcamento(
    client: AsyncClient,
    headers: dict,
    os_id: str,
    observacao: str | None = None,
) -> dict:
    """Gera orçamento para a OS e retorna o JSON do orçamento."""
    payload: dict = {}
    if observacao is not None:
        payload["observacao"] = observacao
    r = await client.post(f"{_BASE_OS}/{os_id}/orcamento", json=payload, headers=headers)
    assert r.status_code == 201, f"gerar_orcamento falhou: {r.status_code} — {r.text}"
    return r.json()


async def criar_os_com_orcamento_comunicado_todos_itens_reservados(
    client: AsyncClient,
    admin_headers: dict,
) -> dict:
    """
    Prepara OS com orçamento COMUNICADO, todos os itens RESERVADO.

    Configuração:
      - serviço: valor_base = 180.00
      - item_com_saldo: disponível=10, reservado=0, valor_unitario=85.00
      - item na OS: quantidade=2 → RESERVADO
      - estoque após reserva: disponível=8, reservado=2
      - total_servicos=180.00, total_itens=170.00, total_geral=350.00

    Retorna:
      {
        atendente, atendente_headers,
        mecanico, mecanico_headers,
        cliente, veiculo, servico, item_com_saldo,
        ordem_servico, orcamento,
        ordem_servico_item_reservado,
      }
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    cliente = await criar_cliente(
        client, admin_headers,
        telefone="11999990001",
        email=f"cliente-res-{uuid.uuid4().hex[:8]}@example.com",
    )
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    servico = await criar_servico(client, admin_headers, valor_base="180.00")
    item_com_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=10,
        valor_unitario="85.00",
    )

    os_ = await criar_ordem_servico(client, atendente["headers"], cliente["id"], veiculo["id"])
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS}/{os_id}/iniciar-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200

    r = await client.patch(
        f"{_BASE_OS}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas"},
        headers=mecanico["headers"],
    )
    assert r.status_code == 200

    r = await client.post(
        f"{_BASE_OS}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201

    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_com_saldo["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_reservado = r.json()

    r = await client.patch(f"{_BASE_OS}/{os_id}/concluir-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200
    ordem_servico = r.json()

    orcamento = await gerar_orcamento(client, atendente["headers"], os_id)

    return {
        "atendente": atendente,
        "atendente_headers": atendente["headers"],
        "mecanico": mecanico,
        "mecanico_headers": mecanico["headers"],
        "cliente": cliente,
        "veiculo": veiculo,
        "servico": servico,
        "item_com_saldo": item_com_saldo,
        "ordem_servico": ordem_servico,
        "orcamento": orcamento,
        "ordem_servico_item_reservado": os_item_reservado,
    }


async def criar_os_com_orcamento_comunicado_com_item_a_receber(
    client: AsyncClient,
    admin_headers: dict,
) -> dict:
    """
    Prepara OS com orçamento COMUNICADO e item A_RECEBER.

    Configuração:
      - serviço: valor_base = 180.00
      - item_sem_saldo: disponível=0, valor_unitario=220.00
      - item na OS: quantidade=1 → A_RECEBER
      - total_servicos=180.00, total_itens=220.00, total_geral=400.00

    Retorna:
      {
        atendente, atendente_headers,
        mecanico, mecanico_headers,
        cliente, veiculo, servico, item_sem_saldo,
        ordem_servico, orcamento,
        ordem_servico_item_a_receber,
      }
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    cliente = await criar_cliente(
        client, admin_headers,
        telefone="11999990002",
        email=f"cliente-arec-{uuid.uuid4().hex[:8]}@example.com",
    )
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    servico = await criar_servico(client, admin_headers, valor_base="180.00")
    item_sem_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=0,
        valor_unitario="220.00",
    )

    os_ = await criar_ordem_servico(client, atendente["headers"], cliente["id"], veiculo["id"])
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS}/{os_id}/iniciar-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200

    r = await client.patch(
        f"{_BASE_OS}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas"},
        headers=mecanico["headers"],
    )
    assert r.status_code == 200

    r = await client.post(
        f"{_BASE_OS}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201

    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_sem_saldo["id"], "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_a_receber = r.json()

    r = await client.patch(f"{_BASE_OS}/{os_id}/concluir-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200
    ordem_servico = r.json()

    orcamento = await gerar_orcamento(client, atendente["headers"], os_id)

    return {
        "atendente": atendente,
        "atendente_headers": atendente["headers"],
        "mecanico": mecanico,
        "mecanico_headers": mecanico["headers"],
        "cliente": cliente,
        "veiculo": veiculo,
        "servico": servico,
        "item_sem_saldo": item_sem_saldo,
        "ordem_servico": ordem_servico,
        "orcamento": orcamento,
        "ordem_servico_item_a_receber": os_item_a_receber,
    }


async def criar_os_com_orcamento_comunicado_misto(
    client: AsyncClient,
    admin_headers: dict,
) -> dict:
    """
    Prepara OS com orçamento COMUNICADO, item RESERVADO + item A_RECEBER.

    Configuração:
      - serviço: valor_base = 180.00
      - item_com_saldo: disponível=10, valor_unitario=85.00 → quantidade=2 → RESERVADO
      - item_sem_saldo: disponível=0, valor_unitario=220.00 → quantidade=1 → A_RECEBER
      - estoque após reserva: disponível=8, reservado=2
      - total_servicos=180.00, total_itens=390.00, total_geral=570.00

    Retorna:
      {
        atendente, atendente_headers,
        mecanico, mecanico_headers,
        cliente, veiculo, servico,
        item_com_saldo, item_sem_saldo,
        ordem_servico, orcamento,
        ordem_servico_item_reservado, ordem_servico_item_a_receber,
      }
    """
    atendente = await criar_atendente(client, admin_headers)
    mecanico = await criar_mecanico(client, admin_headers)

    cliente = await criar_cliente(
        client, admin_headers,
        telefone="11999990003",
        email=f"cliente-misto-{uuid.uuid4().hex[:8]}@example.com",
    )
    veiculo = await criar_veiculo(client, admin_headers, cliente["id"])
    servico = await criar_servico(client, admin_headers, valor_base="180.00")
    item_com_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=10,
        valor_unitario="85.00",
    )
    item_sem_saldo = await criar_item_estoque(
        client, admin_headers,
        quantidade_disponivel=0,
        valor_unitario="220.00",
    )

    os_ = await criar_ordem_servico(client, atendente["headers"], cliente["id"], veiculo["id"])
    os_id = os_["id"]

    r = await client.patch(f"{_BASE_OS}/{os_id}/iniciar-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200

    r = await client.patch(
        f"{_BASE_OS}/{os_id}/diagnostico",
        json={"diagnostico": "Desgaste nas pastilhas"},
        headers=mecanico["headers"],
    )
    assert r.status_code == 200

    r = await client.post(
        f"{_BASE_OS}/{os_id}/servicos",
        json={"servico_id": servico["id"], "observacao": None},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201

    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_com_saldo["id"], "quantidade": 2},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_reservado = r.json()

    r = await client.post(
        f"{_BASE_OS}/{os_id}/itens",
        json={"item_estoque_id": item_sem_saldo["id"], "quantidade": 1},
        headers=mecanico["headers"],
    )
    assert r.status_code == 201
    os_item_a_receber = r.json()

    r = await client.patch(f"{_BASE_OS}/{os_id}/concluir-diagnostico", headers=mecanico["headers"])
    assert r.status_code == 200
    ordem_servico = r.json()

    orcamento = await gerar_orcamento(client, atendente["headers"], os_id)

    return {
        "atendente": atendente,
        "atendente_headers": atendente["headers"],
        "mecanico": mecanico,
        "mecanico_headers": mecanico["headers"],
        "cliente": cliente,
        "veiculo": veiculo,
        "servico": servico,
        "item_com_saldo": item_com_saldo,
        "item_sem_saldo": item_sem_saldo,
        "ordem_servico": ordem_servico,
        "orcamento": orcamento,
        "ordem_servico_item_reservado": os_item_reservado,
        "ordem_servico_item_a_receber": os_item_a_receber,
    }
