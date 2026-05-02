"""
Testes de integração — módulo Clientes.

Baseados nos cenários de tests/dev/modules/cliente/cliente.http.
Cada teste cria seus próprios dados. Nenhum teste depende de outro.
Nenhum JWT e nenhum ID são hardcoded.
"""

import random
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers — documento
# ---------------------------------------------------------------------------

def _cpf_aleatorio() -> str:
    """Gera 11 dígitos numéricos aleatórios (API valida apenas comprimento)."""
    return "".join(str(random.randint(0, 9)) for _ in range(11))


def _cnpj_aleatorio() -> str:
    """Gera 14 dígitos numéricos aleatórios (API valida apenas comprimento)."""
    return "".join(str(random.randint(0, 9)) for _ in range(14))


def _nome_unico(base: str = "Cliente Teste") -> str:
    return f"{base} {uuid.uuid4().hex[:6]}"


# ---------------------------------------------------------------------------
# Helpers — payloads e criação
# ---------------------------------------------------------------------------

def _payload_pf(**override) -> dict:
    base = {
        "tipo_pessoa": "PF",
        "nome_razao_social": _nome_unico("Joao da Silva"),
        "cpf_cnpj": _cpf_aleatorio(),
        "telefone": "11999998888",
        "email": f"joao-{uuid.uuid4().hex[:6]}@example.com",
        "cep": "01001000",
        "logradouro": "Praca da Se",
        "numero": "100",
        "bairro": "Se",
        "cidade": "Sao Paulo",
        "uf": "SP",
    }
    base.update(override)
    return base


def _payload_pj(**override) -> dict:
    base = {
        "tipo_pessoa": "PJ",
        "nome_razao_social": _nome_unico("Empresa LTDA"),
        "cpf_cnpj": _cnpj_aleatorio(),
        "telefone": "1133334444",
        "email": f"empresa-{uuid.uuid4().hex[:6]}@example.com",
        "cep": "01310000",
        "logradouro": "Avenida Paulista",
        "numero": "1000",
        "bairro": "Bela Vista",
        "cidade": "Sao Paulo",
        "uf": "SP",
    }
    base.update(override)
    return base


async def _criar_cliente(client: AsyncClient, admin_headers: dict, payload: dict) -> dict:
    response = await client.post("/api/v1/clientes", json=payload, headers=admin_headers)
    assert response.status_code == 201, (
        f"Erro ao criar cliente: {response.status_code} — {response.text}"
    )
    return response.json()


def _extrair_items(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    raise AssertionError(f"Formato inesperado de resposta: {payload}")


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

async def test_nao_deve_criar_cliente_sem_autenticacao(client: AsyncClient):
    """POST /api/v1/clientes sem Authorization deve retornar 401 ou 403."""
    response = await client.post("/api/v1/clientes", json=_payload_pf())
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------

async def test_admin_deve_criar_cliente_pessoa_fisica(
    client: AsyncClient, admin_headers: dict
):
    """POST com PF válida deve retornar 201 com campos corretos."""
    payload = _payload_pf()
    body = await _criar_cliente(client, admin_headers, payload)

    assert "id" in body
    assert body["tipo_pessoa"] == "PF"
    assert body["nome_razao_social"] == payload["nome_razao_social"]
    assert body["cpf_cnpj"] == payload["cpf_cnpj"]
    assert body["ativo"] is True


async def test_admin_deve_criar_cliente_pessoa_juridica(
    client: AsyncClient, admin_headers: dict
):
    """POST com PJ válida deve retornar 201 com campos corretos."""
    payload = _payload_pj()
    body = await _criar_cliente(client, admin_headers, payload)

    assert "id" in body
    assert body["tipo_pessoa"] == "PJ"
    assert body["nome_razao_social"] == payload["nome_razao_social"]
    assert body["cpf_cnpj"] == payload["cpf_cnpj"]
    assert body["ativo"] is True


async def test_nao_deve_criar_cliente_com_documento_invalido(
    client: AsyncClient, admin_headers: dict
):
    """POST com CPF de tamanho inválido deve retornar 400 ou 422."""
    payload = _payload_pf(cpf_cnpj="123")  # 3 dígitos — inválido
    response = await client.post("/api/v1/clientes", json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_cliente_com_documento_duplicado(
    client: AsyncClient, admin_headers: dict
):
    """Segundo POST com mesmo CPF/CNPJ deve retornar 409."""
    cpf = _cpf_aleatorio()
    await _criar_cliente(client, admin_headers, _payload_pf(cpf_cnpj=cpf))

    response = await client.post(
        "/api/v1/clientes",
        json=_payload_pf(cpf_cnpj=cpf, nome_razao_social="Duplicado"),
        headers=admin_headers,
    )
    assert response.status_code == 409


async def test_nao_deve_criar_cliente_com_tipo_pessoa_invalido(
    client: AsyncClient, admin_headers: dict
):
    """POST com tipo_pessoa inválido deve retornar 400 ou 422."""
    response = await client.post(
        "/api/v1/clientes",
        json=_payload_pf(tipo_pessoa="XX"),
        headers=admin_headers,
    )
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Listagem e filtros
# ---------------------------------------------------------------------------

async def test_admin_deve_listar_clientes(client: AsyncClient, admin_headers: dict):
    """GET /api/v1/clientes deve retornar 200 contendo o cliente recém-criado."""
    criado = await _criar_cliente(client, admin_headers, _payload_pf())

    response = await client.get("/api/v1/clientes", headers=admin_headers)
    assert response.status_code == 200
    ids = [c["id"] for c in _extrair_items(response.json())]
    assert criado["id"] in ids


async def test_admin_deve_filtrar_cliente_por_cpf_cnpj(
    client: AsyncClient, admin_headers: dict
):
    """GET ?cpf_cnpj=<doc> deve retornar o cliente com esse documento."""
    cpf = _cpf_aleatorio()
    criado = await _criar_cliente(client, admin_headers, _payload_pf(cpf_cnpj=cpf))

    response = await client.get(f"/api/v1/clientes?cpf_cnpj={cpf}", headers=admin_headers)
    assert response.status_code == 200
    docs = [c["cpf_cnpj"] for c in _extrair_items(response.json())]
    assert cpf in docs


async def test_admin_deve_filtrar_cliente_por_nome(
    client: AsyncClient, admin_headers: dict
):
    """GET ?nome=<nome> deve retornar o cliente com esse nome."""
    nome = _nome_unico("NomeUnico")
    await _criar_cliente(client, admin_headers, _payload_pf(nome_razao_social=nome))

    response = await client.get(f"/api/v1/clientes?nome={nome}", headers=admin_headers)
    assert response.status_code == 200
    nomes = [c["nome_razao_social"] for c in _extrair_items(response.json())]
    assert any(nome in n for n in nomes)


async def test_admin_deve_filtrar_clientes_ativos(
    client: AsyncClient, admin_headers: dict
):
    """GET ?ativo=true deve retornar apenas clientes ativos."""
    await _criar_cliente(client, admin_headers, _payload_pf())

    response = await client.get("/api/v1/clientes?ativo=true", headers=admin_headers)
    assert response.status_code == 200
    items = _extrair_items(response.json())
    assert all(c["ativo"] is True for c in items)


# ---------------------------------------------------------------------------
# Busca por ID
# ---------------------------------------------------------------------------

async def test_admin_deve_buscar_cliente_por_id(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/clientes/{id} deve retornar o cliente correto."""
    criado = await _criar_cliente(client, admin_headers, _payload_pf())
    cliente_id = criado["id"]

    response = await client.get(f"/api/v1/clientes/{cliente_id}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == cliente_id
    assert body["cpf_cnpj"] == criado["cpf_cnpj"]


async def test_deve_retornar_404_para_id_inexistente(
    client: AsyncClient, admin_headers: dict
):
    """GET /api/v1/clientes/{uuid_inexistente} deve retornar 404."""
    response = await client.get(
        f"/api/v1/clientes/{uuid.uuid4()}", headers=admin_headers
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

async def test_admin_deve_atualizar_cliente(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /api/v1/clientes/{id} deve atualizar os campos enviados."""
    criado = await _criar_cliente(client, admin_headers, _payload_pf())
    cliente_id = criado["id"]

    novo_nome = _nome_unico("Nome Atualizado")
    response = await client.patch(
        f"/api/v1/clientes/{cliente_id}",
        json={"nome_razao_social": novo_nome, "telefone": "11977776666"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nome_razao_social"] == novo_nome
    assert body["telefone"] == "11977776666"


# ---------------------------------------------------------------------------
# Ativar / Desativar
# ---------------------------------------------------------------------------

async def test_admin_deve_desativar_e_ativar_cliente(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /desativar → ativo=false; PATCH /ativar → ativo=true."""
    criado = await _criar_cliente(client, admin_headers, _payload_pf())
    cliente_id = criado["id"]

    # Desativar
    resp = await client.patch(
        f"/api/v1/clientes/{cliente_id}/desativar", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["ativo"] is False

    # Confirmar via filtro ativo=false
    resp_inativos = await client.get("/api/v1/clientes?ativo=false", headers=admin_headers)
    assert resp_inativos.status_code == 200
    ids_inativos = [c["id"] for c in _extrair_items(resp_inativos.json())]
    assert cliente_id in ids_inativos

    # Ativar
    resp = await client.patch(
        f"/api/v1/clientes/{cliente_id}/ativar", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["ativo"] is True


# ---------------------------------------------------------------------------
# Atendente — fluxo completo de negócio
# ---------------------------------------------------------------------------

async def test_atendente_deve_criar_e_listar_clientes(
    client: AsyncClient, admin_headers: dict
):
    """
    Fluxo de negócio completo:
    1. Admin cria usuário com perfil Atendente.
    2. Atendente autentica via /auth/token.
    3. Atendente cria dois clientes (PF e PJ).
    4. Atendente lista clientes e confirma que ambos aparecem.
    """
    # 1. Admin cria o atendente
    email_atendente = f"atendente-{uuid.uuid4().hex[:8]}@example.com"
    resp_criar_user = await client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Atendente Teste Clientes",
            "email": email_atendente,
            "senha": "senha123",
            "perfis": ["Atendente"],
        },
        headers=admin_headers,
    )
    assert resp_criar_user.status_code == 201, (
        f"Falha ao criar atendente: {resp_criar_user.status_code} — {resp_criar_user.text}"
    )

    # 2. Atendente autentica
    resp_token = await client.post(
        "/api/v1/auth/token",
        data={"username": email_atendente, "password": "senha123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp_token.status_code == 200, (
        f"Falha ao autenticar atendente: {resp_token.text}"
    )
    atendente_headers = {"Authorization": f"Bearer {resp_token.json()['access_token']}"}

    # 3. Atendente cria cliente PF
    payload_pf = _payload_pf()
    resp_pf = await client.post("/api/v1/clientes", json=payload_pf, headers=atendente_headers)
    assert resp_pf.status_code == 201, f"Atendente falhou ao criar PF: {resp_pf.text}"
    cliente_pf = resp_pf.json()
    assert cliente_pf["tipo_pessoa"] == "PF"
    assert cliente_pf["ativo"] is True

    # 4. Atendente cria cliente PJ
    payload_pj = _payload_pj()
    resp_pj = await client.post("/api/v1/clientes", json=payload_pj, headers=atendente_headers)
    assert resp_pj.status_code == 201, f"Atendente falhou ao criar PJ: {resp_pj.text}"
    cliente_pj = resp_pj.json()
    assert cliente_pj["tipo_pessoa"] == "PJ"
    assert cliente_pj["ativo"] is True

    # 5. Atendente lista clientes e confirma que ambos aparecem
    resp_lista = await client.get("/api/v1/clientes", headers=atendente_headers)
    assert resp_lista.status_code == 200
    ids_listados = [c["id"] for c in _extrair_items(resp_lista.json())]
    assert cliente_pf["id"] in ids_listados, "Cliente PF não apareceu na listagem do atendente"
    assert cliente_pj["id"] in ids_listados, "Cliente PJ não apareceu na listagem do atendente"


# ---------------------------------------------------------------------------
# Remoção física
# ---------------------------------------------------------------------------

async def test_admin_deve_remover_cliente_fisicamente(
    client: AsyncClient, admin_headers: dict
):
    """DELETE /api/v1/clientes/{id} → 204; GET posterior → 404."""
    criado = await _criar_cliente(client, admin_headers, _payload_pf())
    cliente_id = criado["id"]

    resp_delete = await client.delete(
        f"/api/v1/clientes/{cliente_id}", headers=admin_headers
    )
    assert resp_delete.status_code == 204

    resp_get = await client.get(
        f"/api/v1/clientes/{cliente_id}", headers=admin_headers
    )
    assert resp_get.status_code == 404
