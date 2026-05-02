"""
Testes de integração — módulo Estoque.

Cada teste cria seus próprios dados.
Nenhum teste depende de outro.
Nenhum JWT e nenhum ID são hardcoded.

Rotas reais (prefixo /api/v1/itens-estoque):
  POST   /api/v1/itens-estoque
  GET    /api/v1/itens-estoque            (filtros: tipo, nome, codigo, ativo, baixo_estoque)
  GET    /api/v1/itens-estoque/{id}
  PATCH  /api/v1/itens-estoque/{id}
  PATCH  /api/v1/itens-estoque/{id}/ativar
  PATCH  /api/v1/itens-estoque/{id}/desativar

Perfis autorizados para todas as rotas: Administrador, Atendente.
Mecânico NÃO possui permissão.

Schema de criação (CriarItemEstoqueRequest):
  tipo: TipoItemEstoque  (PECA | INSUMO)
  nome: str
  descricao: Optional[str]
  codigo: Optional[str]
  quantidade_disponivel: int  (default 0)
  quantidade_minima: int       (default 0)
  valor_unitario: Decimal

Schema de resposta (ItemEstoqueResponse):
  id, tipo, nome, descricao, codigo,
  quantidade_disponivel, quantidade_reservada, quantidade_minima,
  valor_unitario, ativo

Constraint: codigo único (CodigoItemEstoqueJaCadastradoError → 409).
Soft delete: PATCH /{id}/desativar → ativo=false; PATCH /{id}/ativar → ativo=true.
"""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_BASE = "/api/v1/itens-estoque"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _codigo_unico() -> str:
    return f"COD-{uuid.uuid4().hex[:10].upper()}"


def _nome_unico(base: str = "Item Estoque") -> str:
    return f"{base} {uuid.uuid4().hex[:8]}"


def _payload_peca(**override) -> dict:
    base = {
        "tipo": "PECA",
        "nome": _nome_unico("Peça"),
        "descricao": "Peça de teste",
        "codigo": _codigo_unico(),
        "quantidade_disponivel": 10,
        "quantidade_minima": 2,
        "valor_unitario": "49.90",
    }
    base.update(override)
    return base


def _payload_insumo(**override) -> dict:
    base = {
        "tipo": "INSUMO",
        "nome": _nome_unico("Insumo"),
        "descricao": "Insumo de teste",
        "codigo": _codigo_unico(),
        "quantidade_disponivel": 20,
        "quantidade_minima": 5,
        "valor_unitario": "12.50",
    }
    base.update(override)
    return base


def _extrair_items(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    raise AssertionError(f"Formato inesperado de resposta: {payload}")


async def _criar_item_estoque(
    client: AsyncClient, headers: dict, **override
) -> dict:
    """Cria item de estoque (PECA por padrão) e retorna o JSON da resposta."""
    payload = _payload_peca(**override)
    response = await client.post(_BASE, json=payload, headers=headers)
    assert response.status_code == 201, (
        f"Erro ao criar item de estoque: {response.status_code} — {response.text}"
    )
    return response.json()


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
# 1. Autenticação
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_item_estoque_sem_autenticacao(client: AsyncClient):
    payload = _payload_peca()
    response = await client.post(_BASE, json=payload)
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 2-3. Criação válida
# ---------------------------------------------------------------------------


async def test_admin_deve_criar_item_estoque_peca(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca()
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["id"]
    assert data["tipo"] == "PECA"
    assert data["nome"] == payload["nome"]
    assert data["quantidade_disponivel"] == payload["quantidade_disponivel"]
    assert data["quantidade_minima"] == payload["quantidade_minima"]
    assert "quantidade_reservada" in data
    assert "valor_unitario" in data
    assert data["ativo"] is True


async def test_admin_deve_criar_item_estoque_insumo(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_insumo()
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["id"]
    assert data["tipo"] == "INSUMO"
    assert data["nome"] == payload["nome"]
    assert data["quantidade_disponivel"] == payload["quantidade_disponivel"]
    assert data["quantidade_minima"] == payload["quantidade_minima"]
    assert "quantidade_reservada" in data
    assert "valor_unitario" in data
    assert data["ativo"] is True


# ---------------------------------------------------------------------------
# 4-8. Validações de payload inválido
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_item_com_quantidade_disponivel_negativa(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca(quantidade_disponivel=-1)
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_item_com_quantidade_minima_negativa(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca(quantidade_minima=-1)
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_item_com_valor_unitario_negativo(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca(valor_unitario="-1.00")
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_item_com_tipo_invalido(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca(tipo="INVALIDO")
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


async def test_nao_deve_criar_item_com_nome_vazio(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_peca(nome="")
    response = await client.post(_BASE, json=payload, headers=admin_headers)
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 9. Unicidade de código
# ---------------------------------------------------------------------------


async def test_nao_deve_criar_item_duplicado_por_codigo(
    client: AsyncClient, admin_headers: dict
):
    codigo = _codigo_unico()
    # Primeiro item — deve criar
    payload1 = _payload_peca(codigo=codigo)
    r1 = await client.post(_BASE, json=payload1, headers=admin_headers)
    assert r1.status_code == 201

    # Segundo item com mesmo código — deve conflitar
    payload2 = _payload_peca(codigo=codigo)  # nome diferente (uuid), mesmo código
    r2 = await client.post(_BASE, json=payload2, headers=admin_headers)
    assert r2.status_code in (400, 409, 422)


# ---------------------------------------------------------------------------
# 10. Listagem
# ---------------------------------------------------------------------------


async def test_admin_deve_listar_itens_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    response = await client.get(_BASE, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert item["id"] in ids


# ---------------------------------------------------------------------------
# 11. Busca por ID
# ---------------------------------------------------------------------------


async def test_admin_deve_buscar_item_estoque_por_id(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    response = await client.get(f"{_BASE}/{item_id}", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == item_id
    assert data["nome"] == item["nome"]
    assert data["tipo"] == item["tipo"]
    assert "quantidade_disponivel" in data
    assert "quantidade_reservada" in data
    assert "quantidade_minima" in data


async def test_buscar_item_por_id_inexistente_deve_retornar_404(
    client: AsyncClient, admin_headers: dict
):
    id_inexistente = str(uuid.uuid4())
    response = await client.get(f"{_BASE}/{id_inexistente}", headers=admin_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 12. Filtro por nome
# ---------------------------------------------------------------------------


async def test_admin_deve_filtrar_item_estoque_por_nome(
    client: AsyncClient, admin_headers: dict
):
    nome = _nome_unico("FiltroNome")
    item = await _criar_item_estoque(client, admin_headers, nome=nome)

    response = await client.get(_BASE, params={"nome": nome}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert item["id"] in ids


# ---------------------------------------------------------------------------
# 13. Filtro por tipo
# ---------------------------------------------------------------------------


async def test_admin_deve_filtrar_item_estoque_por_tipo_peca(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers, tipo="PECA")

    response = await client.get(_BASE, params={"tipo": "PECA"}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert all(i["tipo"] == "PECA" for i in items)
    ids = [i["id"] for i in items]
    assert item["id"] in ids


async def test_admin_deve_filtrar_item_estoque_por_tipo_insumo(
    client: AsyncClient, admin_headers: dict
):
    payload = _payload_insumo()
    r = await client.post(_BASE, json=payload, headers=admin_headers)
    assert r.status_code == 201
    item = r.json()

    response = await client.get(_BASE, params={"tipo": "INSUMO"}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    assert all(i["tipo"] == "INSUMO" for i in items)
    ids = [i["id"] for i in items]
    assert item["id"] in ids


# ---------------------------------------------------------------------------
# 14. Filtro por estoque baixo
# ---------------------------------------------------------------------------


async def test_admin_deve_filtrar_itens_com_estoque_baixo(
    client: AsyncClient, admin_headers: dict
):
    # quantidade_disponivel (2) <= quantidade_minima (5) → baixo estoque
    item = await _criar_item_estoque(
        client, admin_headers, quantidade_disponivel=2, quantidade_minima=5
    )

    response = await client.get(
        _BASE, params={"baixo_estoque": True}, headers=admin_headers
    )
    assert response.status_code == 200

    items = _extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert item["id"] in ids


# ---------------------------------------------------------------------------
# 15. Atualização
# ---------------------------------------------------------------------------


async def test_admin_deve_atualizar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]
    novo_nome = _nome_unico("Atualizado")

    response = await client.patch(
        f"{_BASE}/{item_id}",
        json={"nome": novo_nome},
        headers=admin_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["nome"] == novo_nome
    assert data["id"] == item_id


async def test_admin_deve_atualizar_quantidade_minima_do_item(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers, quantidade_minima=3)
    item_id = item["id"]

    response = await client.patch(
        f"{_BASE}/{item_id}",
        json={"quantidade_minima": 10},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["quantidade_minima"] == 10


async def test_atualizar_sem_nenhum_campo_deve_retornar_erro(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    response = await client.patch(
        f"{_BASE}/{item_id}",
        json={},
        headers=admin_headers,
    )
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 16. Desativar / ativar (soft delete)
# ---------------------------------------------------------------------------


async def test_admin_deve_desativar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    response = await client.patch(
        f"{_BASE}/{item_id}/desativar", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["ativo"] is False


async def test_admin_deve_ativar_item_estoque_previamente_desativado(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    # Desativar
    r_desativar = await client.patch(f"{_BASE}/{item_id}/desativar", headers=admin_headers)
    assert r_desativar.status_code == 200
    assert r_desativar.json()["ativo"] is False

    # Ativar novamente
    r_ativar = await client.patch(f"{_BASE}/{item_id}/ativar", headers=admin_headers)
    assert r_ativar.status_code == 200
    assert r_ativar.json()["ativo"] is True


async def test_item_desativado_deve_aparecer_no_filtro_ativo_false(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    await client.patch(f"{_BASE}/{item_id}/desativar", headers=admin_headers)

    response = await client.get(_BASE, params={"ativo": False}, headers=admin_headers)
    assert response.status_code == 200

    items = _extrair_items(response.json())
    ids = [i["id"] for i in items]
    assert item_id in ids


# ---------------------------------------------------------------------------
# Autorização — Atendente
# ---------------------------------------------------------------------------


async def test_atendente_deve_criar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    headers = await _obter_headers_usuario(client, email, senha)

    payload = _payload_peca()
    response = await client.post(_BASE, json=payload, headers=headers)
    assert response.status_code == 201


async def test_atendente_deve_listar_itens_estoque(
    client: AsyncClient, admin_headers: dict
):
    # Admin cria item
    await _criar_item_estoque(client, admin_headers)

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(_BASE, headers=headers)
    assert response.status_code == 200
    _extrair_items(response.json())  # valida formato


async def test_atendente_deve_buscar_item_por_id(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(f"{_BASE}/{item_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == item_id


async def test_atendente_deve_atualizar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]
    novo_nome = _nome_unico("AtualizadoAtendente")

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.patch(
        f"{_BASE}/{item_id}",
        json={"nome": novo_nome},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["nome"] == novo_nome


async def test_atendente_deve_desativar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Atendente")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.patch(f"{_BASE}/{item_id}/desativar", headers=headers)
    assert response.status_code == 200
    assert response.json()["ativo"] is False


# ---------------------------------------------------------------------------
# Autorização — Mecânico (sem permissão)
# ---------------------------------------------------------------------------


async def test_mecanico_nao_deve_criar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    headers = await _obter_headers_usuario(client, email, senha)

    payload = _payload_peca()
    response = await client.post(_BASE, json=payload, headers=headers)
    assert response.status_code == 403


async def test_mecanico_nao_deve_listar_itens_estoque(
    client: AsyncClient, admin_headers: dict
):
    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(_BASE, headers=headers)
    assert response.status_code == 403


async def test_mecanico_nao_deve_buscar_item_por_id(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.get(f"{_BASE}/{item_id}", headers=headers)
    assert response.status_code == 403


async def test_mecanico_nao_deve_desativar_item_estoque(
    client: AsyncClient, admin_headers: dict
):
    item = await _criar_item_estoque(client, admin_headers)
    item_id = item["id"]

    email, senha = await _criar_usuario_com_perfil(client, admin_headers, "Mecanico")
    headers = await _obter_headers_usuario(client, email, senha)

    response = await client.patch(f"{_BASE}/{item_id}/desativar", headers=headers)
    assert response.status_code == 403
