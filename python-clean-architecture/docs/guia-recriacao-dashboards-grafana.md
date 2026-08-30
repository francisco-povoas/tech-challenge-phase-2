# Como recriar os dashboards do Grafana

Este guia resume como reconstruir os dashboards de observabilidade da API caso seja necessário recriá-los manualmente.

> Observação: se o Grafana estiver usando volume persistente, um `docker compose down` normal não deve apagar os dashboards. O risco maior é recriar o container sem volume ou executar `docker compose down -v`.

---

## 1. Conectar o Grafana ao Prometheus

Acesse:

```text
http://localhost:3000
```

No Grafana:

```text
Connections
→ Data sources
→ Add data source
→ Prometheus
```

Configure a URL:

```text
http://prometheus:9090
```

Depois clique em:

```text
Save & test
```

---

## 2. Criar o dashboard

No Grafana:

```text
Dashboards
→ New
→ New dashboard
→ Add visualization
→ Prometheus
```

Em cada painel, utilize preferencialmente o modo **Builder**.

---

## 3. Painéis recomendados

| Painel | Metric | Filtros | Operations | Unidade |
|---|---|---|---|---|
| Requisições de autenticação/s | `http_server_duration_milliseconds_count` | `http_target=/api/v1/auth/token`, `http_method=POST` | `Rate` → `Sum` | req/s |
| Total acumulado de autenticações | `http_server_duration_milliseconds_count` | mesmos filtros | `Sum` | short |
| P95 - Latência autenticação | `http_server_duration_milliseconds_bucket` | mesmos filtros | `Rate` → `Sum by le` → `Histogram quantile 0.95` | ms |
| P99 - Latência autenticação | `http_server_duration_milliseconds_bucket` | mesmos filtros | `Rate` → `Sum by le` → `Histogram quantile 0.99` | ms |
| Erros de autenticação/s | `http_server_duration_milliseconds_count` | rota + método + `http_status_code =~ 4..|5..` | `Rate` → `Sum` | req/s |
| Requisições HTTP ativas | `http_server_active_requests` | opcional: `http_method` | `Sum` | short |
| Conexões DB em uso | `db_client_connections_usage` | `state=used` | `Sum` | short |

---

## 4. Configuração visual dos painéis

Para métricas ao longo do tempo:

```text
Visualization
→ Time series
```

Para P95 e P99:

```text
Standard options
→ Unit
→ Milliseconds (ms)
```

Para requisições por segundo e erros por segundo:

```text
Standard options
→ Unit
→ requests/sec
```

---

## 5. P95 no Builder, passo a passo

Este é o painel mais fácil de esquecer.

### Metric

```text
http_server_duration_milliseconds_bucket
```

### Label filters

```text
http_target = /api/v1/auth/token
http_method = POST
```

### Operations

```text
Rate
```

Depois:

```text
Sum
→ By: le
```

Depois:

```text
Histogram quantile
→ 0.95
```

Título sugerido:

```text
P95 - Latência da autenticação
```

Descrição sugerida:

```text
Latência abaixo da qual 95% das requisições de autenticação foram concluídas no período analisado.
```

Unidade:

```text
Milliseconds (ms)
```

---

## 6. P99

Duplique o painel de P95.

Altere apenas:

```text
Histogram quantile
0.95 → 0.99
```

Título:

```text
P99 - Latência da autenticação
```

---

## 7. Requisições de autenticação por segundo

### Metric

```text
http_server_duration_milliseconds_count
```

### Label filters

```text
http_target = /api/v1/auth/token
http_method = POST
```

### Operations

```text
Rate
→ Sum
```

O resultado representa:

```text
requisições por segundo
```

Título sugerido:

```text
Requisições de autenticação por segundo
```

---

## 8. Total acumulado de autenticações

### Metric

```text
http_server_duration_milliseconds_count
```

### Label filters

```text
http_target = /api/v1/auth/token
http_method = POST
```

### Operations

```text
Sum
```

Esse painel mostra o total acumulado observado pelo contador.

Título sugerido:

```text
Total acumulado de autenticações
```

---

## 9. Erros de autenticação por segundo

### Metric

```text
http_server_duration_milliseconds_count
```

### Label filters

```text
http_target = /api/v1/auth/token
http_method = POST
http_status_code =~ 4..|5..
```

### Operations

```text
Rate
→ Sum
```

Título sugerido:

```text
Erros de autenticação por segundo
```

---

## 10. Requisições HTTP ativas

### Metric

```text
http_server_active_requests
```

### Operations

```text
Sum
```

Não utilizar `Rate`, pois essa métrica representa um valor instantâneo.

Título sugerido:

```text
Requisições HTTP ativas
```

---

## 11. Conexões de banco em uso

### Metric

```text
db_client_connections_usage
```

### Label filters

```text
state = used
```

### Operations

```text
Sum
```

Não utilizar `Rate`.

Título sugerido:

```text
Conexões de banco em uso
```

---

## 12. Salvar o dashboard

Depois de montar os painéis:

```text
Save dashboard
```

Nome sugerido:

```text
Observabilidade - API Oficina
```

---

## 13. Persistência recomendada

Para evitar perder dashboards e histórico ao recriar containers, use volumes.

Exemplo:

```yaml
services:
  prometheus:
    volumes:
      - ./observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus

  grafana:
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  grafana-data:
  prometheus-data:
```

Com isso:

```text
grafana-data
→ dashboards, datasources e configurações do Grafana

prometheus-data
→ histórico das métricas do Prometheus
```

Evite:

```bash
docker compose -f docker-compose.test.yml down -v
```

se quiser manter os volumes.

---

## 14. Exportar o dashboard como JSON

Além do volume persistente, é recomendável exportar o dashboard do Grafana em JSON e guardar no repositório.

Estrutura sugerida:

```text
observability/
├── otel-collector/
│   └── config.yaml
├── prometheus/
│   └── prometheus.yml
└── grafana/
    └── dashboards/
        └── api-oficina.json
```

Assim, mesmo que os volumes sejam apagados, o dashboard pode ser importado novamente sem reconstruir todos os painéis manualmente.
