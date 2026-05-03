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
