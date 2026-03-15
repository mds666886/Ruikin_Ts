# 演析 Pro MVP（前后端分离）

## 一键启动（推荐）
```bash
cp .env.example .env
docker compose up -d --build
```
打开：`http://localhost:8080`

## 本地开发
### 后端
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

前端默认代理地址可通过 `VITE_API_BASE` 指定（默认 `/api`）。

## 已实现 API
- `GET /api/health`
- `POST /api/projects`
- `POST /api/projects/bootstrap_demo`（一键导入示例）
- `GET /api/projects`
- `POST /api/files/upload`
- `POST /api/analysis/parse/<file_id>`
- `GET /api/analysis/project/<project_id>`
- `POST /api/scene/rewrite/<project_id>`
- `GET /api/scene/project/<project_id>`
- `POST /api/qa/generate/<project_id>`
- `GET /api/qa/project/<project_id>`
- `POST /api/evaluation/run/<project_id>`
- `POST /api/reports/generate/<evaluation_id>`
- `GET /api/reports/<report_id>`
- `GET /api/reports/download/<report_id>`

## 快速验证
```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
```

## 示例数据
- `samples/demo_script.txt`
