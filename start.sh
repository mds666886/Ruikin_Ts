#!/usr/bin/env bash
set -e
cp -n .env.example .env || true
docker compose up -d --build
echo "演析 Pro 已启动: http://localhost:${APP_PORT:-8080}"
