#!/bin/sh
set -e

COMPOSE_FILE="../docker-compose.test-ci.yml"

cleanup() {
  docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
}

trap cleanup EXIT

docker compose -f "$COMPOSE_FILE" up \
  --build \
  --abort-on-container-exit \
  --exit-code-from tests