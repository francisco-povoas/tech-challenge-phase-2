# Kubernetes local

Este ambiente sobe a API e PostgreSQL no namespace `local`, e Jaeger, OpenTelemetry
Collector, Prometheus e Grafana no namespace `observability`.

```text
FastAPI → OTel Collector → Jaeger
                     └──→ Prometheus → Grafana
```

## Subir o ambiente

Os comandos abaixo usam Minikube. O Metrics Server é necessário pelo HPA.

```bash
minikube start
minikube addons enable metrics-server

docker build -t mvp-oficina-api:local .
minikube image load mvp-oficina-api:local

cp k8s-local/01-secret.yaml.example k8s-local/01-secret.yaml
# edite k8s-local/01-secret.yaml: DB_URL e POSTGRES_PASSWORD devem usar a mesma senha
```

Suba toda a observabilidade de uma vez. O script cria o ConfigMap do Collector
a partir de `otel-collector-config.yaml`, aplica os quatro componentes e espera
os respectivos rollouts terminarem.

```bash
./k8s-local/observability/apply.sh
```

Depois suba a aplicação:

```bash
kubectl apply -f k8s-local/00-namespace.yaml
kubectl apply -f k8s-local/01-secret.yaml
kubectl apply -f k8s-local/02-postgres.yaml
kubectl rollout status deployment/mvp-oficina-postgres -n local --timeout=180s

kubectl apply -f k8s-local/03-job-migrations.yaml
kubectl wait --for=condition=complete job/mvp-oficina-api-migrations -n local --timeout=180s

kubectl apply -f k8s-local/04-deployment.yaml
kubectl apply -f k8s-local/05-service.yaml
kubectl apply -f k8s-local/06-hpa.yaml
kubectl rollout status deployment/mvp-oficina-api -n local --timeout=180s
```

A FastAPI é iniciada por `opentelemetry-instrument` e envia sinais via OTLP/gRPC
para `otel-collector.observability.svc.cluster.local:4317`.

## Acessar e validar

Todos os UIs locais usam `NodePort`; não é necessário `kubectl port-forward`.

```bash
minikube service mvp-oficina-api-service -n local --url
minikube service jaeger -n observability --url
minikube service prometheus -n observability --url
minikube service grafana -n observability --url
```

Gere um trace e, na UI do Jaeger, procure pelo serviço `mvp-oficina-api`:

```bash
curl "$(minikube service mvp-oficina-api-service -n local --url)/health-check"
```

Grafana: usuário `admin`, senha `admin`. O datasource Prometheus e o dashboard
`Observabilidade - API Oficina` são provisionados automaticamente.

## Diagnóstico e atualização

```bash
kubectl get pods,svc -n local
kubectl get pods,svc -n observability
kubectl logs -f -n observability deployment/otel-collector
kubectl logs -n local deployment/mvp-oficina-api
```

Após editar `k8s-local/observability/otel-collector-config.yaml`, reaplique a
stack e reinicie o Collector para que ele leia a configuração nova:

```bash
./k8s-local/observability/apply.sh
kubectl rollout restart deployment/otel-collector -n observability
```

Para remover o ambiente:

```bash
kubectl delete namespace local observability
```
