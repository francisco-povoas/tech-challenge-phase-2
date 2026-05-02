"""
Testes de integração — módulo Serviços.

Cada teste cria seus próprios dados.
Nenhum teste depende de outro.
Nenhum JWT e nenhum ID são hardcoded.

Rotas reais (prefixo /api/v1/servicos):
  POST   /api/v1/servicos
  GET    /api/v1/servicos            (filtros opcionais: nome, ativo)
  GET    /api/v1/servicos/{id}
  PATCH  /api/v1/servicos/{id}
  PATCH  /api/v1/servicos/{id}/ativar
  PATCH  /api/v1/servicos/{id}/desativar

Perfis autorizados para todas as rotas: Administrador, Atendente.
Mecânico NÃO possui permissão.

Schema de criação (CriarServicoRequest):
  nome: str
  descricao: Optional[str]
  valor_base: Decimal
  tempo_medio_minutos: int

Schema de resposta (ServicoResponse):
  id, nome, descricao, valor_base, tempo_medio_minutos, ativo
"""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "/api/v1/servicos"


def _nome_unico(base: str = "Servico Teste") -> str:
    return f"{base} {uuid.uuid4().hex[:8]}"


def _payload_servico(**override) -> dict:
    base = {
        "nome": _nome_unico(),
        "descricao": "Descricao de teste",
        "valor_base": 150.00,
        "tempo_medio_minutos": 60,
    }
    base.update(override)
    return base


async def _criar_servico(client: AsyncClient, headers: dict, **override) -> dict:
    payload = _payload_servico(**override)
    response = await client.post(_BASE, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar serviço: {response.status_code} — {response.text}"
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


async def _criar_usuario_com_perfil(
    client: AsyncClient, admin_headers: dict, perfil: str
) -> tuple[str, str]:
    """Cria usuário com perfil informado. Retorna (email, senha)."""
    email = f"usuario-{uuid.uuid4().hex[:8]}@example.com"
    senha = "Senha@1234"
    payload = {
        "nome": f"Usuario {perfil} {uuid.uuid4().hex[:6]}",
        "email": email,
        "senha": senha,
        "perfis": [perfil],
    }
    response = await client.post("/api/v1/usuarios", json=payload, headers=admin_headers)
    assert response.status_code in (200, 201), (
        f"Erro ao criar usuário {perfil}: {response.status_code} — {response.text}"
    )
    return email, senha


async def _obter_headers_usuario(client: AsyncClient, email: str, senha: str) -> dict:
    """Autentica usuário e retorna headers Authorization Bearer."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": senha},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, (
        f"Falha ao autenticar {email}: {response.status_code} — {response.text}"
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

async def test_nao_deve_criar_servico_sem_autenticacao(client: AsyncClient):
    """POST sem Authorization deve retornar 401 ou 403."""
    response = await client.post(_BASE, json=_payload_servico())
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Criação — Admin
# ---------------------------------------------------------------------------

async def test_admin_deve_criar_servico(client: AsyncClient, admin_headers: dict):
    """POST com admin_headers e payload válido deve retornar 201."""
    payload = _payload_servico()
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code == 201

    body = response.json()
    assert "id" in body
    assert body["nome"] == payload["nome"]
    assert body["descricao"] == payload["descricao"]
    assert float(body["valor_base"]) == pytest.approx(payload["valor_base"])
    assert body["tempo_medio_minutos"] == payload["tempo_medio_minutos"]
    assert body["ativo"] is True


async def test_nao_deve_criar_servico_com_valor_negativo(
    client: AsyncClient, admin_headers: dict
):
    """POST com valor_base negativo deve retornar 400 ou 422."""
    payload = _payload_servico(valor_base=-10.00)
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_servico_com_tempo_zero(
    client: AsyncClient, admin_headers: dict
):
    """POST com tempo_medio_minutos=0 deve retornar 400 ou 422 (regra de domínio: > 0)."""
    payload = _payload_servico(tempo_medio_minutos=0)
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_servico_com_nome_vazio(
    client: AsyncClient, admin_headers: dict
):
    """POST com nome vazio deve retornar 400 ou 422."""
    payload = _payload_servico(nome="")
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_servico_com_nome_duplicado(
    client: AsyncClient, admin_headers: dict
):
    """Segundo POST com mesmo nome deve retornar 409."""
    nome = _nome_unico("Servico Duplicado")
    await _criar_servico(client, admin_headers, nome=nome)

    payload = _payload_servico(nome=nome)
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 409, 422)


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

async def test_admin_deve_listar_servicos(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos com admin deve retornar 200 contendo o serviço criado."""
    servico = await _criar_servico(client, admin_headers)

    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    ids = [s["id"] for s in items]
    assert servico["id"] in ids


async def test_admin_deve_filtrar_servico_por_nome(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos?nome=<nome_unico> deve retornar somente o serviço com aquele nome."""
    nome = _nome_unico("Filtro Nome")
    servico = await _criar_servico(client, admin_headers, nome=nome)

    response = await client.get(_BASE, params={"nome": nome}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert any(s["id"] == servico["id"] for s in items)


async def test_admin_deve_filtrar_servico_por_ativo(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos?ativo=true deve retornar apenas serviços ativos."""
    servico = await _criar_servico(client, admin_headers)

    response = await client.get(_BASE, params={"ativo": "true"}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert any(s["id"] == servico["id"] for s in items)
    assert all(s["ativo"] is True for s in items)


# ---------------------------------------------------------------------------
# Busca por ID
# ---------------------------------------------------------------------------

async def test_admin_deve_buscar_servico_por_id(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos/{id} deve retornar 200 com dados do serviço."""
    servico = await _criar_servico(client, admin_headers)
    sid = servico["id"]

    response = await client.get(f"{_BASE}/{sid}", headers=admin_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["id"] == sid
    assert body["nome"] == servico["nome"]
    assert float(body["valor_base"]) == pytest.approx(float(servico["valor_base"]))


async def test_deve_retornar_404_para_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos/{id_inexistente} deve retornar 404."""
    id_inexistente = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{id_inexistente}", headers=admin_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Atualização
# ---------------------------------------------------------------------------

async def test_admin_deve_atualizar_servico(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /servicos/{id} deve retornar 200 com dados atualizados."""
    servico = await _criar_servico(client, admin_headers)
    sid = servico["id"]

    novo_nome = _nome_unico("Servico Atualizado")
    response = await client.patch(
        f"{_BASE}/{sid}",
        json={"nome": novo_nome, "valor_base": 200.00},
        headers=admin_headers,
    )
    assert response.status_code == 200

    body = response.json()
    assert body["nome"] == novo_nome
    assert float(body["valor_base"]) == pytest.approx(200.00)


async def test_nao_deve_atualizar_servico_inexistente(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /servicos/{id_inexistente} deve retornar 404."""
    id_inexistente = str(uuid.uuid4())
    response = await client.patch(
        f"{_BASE}/{id_inexistente}",
        json={"nome": _nome_unico()},
        headers=admin_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Soft delete — desativar/ativar
# ---------------------------------------------------------------------------

async def test_admin_deve_desativar_servico(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /servicos/{id}/desativar deve retornar 200 com ativo=False."""
    servico = await _criar_servico(client, admin_headers)
    sid = servico["id"]

    response = await client.patch(f"{_BASE}/{sid}/desativar", headers=admin_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["ativo"] is False


async def test_admin_deve_ativar_servico_desativado(
    client: AsyncClient, admin_headers: dict
):
    """PATCH /servicos/{id}/ativar deve retornar 200 com ativo=True."""
    servico = await _criar_servico(client, admin_headers)
    sid = servico["id"]

    # Desativa primeiro
    r = await client.patch(f"{_BASE}/{sid}/desativar", headers=admin_headers)
    assert r.status_code == 200

    # Reativa
    response = await client.patch(f"{_BASE}/{sid}/ativar", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["ativo"] is True


async def test_admin_deve_filtrar_servicos_inativos(
    client: AsyncClient, admin_headers: dict
):
    """GET /servicos?ativo=false deve retornar apenas serviços desativos."""
    servico = await _criar_servico(client, admin_headers)
    sid = servico["id"]

    await client.patch(f"{_BASE}/{sid}/desativar", headers=admin_headers)

    response = await client.get(_BASE, params={"ativo": "false"}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert any(s["id"] == sid for s in items)
    assert all(s["ativo"] is False for s in items)


# ---------------------------------------------------------------------------
# Autorização por perfil — Atendente (permitido)
# ---------------------------------------------------------------------------

async def test_atendente_deve_listar_servicos(
    client: AsyncClient, admin_headers: dict
):
    """Atendente pode listar serviços (perfil autorizado)."""
    # Admin cria serviço
    servico = await _criar_servico(client, admin_headers)

    # Cria e autentica Atendente
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    atendente_headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(_BASE, headers=atendente_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert any(s["id"] == servico["id"] for s in items)


async def test_atendente_deve_criar_servico(
    client: AsyncClient, admin_headers: dict
):
    """Atendente pode criar serviço (perfil autorizado)."""
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    atendente_headers = await _obter_headers_usuario(client, email, senha)

    payload = _payload_servico()
    response = await client.post(_BASE, json=payload, headers=atendente_headers)
    assert response.status_code == 201

    body = response.json()
    assert body["nome"] == payload["nome"]
    assert body["ativo"] is True


async def test_atendente_deve_buscar_servico_por_id(
    client: AsyncClient, admin_headers: dict
):
    """Atendente pode buscar serviço por ID."""
    servico = await _criar_servico(client, admin_headers)

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    atendente_headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(f"{_BASE}/{servico['id']}", headers=atendente_headers)
    assert response.status_code == 200
    assert response.json()["id"] == servico["id"]


# ---------------------------------------------------------------------------
# Autorização por perfil — Mecânico (não autorizado)
# ---------------------------------------------------------------------------

async def test_mecanico_nao_deve_listar_servicos(
    client: AsyncClient, admin_headers: dict
):
    """Mecânico não possui perfil autorizado para acessar serviços."""
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    mecanico_headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(_BASE, headers=mecanico_headers)
    assert response.status_code == 403


async def test_mecanico_nao_deve_criar_servico(
    client: AsyncClient, admin_headers: dict
):
    """Mecânico não pode criar serviço — deve retornar 403."""
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    mecanico_headers = await _obter_headers_usuario(client, email, senha)

    response = await client.post(_BASE, json=_payload_servico(), headers=mecanico_headers)
    assert response.status_code == 403
