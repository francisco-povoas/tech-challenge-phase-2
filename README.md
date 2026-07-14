# API de Gestão de Oficina — MVP

<p align="left">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=py,fastapi,postgres,docker,kubernetes,terraform,aws,githubactions&theme=dark" />
  </a>
</p>

MVP de uma API REST para gestão de oficina mecânica, construída com **FastAPI** e **Python 3.12**, organizada seguindo os princípios de **Domain-Driven Design (DDD)** e **Clean Architecture**.

O projeto cobre o ciclo completo de atendimento: da abertura da ordem de serviço até a entrega do veículo, passando por diagnóstico, orçamento, aprovação, execução, pagamento.

Esta versão contempla a evolução da Fase 2 do Tech Challenge, adicionando **containerização**, **testes automatizados**, **CI/CD**, **Kubernetes**, **Terraform** e provisionamento de infraestrutura na **AWS**.

---

## Tecnologias

### Aplicação

- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL 16
- SQLModel / SQLAlchemy
- Alembic
- Pytest + Pytest-asyncio
- Docker / Docker Compose

### Infraestrutura e DevOps

- GitHub Actions
- Docker
- Amazon ECR
- Amazon EKS
- Amazon RDS PostgreSQL
- Amazon S3 para Terraform remote state
- Terraform
- Kubernetes Deployment, Service, Secret, Job e HPA

---


## Arquitetura da solução

A aplicação é empacotada em uma imagem Docker e publicada no **Amazon ECR**. O ambiente de staging roda em **Amazon EKS**, com pods executando a API FastAPI/Uvicorn. O banco de dados PostgreSQL é provisionado no **Amazon RDS** e acessado pela aplicação por meio de variáveis sensíveis armazenadas em **Kubernetes Secrets**.

A API é exposta por um **Service Kubernetes do tipo LoadBalancer**, que provisiona um **AWS Load Balancer** com DNS público. O **HPA** escala os pods automaticamente conforme consumo de CPU.

![Arquitetura AWS Staging](python-clean-architecture/docs/architecture-staging-aws.jpg)

### Recursos provisionados

| Recurso | Finalidade |
|---|---|
| Amazon ECR | Armazenamento das imagens Docker da aplicação |
| Amazon EKS | Cluster Kubernetes para execução da API |
| EKS Node Group | Capacidade computacional para execução dos pods |
| AWS Load Balancer | Exposição HTTP externa da API |
| Amazon RDS PostgreSQL | Banco de dados da aplicação |
| Security Groups | Controle de acesso entre EKS e RDS |
| Amazon S3 | Armazenamento remoto do state do Terraform |
| Kubernetes Deployment | Execução dos pods da API |
| Kubernetes Service | Exposição da aplicação dentro/fora do cluster |
| Kubernetes Secret | Variáveis sensíveis da aplicação |
| Kubernetes Job | Execução de migrations e seed admin |
| HPA | Escalabilidade automática dos pods |

---

## Fluxo de CI/CD

O projeto utiliza GitHub Actions para validação e deploy do ambiente de staging.

![Fluxo CI/CD](python-clean-architecture/docs/ci-cd-staging.jpg)

### Estratégia de branches

| Branch | Finalidade |
|---|---|
| `feature/*` | Desenvolvimento de novas funcionalidades |
| `dev` | Integração das features e execução de testes |
| `staging` | Ambiente cloud demonstrável na AWS |
| `main` | Preparada para produção futura, não implementada nesta fase |

> A branch `main` não provisiona um ambiente de produção nesta entrega. A decisão foi manter apenas o ambiente `staging` para reduzir custo e complexidade no contexto acadêmico. A estrutura foi preparada para permitir evolução futura para múltiplos ambientes.

### Pipelines

| Workflow | Gatilho | Responsabilidade |
|---|---|---|
| `ci.yml` | Pull Request | Executa testes unitários, testes de integração e validação de build |
| `deploy-staging.yml` | Push na `staging` | Publica imagem no ECR e atualiza o ambiente Kubernetes no EKS |

O deploy em staging executa, em ordem:

1. Build da imagem Docker.
2. Push da imagem para o Amazon ECR.
3. Configuração de acesso ao cluster EKS.
4. Aplicação do namespace e secrets no Kubernetes.
5. Execução do Job de migrations com Alembic e seed admin.
6. Aplicação dos manifestos Kubernetes.
7. Atualização da imagem do Deployment.
8. Espera do rollout da aplicação.

---

## Estrutura do projeto

```text
.
├── .github/workflows/       # Pipelines de CI/CD
├── infra/
│   ├── bootstrap/           # Bucket S3 para remote state do Terraform
│   └── staging/             # Infraestrutura AWS do ambiente staging
├── k8s/
│   └── staging/             # Manifests Kubernetes do ambiente staging
├── python-clean-architecture/
│   ├── app/
│   │   ├── api/             # Rotas e controllers
│   │   ├── modules/         # Módulos de domínio
│   │   └── shared/          # Infra compartilhada
│   ├── alembic/             # Migrations
│   ├── scripts/             # Seed e utilitários
│   └── tests/
│       ├── unit/            # Testes unitários
│       ├── integration/     # Testes de integração
│       └── dev/             # Arquivos .http para testes manuais
└── docs/                    # Diagramas e ADRs
```

## Organização em Clean Architecture

A aplicação está organizada por módulos de domínio em `python-clean-architecture/app/modules/`, como `clientes`, `estoque`, `iam`, `ordens_servico`, `servicos` e `veiculos`. Em geral, cada módulo separa as responsabilidades em `domain`, `application`, `infrastructure` e `presentation`, mantendo as regras de negócio próximas do contexto ao qual pertencem.

A camada `domain` concentra entidades, value objects, filtros, exceções e portas; `application` reúne DTOs e casos de uso que coordenam os fluxos da aplicação; `infrastructure` implementa detalhes externos, como persistência, autenticação e adapters concretos; e `presentation` expõe routers e dependências HTTP do FastAPI. Essa divisão evidencia a inversão de dependências por meio de portas e Unit of Work, além de facilitar a leitura dos limites entre regras de negócio, orquestração e tecnologia.

O diretório `python-clean-architecture/app/shared/` está no mesmo nível de `modules/` e reúne estruturas reutilizáveis entre contextos, como DTOs compartilhados, infraestrutura comum, portas genéricas e value objects transversais. Como evolução futura, vale manter esse diretório restrito a elementos realmente compartilhados, evitando concentrar regras específicas de um domínio fora do seu módulo.

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

## Docker Compose disponíveis para testes locais

| Arquivo | Uso |
|---|---|
| `docker-compose.dev.yml` | Sobe API e banco para desenvolvimento |
| `docker-compose-unit.yml` | Executa testes unitários |
| `docker-compose.test.yml` | Executa testes de integração com banco isolado |

---


## Provisionamento da infraestrutura

A infraestrutura foi separada em dois diretórios Terraform:

```text
infra/bootstrap
infra/staging
```

### 1. Bootstrap

O bootstrap cria o bucket S3 usado como remote state do Terraform.

```bash
cd infra/bootstrap
terraform init
terraform plan
terraform apply
```

Este passo deve ser executado antes do ambiente `staging`.

### 2. Staging

O ambiente `staging` utiliza o backend S3 criado no bootstrap.

```bash
cd infra/staging
terraform init
terraform plan
terraform apply
```

Após a criação do EKS, atualize o kubeconfig:

```bash
aws eks update-kubeconfig   --region us-east-1   --name mvp-oficina-staging-cluster
```

Valide o acesso ao cluster:

```bash
kubectl get nodes
```

### Observação sobre AWS Academy

Este projeto foi executado em uma conta **AWS Academy**. Por limitação de permissões do laboratório, não foi possível criar roles IAM específicas para o EKS. Por isso, o cluster EKS e o Node Group foram configurados utilizando a role existente `LabRole`.

Em uma conta AWS convencional, o recomendado seria criar roles IAM específicas para:

- EKS Cluster Role;
- EKS Node Group Role;
- permissões mínimas necessárias para cada recurso.

---

## Secrets do GitHub Actions

O ambiente `staging` do GitHub Actions utiliza variáveis e secrets para executar o deploy.

### Environment Variables

| Variável | Exemplo |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `AWS_ACCOUNT_ID` | `706619443268` |
| `ECR_REPOSITORY` | `mvp-oficina-api` |
| `EKS_CLUSTER_NAME` | `mvp-oficina-staging-cluster` |
| `K8S_NAMESPACE` | `staging` |

### Environment Secrets

| Secret | Finalidade |
|---|---|
| `AWS_ACCESS_KEY_ID` | Credencial temporária AWS Academy |
| `AWS_SECRET_ACCESS_KEY` | Credencial temporária AWS Academy |
| `AWS_SESSION_TOKEN` | Token temporário AWS Academy |
| `DB_URL` | URL de conexão async com o RDS |
| `ADMIN_NOME` | Nome do usuário admin criado no seed |
| `ADMIN_EMAIL` | E-mail do usuário admin |
| `ADMIN_PASSWORD` | Senha do usuário admin |

> As credenciais da AWS Academy expiram quando o laboratório é reiniciado. Antes de executar um novo deploy, atualize os secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `AWS_SESSION_TOKEN`.

---

## Deploy em Kubernetes

O deploy em staging é feito automaticamente pelo workflow `deploy-staging.yml` quando há push na branch `staging`.

Para disparar um novo deploy sem alterar código:

```bash
git commit --allow-empty -m "chore: trigger staging deployment"
git push origin staging
```

Comandos úteis para validação após o deploy:

```bash
kubectl get pods -n staging -o wide
kubectl get deployment mvp-oficina-api -n staging -o wide
kubectl get svc -n staging -o wide
kubectl get hpa -n staging
```

Verificar a imagem em execução:

```bash
kubectl get deployment mvp-oficina-api   -n staging   -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Logs da aplicação:

```bash
kubectl logs -n staging deployment/mvp-oficina-api --tail=100
```

Logs do Job de migrations:

```bash
kubectl logs -n staging job/mvp-oficina-api-migrations
```

---

## Escalabilidade automática

O HPA foi configurado para escalar a aplicação conforme consumo de CPU.

Acompanhar HPA e pods:

```bash
watch -n 2 "kubectl get hpa -n staging && echo '' && kubectl get pods -n staging"
```

Gerar carga interna no cluster:

```bash
kubectl run load-generator   -n staging   --rm -it   --restart=Never   --image=rakyll/hey   -- -z 5m -c 50 http://mvp-oficina-api-service.staging.svc.cluster.local/health
```

Acompanhar consumo dos pods:

```bash
watch -n 2 "kubectl top pods -n staging"
```

---

## Limpeza da infraestrutura

Para evitar custos, remova primeiro os recursos Kubernetes que criam Load Balancer:

```bash
kubectl delete -f k8s/staging/05-hpa.yaml --ignore-not-found
kubectl delete -f k8s/staging/04-service.yaml --ignore-not-found
kubectl delete -f k8s/staging/03-deployment.yaml --ignore-not-found
kubectl delete job mvp-oficina-api-migrations -n staging --ignore-not-found
kubectl delete secret mvp-oficina-api-secrets -n staging --ignore-not-found
kubectl delete namespace staging --ignore-not-found
```

Depois destrua a infraestrutura do staging:

```bash
cd infra/staging
terraform destroy
```

O diretório `infra/bootstrap` não precisa ser destruído entre execuções. Ele mantém apenas o bucket S3 usado como remote state. Ao final definitivo do projeto, o bootstrap também pode ser removido:

```bash
cd infra/bootstrap
terraform destroy
```

---

## Melhorias futuras

- Criar ambiente de produção associado à branch `main`.
- Adicionar rollback automático no workflow de deploy.
- Incluir API Gateway para autenticação centralizada, rate limiting e versionamento de APIs.
- Criar lifecycle policy no ECR para remoção automática de imagens antigas.
- Evoluir observabilidade com métricas, traces e dashboards.

---

## Decisões arquiteturais

As principais decisões arquiteturais do projeto estão registradas em ADRs na pasta [`docs/adr`](docs/adr).

- [ADR 1: Uso do PostgreSQL como banco de dados](docs/adr/0001-uso-do-postgresql.md)

---

## Status

MVP acadêmico da Fase 2 concluído para demonstração em ambiente `staging`.
