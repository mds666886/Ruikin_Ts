@echo off
if not exist .env copy .env.example .env
docker compose up -d --build
echo 演析 Pro 已启动: http://localhost:8080
