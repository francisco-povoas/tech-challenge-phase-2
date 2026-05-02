# Arquitetura do Projeto — Gestão de Oficina Mecânica

> Este documento reúne a explicação completa da arquitetura, suas vantagens, a topologia detalhada do módulo IAM, o funcionamento das factories de injeção de dependência e as decisões de design tomadas durante o desenvolvimento.

---

## Contexto

Este é o back-end de um sistema de gerenciamento de oficina mecânica, centrado no ciclo de vida de uma **Ordem de Serviço (OS)**. O domínio foi modelado com DDD, passando por Domain Storytelling e Event Storming, resultando em agregados, atores, comandos, policies e eventos bem definidos.

O sistema é implementado como um **monólito modular** em FastAPI + PostgreSQL, com arquitetura interna baseada em Clean Architecture. A estrutura foi pensada para facilitar a evolução futura para microsserviços.

---

## Por que monólito modular?

Um monólito tradicional agrupa código por camada técnica (`models/`, `services/`, `routers/`), misturando responsabilidades de negócios diferentes no mesmo lugar. Isso dificulta extrair partes do sistema no futuro.

O monólito modular resolve isso: cada **contexto de negócio** vive em seu próprio módulo com suas próprias camadas internas. O resultado é a simplicidade operacional de um monólito (um processo, um banco, deploy único) com a disciplina de separação que microsserviços exigem. Quando chegar a hora de extrair um módulo, o código não precisa ser reescrito — só reorganizado.

---

## Estrutura de diretórios

```
app/
├── __init__.py              # Ponto de entrada: instancia a aplicação FastAPI e expõe `app`
├── __main__.py              # Entrypoint CLI: executa uvicorn
├── config.py                # Settings via pydantic-settings (variáveis de ambiente)
├── logger.py                # Configuração centralizada de logging
│
├── api/                     # Montagem central da aplicação FastAPI
│   ├── app.py               # create_app(): registra routers e extensões
│   ├── lifespan.py          # Gerencia ciclo de vida (startup/shutdown do banco)
│   ├── extensions.py        # Handlers globais de exceção (ex: validação de request)
│   └── routers/
│       ├── root.py          # Router raiz: apenas o endpoint /health-check
│       └── v1.py            # Agrega os routers de todos os módulos sob /api/v1
│
├── shared/                  # Código transversal — sem lógica de negócio específica
│   ├── exceptions.py        # DomainException: classe base de todas as exceções de domínio
│   ├── value_objects/
│   │   ├── email.py         # Email: valida formato via regex; lança InvalidEmailError
│   │   ├── id.py            # ID: wrapper de UUID com from_string() e generate()
│   │   └── password.py      # Password: valida tamanho mínimo/máximo; lança InvalidPasswordError
│   ├── dtos/
│   │   └── usuario_autenticado.py  # UsuarioAutenticado: dados de identidade extraídos do JWT
│   │                                # Usado por qualquer módulo que precise saber quem fez a
│   │                                # requisição, sem importar nada do módulo IAM
│   └── infra/
│       ├── db/
│       │   ├── __init__.py  # DBSession, engine, async_session (SQLAlchemy async)
│       │   └── base_uow.py  # BaseUnitOfWork: commit/rollback/close da sessão
│       ├── security/
│       │   └── crypto.py    # Hasher (bcrypt via passlib) + HasherProtocol (interface)
│       └── api/
│           └── dependencies/
│               └── auth.py  # get_usuario_autenticado(): valida JWT e retorna UsuarioAutenticado
│                            # Dependência FastAPI reutilizável por qualquer módulo
│
└── modules/                 # Contextos de negócio — cada um é um bounded context isolado
    ├── iam/                 # Identity & Access Management: usuários e autenticação
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   └── usuario.py       # Entidade Usuario: nome, email (Email VO), senha (Password VO)
    │   │   │                        # Regra: nome não pode ser vazio
    │   │   ├── ports/
    │   │   │   ├── usuario_repo.py  # Protocol UsuarioRepo: contrato de persistência
    │   │   │   │                    # (salvar, obter_por_id, obter_por_email, atualizar, remover)
    │   │   │   └── usuario_uow.py   # Protocol UsuarioUnitOfWork: agrupa usuario_repo + transação
    │   │   └── exceptions.py        # UsuarioNaoEncontradoError, UsuarioJaExisteError,
    │   │                            # AutenticacaoFalhouError, InvalidUsuarioError
    │   ├── application/
    │   │   ├── dtos/
    │   │   │   ├── usuario.py       # CriarUsuarioRequest, UsuarioResponse, AtualizarUsuario
    │   │   │   └── auth.py          # TokenResponse (expire, access_token, token_type)
    │   │   └── use_cases/
    │   │       ├── criar_usuario.py      # Valida email/senha, garante unicidade, persiste
    │   │       ├── autenticar_usuario.py # Busca por email, verifica hash da senha
    │   │       ├── obter_usuario.py      # Busca por ID, lança UsuarioNaoEncontradoError
    │   │       ├── atualizar_usuario.py  # Atualiza nome e/ou email de um usuário existente
    │   │       └── remover_usuario.py    # Remove pelo ID, retorna bool
    │   ├── infrastructure/
    │   │   ├── db/
    │   │   │   ├── models/
    │   │   │   │   └── usuario.py        # UsuarioModel (SQLModel): tabela `usuario`
    │   │   │   │                         # Colunas: id (UUID PK), nome, email (unique), senha_hash
    │   │   │   ├── repositories/
    │   │   │   │   └── usuario_repo.py   # UsuarioRepo: implementa o Protocol UsuarioRepo
    │   │   │   │                         # Converte entre UsuarioModel (ORM) e Usuario (entidade)
    │   │   │   └── uow/
    │   │   │       └── usuario_uow.py    # UsuarioUnitOfWork: estende BaseUnitOfWork,
    │   │   │                             # instancia UsuarioRepo e expõe como usuario_repo
    │   │   └── auth/
    │   │       └── jwt.py                # JWTProvider: create_access_token(), get_sub(), decode()
    │   │                                 # InvalidToken: lançada quando o token é inválido
    │   └── presentation/
    │       ├── dependencies/
    │       │   ├── __init__.py      # Factories de use cases como dependências FastAPI
    │       │   │                    # (CriarUsuario, ObterUsuario, AtualizarUsuario, etc.)
    │       │   └── auth.py          # TokenProvider, Oauth2Form, UsuarioAtual
    │       │                        # get_usuario_atual(): resolve o usuário logado via JWT
    │       └── routers/
    │           ├── usuario.py       # CRUD: POST /usuarios, GET/PATCH/DELETE /usuarios/{id}
    │           └── auth.py          # POST /auth/token (login), GET /auth/me (usuário logado)
    │
    └── veiculos/            # Cadastro e gestão de veículos dos clientes
        ├── domain/
        │   ├── entities/
        │   │   └── veiculo.py       # Entidade Veiculo: placa, marca, modelo, ano, cliente_id
        │   │                        # Regras: placa não vazia, ano entre 1886 e 2100
        │   │                        # cliente_id é string pura — sem import do módulo clientes
        │   ├── ports/
        │   │   └── veiculo_repo.py  # Protocol VeiculoRepo: salvar, obter_por_id,
        │   │                        # obter_por_placa, listar_por_cliente, remover
        │   └── exceptions.py        # VeiculoNaoEncontradoError, PlacaJaCadastradaError,
        │                            # VeiculoInvalidoError
        ├── application/
        │   ├── dtos/
        │   │   └── veiculo.py       # CriarVeiculoRequest, VeiculoResponse, AtualizarVeiculo
        │   └── use_cases/           # A implementar nas próximas iterações
        ├── infrastructure/
        │   └── db/
        │       ├── models/
        │       │   └── veiculo.py        # VeiculoModel (SQLModel): tabela `veiculo`
        │       │                         # cliente_id sem FK declarada — desacoplamento intencional
        │       ├── repositories/
        │       │   └── veiculo_repo.py   # VeiculoRepo: implementação concreta do Protocol
        │       └── uow/
        │           └── veiculo_uow.py    # VeiculoUnitOfWork: estende BaseUnitOfWork
        └── presentation/
            ├── dependencies/        # A implementar junto com os use cases
            └── routers/
                └── veiculo.py      # Endpoints a implementar (esqueleto registrado no v1.py)
```

---

## Responsabilidade de cada camada

### `domain/` — O que o sistema É

A camada mais interna. **Zero dependências externas** — sem FastAPI, sem SQLModel, sem outros módulos.

- **`entities/`** — objetos com identidade própria e regras de negócio intrínsecas. Usam Value Objects para garantir que dados inválidos nunca existam no domínio.
- **`ports/`** — contratos (`Protocol`) que o domínio exige do mundo externo. Não sabe se é PostgreSQL, MongoDB ou um dict em memória. É uma promessa sem implementação.
- **`exceptions.py`** — exceções de domínio específicas do módulo.

### `application/` — Como o sistema FAZ

Orquestra o domínio. **Depende apenas de `domain/` e `shared/`**.

- **`use_cases/`** — um arquivo por caso de uso. Cada um é um **comando do Event Storming materializado em código**. Coordena entidades e ports sem ter lógica de negócio própria.
- **`dtos/`** — objetos simples de transferência entre camadas. O use case não sabe que existe HTTP, e o router não sabe que existe entidade de domínio.

### `infrastructure/` — Como o sistema se CONECTA ao mundo externo

Implementações concretas dos ports. **Pode depender de bibliotecas externas**.

- **`db/models/`** — mapeamento ORM (SQLModel). Representa a tabela, não o domínio. Tem conversão de/para entidade.
- **`db/repositories/`** — implementa o Protocol do domain/ports. Recebe `AsyncSession` e usa o model ORM.
- **`db/uow/`** — implementa o Unit of Work. Garante atomicidade das operações de escrita.
- **`auth/`** — provedor JWT (geração e decodificação de tokens).

### `presentation/` — Como o sistema é ACESSADO

Interface HTTP. **Depende de `application/`** via injeção de dependência.

- **`dependencies/`** — factories que montam os use cases com suas dependências. É o único lugar do sistema onde você diz _"quando alguém pedir `UsuarioRepo`, entregue `UsuarioRepoImpl` com esta session"_.
- **`routers/`** — endpoints FastAPI. Recebem request, chamam use case, retornam response.

---

## Topologia detalhada do módulo IAM

### O princípio central

As camadas internas não sabem que as externas existem. A dependência sempre aponta para dentro:

```
presentation  →  application  →  domain  ←  infrastructure
```

### Value Objects

`Email`, `Password` e `ID` vivem em `shared/value_objects/` porque são usados por múltiplos módulos. Cada um encapsula validação e garante que um dado inválido **nunca existe** no domínio:

```python
Email("invalido")    # lança InvalidEmailError imediatamente
Password("abc")      # lança InvalidPasswordError (menos de 8 caracteres)
ID.from_string("x")  # lança InvalidIDError
```

### Por que separar `UsuarioRepo` do `UsuarioUnitOfWork`?

| `UsuarioRepo` (port direto) | `UsuarioUnitOfWork` (port com transação) |
|---|---|
| Operações de **leitura** — não precisa de transação | Operações de **escrita** — precisa de atomicidade |
| `ObterUsuarioUseCase`, `AutenticarUsuarioUseCase` | `CriarUsuarioUseCase`, `AtualizarUsuarioUseCase`, `RemoverUsuarioUseCase` |

O `UsuarioUnitOfWork` expõe o `usuario_repo` internamente porque o repositório precisa estar **dentro da mesma sessão/transação**. Ao fazer `uow.commit()`, tudo que o repo fez é confirmado atomicamente.

### Por que separar `UsuarioModel` (ORM) da entidade `Usuario`?

O banco muda por razões técnicas (índices, colunas de auditoria, FKs). O domínio muda por razões de negócio. Se forem a mesma classe, qualquer mudança em um impacta o outro. O repositório faz a conversão entre os dois mundos:

```
Banco → UsuarioModel (ORM) → _to_entity() → Usuario (domínio)
Domínio → Usuario → UsuarioModel → session.add() → Banco
```

### DTOs de application vs schemas de presentation

São coisas diferentes com propósitos diferentes:

```
HTTP request (JSON)
    │
    ▼
presentation: CriarUsuarioRequest   ← valida o contrato HTTP
    │
    ▼
application/dtos: CriarUsuarioDTO   ← o use case não sabe que existe HTTP
    │
    ▼
domain: Usuario                     ← o domínio não sabe que existe DTO
```

---

## Como a injeção de dependência funciona

### O problema que ela resolve

`CriarUsuarioUseCase` precisa de `uow` e `hasher`. O `uow` precisa de `session`. A `session` vem do pool de conexões do SQLAlchemy, gerenciado pelo FastAPI. O arquivo `presentation/dependencies/__init__.py` é a **fábrica** que monta essa cadeia automaticamente a cada request.

### Cadeia de construção para `POST /usuarios`

```
FastAPI recebe request
│
├─► Depends(get_usuario_uow)
│     └─► abre AsyncSession via async_session()
│           └─► usuario_uow_factory(session)
│                 └─► UsuarioUnitOfWork(session)
│                       └─► UsuarioRepo(session)  ← mesmo session do uow!
│
├─► Depends(get_hasher)
│     └─► Hasher()
│
└─► Depends(get_criar_usuario)
      ├─► recebe uow (já construído acima)
      ├─► recebe hasher (já construído acima)
      └─► CriarUsuarioUseCase(uow=uow, hasher=hasher)
```

### O que são os `Annotated` no final do arquivo de dependencies

São açúcar sintático do FastAPI. Permitem que o router seja limpo:

```python
# Sem Annotated — verboso
async def criar(usecase: CriarUsuarioUseCase = Depends(get_criar_usuario)):
    ...

# Com Annotated — limpo
CriarUsuario = Annotated[CriarUsuarioUseCase, Depends(get_criar_usuario)]

async def criar(usecase: CriarUsuario):
    ...
```

O tipo continua sendo `CriarUsuarioUseCase` para o type checker. O `Depends` resolve a construção em runtime. São a mesma coisa expressa de formas diferentes.

---

## Fluxo completo de uma requisição

### `POST /api/v1/usuarios`

```
POST /usuarios  {nome, email, senha}
│
▼
presentation/routers/usuario.py
  └── async def criar(dto: CriarUsuarioRequest, usecase: CriarUsuario)
        │
        │  FastAPI resolve CriarUsuario automaticamente (ver seção acima)
        │
        ▼
      await usecase.execute(dto)                    ← application
        │
        ├── Email(dto.email)                        ← valida (shared/value_objects)
        ├── Password(dto.senha)                     ← valida (shared/value_objects)
        │
        ├── async with self.uow:                    ← abre transação
        │     obter_por_email(email)                ← garante unicidade
        │     senha_hash = hasher.hash(senha.value) ← hasheia (shared/infra/security)
        │     usuario = Usuario(...)                ← cria entidade (domain)
        │     uow.usuario_repo.salvar(usuario)      ← persiste via port
        │       └── UsuarioModel from_entity()      ← converte (infrastructure)
        │             └── session.add(model)        ← SQLAlchemy
        │     uow.commit()                          ← session.commit()
        │
        └── return UsuarioResponse(...)             ← DTO de saída (application)
              │
              ▼
            router retorna HTTP 201 {id, nome, email}
```

---

## Comunicação entre módulos

A regra é: **um módulo nunca importa diretamente de outro módulo**. A comunicação acontece por contratos explícitos.

### Autenticação em rotas de outros módulos

O middleware de autenticação vive em `shared/infra/api/dependencies/auth.py`. Qualquer módulo pode proteger suas rotas assim:

```python
# modules/ordens_servico/presentation/routers/ordem_servico.py
from app.shared.infra.api.dependencies.auth import UsuarioAutenticadoDep

@router.patch("/{os_id}/status")
async def alterar_status(
    os_id: UUID,
    dto: AlterarStatusRequest,
    usuario: UsuarioAutenticadoDep,     # ← valida JWT, retorna UsuarioAutenticado
    usecase: AlterarStatusUsecase = Depends(...),
):
    await usecase.execute(os_id=str(os_id), novo_status=dto.status, usuario_id=usuario.id)
```

`UsuarioAutenticado` é um DTO simples em `shared/dtos/` — não é a entidade `Usuario` do IAM. Carrega só o que o token JWT contém: `id` e `perfis`. Cada módulo usa o que precisa, sem acoplamento.

### Quando um módulo precisa acionar outro (operação síncrona)

O módulo que precisa declara um `Protocol` descrevendo o que necessita. O outro módulo fornece a implementação. A injeção de dependência conecta os dois em runtime, sem import direto:

```python
# Módulo OS declara o que precisa — sem saber quem implementa
class ServicoPermissao(Protocol):
    async def usuario_pode_alterar_os(self, usuario_id: str, os_id: str) -> bool: ...

# Módulo IAM implementa
class ServicoPermissaoImpl:
    async def usuario_pode_alterar_os(self, usuario_id: str, os_id: str) -> bool:
        ...

# presentation/dependencies do módulo OS conecta os dois em runtime
```

### Quando uma ação dispara consequências em outro módulo (operação assíncrona)

Usa eventos de domínio. No monólito, o event bus é simples (handlers em memória). Na migração para microsserviços, vira um broker real (Kafka, RabbitMQ) sem que a lógica de negócio mude:

```
OrdemServicoFinalizada → [event bus] → módulo Pagamentos reage
OrcamentoAprovado      → [event bus] → módulo OS avança status
```

---

## Vantagens concretas da arquitetura

### 1. Você pode trocar o banco sem tocar em negócio

Hoje é PostgreSQL com SQLAlchemy. Amanhã precisa migrar para MongoDB. Crie um novo arquivo em `infrastructure/repositories/` implementando o mesmo Protocol. Use case, entidade, router — **zero alterações**.

### 2. Você testa a regra de negócio sem banco

`CriarUsuarioUseCase` depende de `UsuarioUnitOfWork` (um Protocol). No teste, você passa um fake:

```python
class FakeUoW:
    def __init__(self):
        self.usuario_repo = FakeRepo()
        self.committed = False

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def commit(self): self.committed = True

async def test_criar_usuario_hasheia_senha():
    uow = FakeUoW()
    usecase = CriarUsuarioUseCase(uow=uow, hasher=FakeHasher())

    await usecase.execute(CriarUsuarioDTO(email="a@a.com", senha="senha1234"))

    assert uow.committed is True
    assert uow.usuario_repo.saved[0].senha != "senha1234"  # foi hasheada
```

Sem FastAPI. Sem banco. Sem Docker. Milissegundos.

### 3. Você sabe exatamente onde mexer quando um requisito muda

Chegou um requisito: _"ao criar usuário, enviar e-mail de boas-vindas"_. Você sabe que vai no `CriarUsuarioUseCase`. Não vai procurar em 10 arquivos de service misturados.

### 4. A extração para microsserviço é mover uma pasta

Cada módulo já é um bounded context isolado. Para extraí-lo: mova a pasta, publique o `shared/` como pacote, crie o `api/app.py` próprio. A lógica não muda.

---

## Ports vs Adapters — a nomenclatura

No padrão original **Ports & Adapters (Hexagonal Architecture)**:

| Termo | O que é | Neste projeto |
|---|---|---|
| **Port** | O contrato — a interface | `domain/ports/usuario_repo.py` |
| **Adapter** | A implementação concreta | `infrastructure/db/repositories/usuario_repo.py` |

Clean Architecture usa nomes diferentes mas o conceito é idêntico:

| Hexagonal | Clean Architecture | Neste projeto |
|---|---|---|
| Port | Repository Interface / Gateway | `domain/ports/` |
| Adapter | Repository Implementation | `infrastructure/` |

Ports **declaram a intenção**. Adapters **realizam a intenção**. O `presentation/dependencies/__init__.py` é onde você **liga um ao outro** em tempo de execução.

---

## Sobre entidades sem port próprio

Se uma entidade é simples demais para ter repositório próprio (ex.: `Perfil` que é sempre lido junto com `Usuario`), ela faz parte do **agregado raiz**. O repositório do agregado raiz já a cobre:

```python
# domain/ports/usuario_repo.py
class UsuarioRepo(Protocol):
    async def obter_por_id(self, id: ID) -> Usuario | None: ...
    # Usuario já retorna com lista de Perfil dentro — Perfil não precisa de repo próprio
```

Não crie ports e use cases para tudo. Só crie quando a entidade tem ciclo de vida próprio e precisa ser persistida ou consultada independentemente.

---

## Resumo mental das camadas

```
┌─────────────────────────────────────────────────────┐
│  presentation/routers      HTTP in/out               │
│  presentation/dependencies  liga tudo via Depends    │
├─────────────────────────────────────────────────────┤
│  application/use_cases     comandos do Event Storming│
│  application/dtos          transferência de dados    │
├─────────────────────────────────────────────────────┤
│  domain/entities           o que É o negócio         │
│  domain/ports              o que o negócio PRECISA   │
├─────────────────────────────────────────────────────┤
│  infrastructure/           como o mundo ENTREGA      │
│  (repositories, uow, jwt)  o que o domínio pediu     │
└─────────────────────────────────────────────────────┘
          ↑ dependências só apontam para cima ↑
```

| Camada | Pergunta que responde | Depende de |
|---|---|---|
| `domain/entities` | O que é um Usuário? | Nada |
| `domain/ports` | O que o domínio precisa do mundo? | Nada |
| `application/use_cases` | Como criar/autenticar/remover um usuário? | `domain` |
| `infrastructure/models` | Como o usuário é salvo no banco? | SQLModel |
| `infrastructure/repositories` | Como buscar/salvar via ORM? | `domain/ports`, `infrastructure/models` |
| `infrastructure/uow` | Como garantir atomicidade? | `infrastructure/repositories` |
| `presentation/dependencies` | Como o FastAPI monta tudo? | Todas as anteriores |
| `presentation/routers` | Quais endpoints existem? | `application` via dependencies |

---

## Como adicionar um novo módulo

1. Criar `app/modules/<nome>/` com as quatro camadas
2. Definir entidades e ports em `domain/`
3. Escrever use cases em `application/use_cases/`
4. Implementar models, repositórios e UoW em `infrastructure/`
5. Criar routers e dependencies em `presentation/`
6. Registrar o router em `app/api/routers/v1.py`

Nenhum outro arquivo existente precisa ser alterado.

---

## Módulos planejados

| Módulo | Domínio | Tabelas principais |
|---|---|---|
| `iam` ✅ | Identidade, autenticação e controle de acesso | `usuario`, `perfil`, `usuario_perfil` |
| `veiculos` ✅ *(skeleton)* | Cadastro e gestão de veículos dos clientes | `veiculo` |
| `clientes` *(futuro)* | Cadastro de clientes | `cliente` |
| `ordens_servico` *(futuro)* | Ciclo de vida da OS | `ordem_servico`, `item_os` |
| `orcamentos` *(futuro)* | Criação e aprovação de orçamentos | `orcamento`, `item_orcamento` |
| `estoque` *(futuro)* | Peças e itens de estoque | `item_estoque`, `movimentacao` |
| `pagamentos` *(futuro)* | Registros de pagamento | `pagamento` |
