#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-$(pwd)}"
export QUEUE_BACKEND="${QUEUE_BACKEND:-memory}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///output/test_monitor.db}"
export RULE_CONFIG_PATH="${RULE_CONFIG_PATH:-configs/rules.yaml}"

mkdir -p output

echo "Running pytest..."
pytest -v

echo "Validating Docker Compose..."
docker compose config

echo "CI checks completed successfully."
