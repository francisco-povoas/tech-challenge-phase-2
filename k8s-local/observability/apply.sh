#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kubectl apply -f "${SCRIPT_DIR}/00-namespace.yaml"

kubectl create configmap otel-collector-config \
  --namespace observability \
  --from-file=config.yaml="${SCRIPT_DIR}/otel-collector-config.yaml" \
  --dry-run=client \
  --output yaml | kubectl apply -f -

kubectl apply -f "${SCRIPT_DIR}/01-jaeger.yaml"
kubectl apply -f "${SCRIPT_DIR}/02-otel-collector.yaml"
kubectl apply -f "${SCRIPT_DIR}/prometheus-config.yaml"
kubectl apply -f "${SCRIPT_DIR}/03-prometheus.yaml"
kubectl apply -f "${SCRIPT_DIR}/04-grafana.yaml"

for deployment in jaeger otel-collector prometheus grafana; do
  kubectl rollout status "deployment/${deployment}" -n observability --timeout=180s
done
