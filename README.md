# API de Gestão de Oficina — MVP

<p align="left">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=py,fastapi,postgres,docker&theme=dark" />
  </a>
</p>

MVP de uma API REST para gestão de oficina mecânica, construída com **FastAPI** e **Python 3.12**, organizada seguindo os princípios de **Domain-Driven Design (DDD)** e **Clean Architecture**.

O projeto cobre o ciclo completo de atendimento: da abertura da ordem de serviço até a entrega do veículo, passando por diagnóstico, orçamento, aprovação, execução, pagamento e histórico.

---

## Tecnologias

- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL 16
- SQLModel / SQLAlchemy
- Alembic
- Pytest + Pytest-asyncio
- Docker / Docker Compose

---

## Estrutura do projeto

```
python-clean-architecture/
├── app/
│   ├── api/          # Rotas e controllers
│   ├── modules/      # Módulos de domínio (iam, clientes, veículos, ordens de serviço…)
│   └── shared/       # Infra compartilhada (banco, segurança, notificações)
├── alembic/          # Migrations
├── scripts/          # Seed e utilitários
└── tests/
    ├── unit/         # Testes unitários (sem banco)
    ├── integration/  # Testes de integração (com banco de teste)
    └── dev/          # Arquivos .http para testes manuais
```

---

## Configuração

Copie os arquivos de exemplo e ajuste as variáveis conforme o ambiente local:

```bash
cp .env.dev-example .env.dev
cp .env.test-example .env.test
```

> Os arquivos `.env.*` reais não são versionados.

---

## Executando a aplicação

```bash
docker compose -f docker-compose.dev.yml up --build
```

A API estará disponível em: `http://localhost:8000`

---

## Documentação da API

Com a aplicação rodando:

| Interface | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## Testes unitários

- Não sobem a API nem o banco de dados.
- Validam domínio, casos de uso e serviços internos de forma isolada.

```bash
docker compose -f docker-compose-unit.yml up --build --abort-on-container-exit
```

Relatório de cobertura gerado em:

```
python-clean-architecture/reports/coverage-unit.xml
```

---

## Testes de integração

- Sobem um PostgreSQL isolado para testes.
- Executam migrations e seed antes dos testes.
- Rodam contra a aplicação usando client HTTP de teste (sem servidor separado).

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

Relatório de cobertura gerado em:

```
python-clean-architecture/reports/coverage-integration.xml
```

Para limpar os containers e volumes após os testes:

```bash
docker compose -f docker-compose.test.yml down -v
```

---

## Testes manuais com .http

Os arquivos `.http` ficam em `tests/dev` e podem ser executados com a extensão **REST Client** do VS Code ou ferramenta compatível.

**Pré-requisito:** a aplicação deve estar rodando (`docker-compose.dev.yml`).

**Fluxo sugerido:**
1. Execute o arquivo de autenticação (`tests/dev/modules/iam/auth.http`) para obter o token JWT.
2. Use o token nos demais arquivos de teste.

---

## Docker Compose disponíveis

| Arquivo | Uso |
|---|---|
| `docker-compose.dev.yml` | Sobe API e banco para desenvolvimento |
| `docker-compose-unit.yml` | Executa testes unitários |
| `docker-compose.test.yml` | Executa testes de integração com banco isolado |

---

## Status

MVP acadêmico em desenvolvimento.

