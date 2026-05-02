"""
Testes de integração — módulo Veículos.

Baseados nos cenários de tests/dev/modules/veiculo/veiculo.http.
Cada teste cria seus próprios dados (cliente, veículo, usuário).
Nenhum teste depende de outro. Nenhum JWT e nenhum ID são hardcoded.

Regras de placa (value object Placa):
  Regex: ^[A-Z]{3}[0-9]{1}[A-Z0-9]{1}[0-9]{2}$
  Padrão antigo:  ABC1234  (posição 4 = dígito, posição 5 = dígito)
  Padrão Mercosul: ABC1D23 (posição 4 = dígito, posição 5 = letra)

Permissões: Administrador e Atendente podem criar/listar/consultar/atualizar/remover.
Delete: físico — 204 + 404 após.
"""

import random
import string
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers — placa
# ---------------------------------------------------------------------------

def _placa_aleatoria() -> str:
    """
    Gera placa aleatória no formato Mercosul: ABC1D23.
    Regex do domínio: ^[A-Z]{3}[0-9]{1}[A-Z0-9]{1}[0-9]{2}$
    """
    letras = string.ascii_uppercase
    return (
        random.choice(letras)
        + random.choice(letras)
        + random.choice(letras)
        + str(random.randint(0, 9))
        + random.choice(letras)          # posição 5 = letra → Mercosul
        + str(random.randint(0, 9))
        + str(random.randint(0, 9))
    )


# ---------------------------------------------------------------------------
# Helpers — CPF/CNPJ para clientes
# ---------------------------------------------------------------------------

def _cpf_aleatorio() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(11))


def _cnpj_aleatorio() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(14))


# ---------------------------------------------------------------------------
# Helpers — payloads e criação
# ---------------------------------------------------------------------------

def _extrair_items(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    raise AssertionError(f"Formato inesperado de resposta: {payload}")


async def _criar_cliente(client: AsyncClient, headers: dict) -> dict:
    """Cria um cliente PF e retorna o body da resposta."""
    payload = {
        "tipo_pessoa": "PF",
        "nome_razao_social": f"Cliente Veiculo {uuid.uuid4().hex[:6]}",
        "cpf_cnpj": _cpf_aleatorio(),
        "telefone": "11999998888",
    }
    response = await client.post("/api/v1/clientes", json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar cliente: {response.status_code} — {response.text}"
    )
    return response.json()


async def _criar_veiculo(
    client: AsyncClient, headers: dict, cliente_id: str, **override
) -> dict:
    """Cria um veículo associado ao cliente e retorna o body da resposta."""
    payload = {
        "cliente_id": cliente_id,
        "placa": _placa_aleatoria(),
        "marca": "Toyota",
        "modelo": "Corolla",
        "ano_fabricacao": 2020,
        "ano_modelo": 2021,
        "cor": "Prata",
    }
    payload.update(override)
    response = await client.post("/api/v1/veiculos", json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar veículo: {response.status_code} — {response.text}"
    )
    return response.json()


async def _criar_atendente_e_autenticar(
    client: AsyncClient, admin_headers: dict
) -> dict:
    """
    Cria usuário com perfil Atendente via admin e autentica.
    Retorna headers prontos para uso.
    """
    email = f"atendente-veiculo-{uuid.uuid4().hex[:8]}@example.com"
    senha = "senha123"

    resp = await client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Atendente Veiculos",
            "email": email,
            "senha": senha,
            "perfis": ["Atendente"],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, (
        f"Falha ao criar atendente: {resp.status_code} — {resp.text}"
    )

    resp_token = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": senha},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp_token.status_code == 200, (
        f"Falha ao autenticar atendente: {resp_token.text}"
    )
    return {"Authorization": f"Bearer {resp_token.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

async def test_nao_deve_criar_veiculo_sem_autenticacao(
    client: AsyncClient, admin_headers: dict
):
    """POST /api/v1/veiculos sem Authorization deve retornar 401 ou 403.
    Cria cliente previamente porque a API pode validar auth antes do body.
    """
    cliente = await _criar_cliente(client, admin_headers)
    payload = {
        "cliente_id": cliente["id"],
        "placa": _placa_aleatoria(),
        "marca": "Fiat",
        "modelo": "Uno",
    }
    response = await client.post("/api/v1/veiculos", json=payload)
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Criação — Admin
# ---------------------------------------------------------------------------

async def test_admin_deve_criar_veiculo(
    client: AsyncClient, admin_headers: dict
):
    """Admin cria veículo associado a cliente — espera 201 com campos corretos."""
    cliente = await _criar_cliente(client, admin_headers)
    placa = _placa_aleatoria()

    veiculo = await _criar_veiculo(
        client, admin_headers, cliente["id"], placa=placa, marca="Honda", modelo="Civic"
    )

    assert "id" in veiculo
    assert veiculo["placa"] == placa
    assert veiculo["marca"] == "Honda"
    assert veiculo["modelo"] == "Civic"
    assert veiculo["cliente_id"] == cliente["id"]


# ---------------------------------------------------------------------------
# Criação — Atendente (fluxo de negócio principal)
# ---------------------------------------------------------------------------

async def test_atendente_deve_criar_veiculo(
    client: AsyncClient, admin_headers: dict
):
    """
    Fluxo de negócio do atendimento inicial:
    Atendente cria cliente PF e cadastra o veículo do cliente.
    """
    atendente_headers = await _criar_atendente_e_autenticar(client, admin_headers)

    # Atendente cria o cliente
    cliente = await _criar_cliente(client, atendente_headers)

    # Atendente cria o veículo vinculado ao cliente
    placa = _placa_aleatoria()
    veiculo = await _criar_veiculo(
        client, atendente_headers, cliente["id"],
        placa=placa, marca="Volkswagen", modelo="Gol"
    )

    assert "id" in veiculo
    assert veiculo["placa"] == placa
    assert veiculo["cliente_id"] == cliente["id"]
    assert veiculo["marca"] == "Volkswagen"
    assert veiculo["modelo"] == "Gol"


# ---------------------------------------------------------------------------
# Listagem — Admin e Atendente
# ---------------------------------------------------------------------------

async def test_admin_deve_listar_veiculos(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/veiculos deve retornar 200 contendo o veículo recém-criado."""
    cliente = await _criar_cliente(client, admin_headers)
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"])

    response = await client.get("/api/v1/veiculos", headers=admin_headers)
    assert response.status_code == 200
    ids = [v["id"] for v in _extrair_items(response.json())]
    assert veiculo["id"] in ids


async def test_atendente_deve_listar_veiculos(
    client: AsyncClient, admin_headers: dict
):
    """
    Atendente cria cliente e veículo e confirma que aparecem na listagem.
    Valida o fluxo completo do perfil Atendente no domínio.
    """
    atendente_headers = await _criar_atendente_e_autenticar(client, admin_headers)

    cliente = await _criar_cliente(client, atendente_headers)
    veiculo = await _criar_veiculo(client, atendente_headers, cliente["id"])

    response = await client.get("/api/v1/veiculos", headers=atendente_headers)
    assert response.status_code == 200
    ids = [v["id"] for v in _extrair_items(response.json())]
    assert veiculo["id"] in ids


# ---------------------------------------------------------------------------
# Busca por ID
# ---------------------------------------------------------------------------

async def test_admin_deve_buscar_veiculo_por_id(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/veiculos/{id} deve retornar o veículo correto."""
    cliente = await _criar_cliente(client, admin_headers)
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"])
    veiculo_id = veiculo["id"]

    response = await client.get(f"/api/v1/veiculos/{veiculo_id}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == veiculo_id
    assert body["placa"] == veiculo["placa"]
    assert body["cliente_id"] == cliente["id"]


async def test_deve_retornar_404_para_veiculo_inexistente(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/veiculos/{uuid_inexistente} deve retornar 404."""
    response = await client.get(
        f"/api/v1/veiculos/{uuid.uuid4()}", headers=admin_headers
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------

async def test_admin_deve_filtrar_veiculo_por_placa(
    client: AsyncClient, admin_headers: dict
):
    """GET ?placa=<placa> deve retornar o veículo com essa placa."""
    cliente = await _criar_cliente(client, admin_headers)
    placa = _placa_aleatoria()
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"], placa=placa)

    response = await client.get(f"/api/v1/veiculos?placa={placa}", headers=admin_headers)
    assert response.status_code == 200
    placas = [v["placa"] for v in _extrair_items(response.json())]
    assert placa in placas


async def test_admin_deve_filtrar_veiculo_por_cliente_id(
    client: AsyncClient, admin_headers: dict
):
    """GET ?cliente_id=<id> deve retornar apenas veículos desse cliente."""
    cliente = await _criar_cliente(client, admin_headers)
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"])

    response = await client.get(
        f"/api/v1/veiculos?cliente_id={cliente['id']}", headers=admin_headers
    )
    assert response.status_code == 200
    items = _extrair_items(response.json())
    ids = [v["id"] for v in items]
    assert veiculo["id"] in ids
    # Todos os veículos retornados pertencem ao cliente
    assert all(v["cliente_id"] == cliente["id"] for v in items)


async def test_admin_deve_filtrar_veiculo_por_marca(
    client: AsyncClient, admin_headers: dict
):
    """GET ?marca=<marca> deve retornar veículos com essa marca."""
    cliente = await _criar_cliente(client, admin_headers)
    marca = f"MarcaTeste{uuid.uuid4().hex[:4].upper()}"
    veiculo = await _criar_veiculo(
        client, admin_headers, cliente["id"], marca=marca, modelo="ModeloX"
    )

    response = await client.get(f"/api/v1/veiculos?marca={marca}", headers=admin_headers)
    assert response.status_code == 200
    items = _extrair_items(response.json())
    marcas = [v["marca"] for v in items]
    assert marca in marcas


# ---------------------------------------------------------------------------
# Validações de criação
# ---------------------------------------------------------------------------

async def test_nao_deve_criar_veiculo_com_placa_invalida(
    client: AsyncClient, admin_headers: dict
):
    """POST com placa fora do padrão deve retornar 400 ou 422."""
    cliente = await _criar_cliente(client, admin_headers)
    payload = {
        "cliente_id": cliente["id"],
        "placa": "INVALIDA",  # não bate com regex ^[A-Z]{3}[0-9]{1}[A-Z0-9]{1}[0-9]{2}$
        "marca": "Fiat",
        "modelo": "Uno",
    }
    response = await client.post("/api/v1/veiculos", json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_veiculo_com_placa_duplicada(
    client: AsyncClient, admin_headers: dict
):
    """Segundo POST com mesma placa deve retornar 409."""
    cliente = await _criar_cliente(client, admin_headers)
    placa = _placa_aleatoria()
    await _criar_veiculo(client, admin_headers, cliente["id"], placa=placa)

    response = await client.post(
        "/api/v1/veiculos",
        json={
            "cliente_id": cliente["id"],
            "placa": placa,
            "marca": "Ford",
            "modelo": "Ka",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


async def test_nao_deve_criar_veiculo_para_cliente_inexistente(
    client: AsyncClient, admin_headers: dict
):
    """POST com cliente_id inexistente deve retornar 404."""
    payload = {
        "cliente_id": str(uuid.uuid4()),
        "placa": _placa_aleatoria(),
        "marca": "Chevrolet",
        "modelo": "Onix",
    }
    response = await client.post("/api/v1/veiculos", json=payload, headers=admin_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

async def test_admin_deve_atualizar_veiculo(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /api/v1/veiculos/{id} deve atualizar os campos enviados."""
    cliente = await _criar_cliente(client, admin_headers)
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"])
    veiculo_id = veiculo["id"]

    response = await client.patch(
        f"/api/v1/veiculos/{veiculo_id}",
        json={"marca": "Renault", "modelo": "Kwid", "cor": "Vermelho"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["marca"] == "Renault"
    assert body["modelo"] == "Kwid"
    assert body["cor"] == "Vermelho"


# ---------------------------------------------------------------------------
# Remoção física
# ---------------------------------------------------------------------------

async def test_admin_deve_remover_veiculo_fisicamente(
    client: AsyncClient, admin_headers: dict
):
    """DELETE /api/v1/veiculos/{id} → 204; GET posterior → 404."""
    cliente = await _criar_cliente(client, admin_headers)
    veiculo = await _criar_veiculo(client, admin_headers, cliente["id"])
    veiculo_id = veiculo["id"]

    resp_delete = await client.delete(
        f"/api/v1/veiculos/{veiculo_id}", headers=admin_headers
    )
    assert resp_delete.status_code == 204

    resp_get = await client.get(
        f"/api/v1/veiculos/{veiculo_id}", headers=admin_headers
    )
    assert resp_get.status_code == 404
