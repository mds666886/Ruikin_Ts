# 演析 Pro 第一阶段：项目总设计（参赛版）

## 1. 项目总设计

### 1.1 项目简介（可直接放作品说明书）
“演析 Pro”是一套面向多场景汇报训练的智能演练平台。系统围绕“材料解析 → 场景化重构 → 问答预测 → 表达评估 → 复盘报告”构建完整闭环，帮助用户将 PPT/PDF/讲稿从“能展示”提升为“能讲清、能应答、能复盘”。

平台首版重点解决三类真实痛点：
1) **结构问题难发现**：汇报材料逻辑断层、重点不突出、节奏失衡；
2) **答辩问题难准备**：问题准备零散，缺少类型化与深度化预测；
3) **复盘问题难量化**：仅凭主观感觉改稿，缺少结构化评分和优先级建议。

### 1.2 项目亮点（评委视角）
1. **完整流程闭环**：不是“上传文件+总结”，而是覆盖“分析-演练-反馈-改进”的平台化流程。
2. **场景化策略引擎**：同一份材料在竞赛答辩/论文答辩/求职展示等场景下输出不同建议。
3. **结构化量化评分**：把“讲得好不好”拆成可计算指标（结构完整度、风险页、时间匹配度等）。
4. **低门槛可落地**：首版基于“前后端分离 + Flask API + Vue 页面 + 规则引擎”，无需重云依赖，适合赛事短周期交付。
5. **可扩展架构**：后续可平滑接入 ASR、LLM、多轮追问和个性化模型。
6. **傻瓜式部署**：支持 Docker Compose 一键启动，前后端分别打包、独立升级。

### 1.3 创新点（建议用于答辩）
1. **多场景重构创新**：首次将“场景角色目标”显式建模（如评委关心创新性、导师关心方法严谨、面试官关心贡献与落地），驱动建议差异化。
2. **演练任务图创新**：将上传内容拆分为“页面节点 + 逻辑边 + 风险标签”，支持自动定位断点与重排建议。
3. **问答类型矩阵创新**：按照基础理解题、追问题、质疑题、对比题、应用题进行结构化生成，不再只给随机问题。
4. **复盘优先级创新**：通过影响度 × 修复成本生成“先改什么”的清单，提升训练效率。
5. **竞赛可解释性创新**：每条评分与建议都可追溯到具体页面或文本片段，便于评委审查与展示。

### 1.4 应用场景
- 学科竞赛答辩（重点：创新点表达、评委质疑应对）
- 毕业论文答辩（重点：研究问题、方法、实验与结论链路）
- 课程汇报（重点：结构清晰、时间控制、知识点覆盖）
- 科研组会（重点：进展汇报、问题暴露、下一步计划）
- 求职项目展示（重点：个人贡献、技术难点、业务价值）
- 商业路演（重点：痛点-方案-商业模式-可行性）

### 1.5 目标用户
- **核心用户**：高校学生（竞赛队伍、毕业生、课程展示者）
- **扩展用户**：研究生、实验室成员、求职者、创业团队
- **管理用户**：指导老师、队长/组长（查看团队演练报告）

---

## 2. 系统功能架构

### 2.1 总体模块图（前后端分离）
1. **前端层（Vue + Vite + ECharts）**
   - 页面渲染、图表可视化、文件上传交互、报告导出。
2. **后端层（Flask API Service）**
   - 文件管理、解析调度、场景策略引擎、问答生成器、评分器、报告生成器。
3. **能力层（Core Engine）**
   - PPT/PDF/讲稿解析器、规则引擎、模板库、指标计算器。
4. **数据与存储层（SQLite + 文件目录）**
   - 项目、文件、页面分析、问答、评分、报告、日志。

### 2.2 前后端接口边界（必须固定）
- 前端只通过 REST API 访问后端，不直连数据库。
- 后端统一返回 JSON：`{code, message, data}`。
- 首版 API 分组：
  - `/api/projects`：项目创建、查询、场景切换
  - `/api/files`：上传、解析触发、解析状态
  - `/api/analysis`：页级分析、风险页、重点页
  - `/api/qa`：问答生成与分页查询
  - `/api/evaluation`：表达评估、评分计算
  - `/api/reports`：复盘报告生成、下载

### 2.3 打包与部署架构（傻瓜式）
1. **前端独立打包**：`npm run build` 生成 `dist/` 静态资源。
2. **后端独立打包**：`docker build` 生成 Flask API 镜像。
3. **Nginx 统一入口**：
   - `/` 指向前端静态页面；
   - `/api` 反向代理到 Flask 服务。
4. **Docker Compose 一键部署**：`docker compose up -d` 同时拉起 `frontend + backend + nginx`。
5. **升级策略**：前端改动只重发静态包；后端改动只重发 API 镜像。

### 2.4 五大核心功能（首版定义）
1. **材料解析模块**
   - 输入：PPT/PDF/TXT
   - 处理：提取页文本、标题候选、文本量、图文比例估计、关键词密度、逻辑连续性
   - 输出：页级结构化数据 + 风险页清单（如“文字过密”“疑似断点页”）

2. **场景化重构模块**
   - 输入：页级分析数据 + 场景类型
   - 处理：套用场景策略（权重与顺序建议）
   - 输出：页面排序建议、强调点建议、删减建议

3. **问答预测模块**
   - 输入：页面内容摘要 + 场景类型
   - 处理：按问题类型模板 + 规则组合生成候选问答
   - 输出：五类问题列表（基础/追问/质疑/对比/应用）

4. **表达评估模块（MVP 使用文本版）**
   - 输入：讲稿文本 + 目标时长 + 页面分析
   - 处理：估算语速、页面覆盖度、章节时长分配、超时风险
   - 输出：表达评分 + 漏讲页/超时段提示

5. **复盘报告模块**
   - 输入：结构评分 + 表达评分 + 风险与问答
   - 处理：规则融合 + 优先级计算
   - 输出：一份可下载报告（总分、短板、TOP改进项、下一轮练习建议）

### 2.5 特色能力（答辩可讲）
- **场景策略表可配置**：新增场景只改配置，不改核心代码。
- **评分可解释**：每个分数可展开“计算依据”。
- **链路可复现**：同一输入可重复得到稳定结果，适合教学和比赛演示。

---

## 3. 页面清单（前端 SPA）

### 3.1 页面总览（Vue 路由）
1. **首页 / 项目概览页**
   - 功能：创建项目、查看最近项目、流程引导。
2. **材料上传页**
   - 功能：上传 PPT/PDF/TXT、文件预检、解析任务发起。
3. **解析结果页**
   - 功能：页级统计图（文本量、风险页、逻辑断点）、重点页定位。
4. **场景重构页**
   - 功能：选择场景、查看重排建议、突出内容建议。
5. **问答预测页**
   - 功能：五类问题生成、按页过滤、导出问答卡片。
6. **表达评估页**
   - 功能：粘贴讲稿、设定目标时长、查看语速/覆盖度/超时风险。
7. **复盘报告页**
   - 功能：查看总分、问题优先级、改进建议，支持导出。
8. **系统设置页（MVP 可简化）**
   - 功能：默认参数配置（语速阈值、页均时长、评分权重）。

### 3.2 首版页面优先级（必须做）
- P0：首页、上传页、解析结果页、场景重构页、问答预测页、复盘报告页。
- P1：表达评估页（文本版）、设置页（可先做隐藏入口）。

### 3.3 前端工程目录（建议直接照抄）
```
frontend/
  src/
    api/            # axios 请求封装
    views/          # 页面组件
    components/     # 公共组件
    router/         # 路由
    stores/         # Pinia 状态
    assets/         # 静态资源
```

### 3.4 后端工程目录（建议直接照抄）
```
backend/
  app/
    api/            # Flask 蓝图
    services/       # 业务逻辑
    parsers/        # PPT/PDF/TXT 解析
    models/         # SQLAlchemy 模型
    core/           # 策略、评分、规则
  uploads/          # 上传文件目录
  reports/          # 导出报告目录
```

---

## 4. 数据库设计（SQLite，适合新手）

### 4.1 ER 关系（简版）
- `projects` 1---n `files`
- `files` 1---n `slides`
- `projects` 1---n `qa_items`
- `projects` 1---n `evaluation_runs`
- `evaluation_runs` 1---1 `reports`

### 4.2 表结构建议

#### 1) projects（项目表）
- `id` INTEGER PK
- `name` TEXT NOT NULL
- `scene_type` TEXT NOT NULL（competition/thesis/course/research/job/pitch）
- `target_minutes` INTEGER DEFAULT 10
- `created_at` DATETIME
- `updated_at` DATETIME

#### 2) files（文件表）
- `id` INTEGER PK
- `project_id` INTEGER FK
- `file_name` TEXT
- `file_type` TEXT（pptx/pdf/txt）
- `file_path` TEXT
- `parse_status` TEXT（pending/done/failed）
- `created_at` DATETIME

#### 3) slides（页面分析表）
- `id` INTEGER PK
- `file_id` INTEGER FK
- `page_no` INTEGER
- `title_guess` TEXT
- `text_count` INTEGER
- `image_ratio` REAL
- `is_key_page` INTEGER（0/1）
- `risk_tags` TEXT（JSON 字符串）
- `logic_score` REAL
- `summary` TEXT

#### 4) scene_suggestions（场景建议表）
- `id` INTEGER PK
- `project_id` INTEGER FK
- `scene_type` TEXT
- `suggestion_type` TEXT（order/highlight/cut）
- `content` TEXT
- `priority` INTEGER

#### 5) qa_items（问答表）
- `id` INTEGER PK
- `project_id` INTEGER FK
- `page_no` INTEGER
- `qa_type` TEXT（basic/followup/challenge/compare/apply）
- `question` TEXT
- `reference_answer` TEXT
- `difficulty` INTEGER（1-5）

#### 6) evaluation_runs（评估记录表）
- `id` INTEGER PK
- `project_id` INTEGER FK
- `script_text` TEXT
- `estimated_wpm` REAL
- `coverage_score` REAL
- `timing_score` REAL
- `expression_score` REAL
- `created_at` DATETIME

#### 7) reports（复盘报告表）
- `id` INTEGER PK
- `evaluation_id` INTEGER FK
- `total_score` REAL
- `structure_score` REAL
- `qa_score` REAL
- `risk_summary` TEXT
- `top_actions` TEXT（JSON 数组）
- `report_markdown` TEXT
- `created_at` DATETIME

### 4.3 为什么这样设计（给新手的结论）
- 表不多、关系直观、方便 Flask + SQLAlchemy 快速实现。
- `slides`、`qa_items`、`reports` 能直接支撑比赛演示最核心结果。
- 后续扩展音频评估时，可新增 `audio_runs` 表，不破坏现有结构。

---

## 5. MVP 开发顺序（强执行版）

### Sprint 0：项目骨架（0.5 天）
1. 初始化 `frontend(Vue)` + `backend(Flask API)` 双工程。
2. 跑通跨域调用（CORS）与健康检查接口 `/api/health`。
3. 跑通“创建项目 + 上传文件 + 保存数据库”。

### Sprint 1：材料解析（1~2 天）
1. 接入 `python-pptx`、`PyMuPDF`、TXT 读取。
2. 输出统一页结构（page_no/title_guess/text_count/...）。
3. 实现风险规则（文字过密、疑似无标题、逻辑断点）。

### Sprint 2：场景化重构 + 问答预测（1~2 天）
1. 建场景策略配置文件（JSON/YAML）。
2. 实现重排建议、突出建议、删减建议。
3. 生成五类问题与参考回答。

### Sprint 3：表达评估（文本版）+ 复盘报告（1 天）
1. 基于讲稿做语速/时长/覆盖度计算。
2. 计算结构分 + 表达分 + 问答准备度。
3. 生成报告页 + Markdown 导出。

### Sprint 4：打磨与参赛包装（1 天）
1. 加图表（ECharts）与示例项目。
2. 录制演示流程：上传→分析→问答→报告。
3. 完成说明书/PPT/答辩讲稿。

### Sprint 5：分离打包 + 傻瓜式部署（0.5 天）
1. 前端执行 `npm run build` 生成生产包。
2. 后端制作 Docker 镜像，固定依赖版本。
3. 编写 `docker-compose.yml` 与 `.env.example`。
4. 提供 `start.bat` / `start.sh` 一键启动脚本。
5. 输出《3分钟部署手册》（复制命令即可）。

### MVP 验收标准（必须满足）
1. 支持上传至少 1 个 PPT 或 PDF 并得到页级解析结果。
2. 可切换至少 3 个场景并输出不同建议。
3. 每个项目至少生成 15 个分类问题。
4. 能输出包含评分和改进优先级的复盘报告。
5. 全流程演示时长控制在 3~5 分钟内（便于现场展示）。
6. 在全新机器执行 `docker compose up -d` 可在 5 分钟内启动成功。

---

## 6. 傻瓜式部署方案（参赛现场推荐）

### 6.1 部署目标
- 非开发人员只需安装 Docker Desktop（Windows）或 Docker Engine（Linux），即可启动。
- 不要求本地安装 Python/Node。

### 6.2 一键部署步骤（给评委/老师）
1. 打开项目目录。
2. 执行：`cp .env.example .env`（Windows 用 `copy`）。
3. 执行：`docker compose up -d --build`。
4. 浏览器访问：`http://localhost:8080`。

### 6.3 打包产物清单（提交作品时必须有）
- `frontend-dist.zip`：前端静态包。
- `backend-image.tar`：后端镜像离线包（可选）。
- `docker-compose.yml`：编排文件。
- `.env.example`：环境变量模板。
- `start.sh` 与 `start.bat`：一键启动脚本。
- `DEPLOY.md`：图文部署手册。

### 6.4 风险兜底（现场无网）
- 提前准备 `backend-image.tar`，现场 `docker load -i backend-image.tar` 直接导入。
- 前端静态资源本地化，不依赖 CDN。
- 示例数据内置，避免因上传文件失败导致演示中断。
