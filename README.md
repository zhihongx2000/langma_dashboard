# Lang Ma Dashboard

面向工程团队的本地开发仓库说明。当前仓库按 `Monorepo` 方式组织，主应用为 `Lang Ma Dashboard`，同时集成一个独立子系统 `subprojects/testcrawl`，用于考试院信息采集与工具联动。

本轮文档整理不改动运行时代码接口，也不搬迁真实目录；目标是先把项目结构、运行方式、配置边界和工业化缺口讲清楚，为后续工程化升级建立统一基线。

## 项目定位

仓库当前包含 4 个主要部分：

- 主前端工作台：基于 `Vite + React`，提供工作台首页、教务工具页、用户画像分析页。
- 主后端 API：基于 `FastAPI + SQLAlchemy`，提供用户画像分析、Prompt 版本管理、外部工具联动入口。
- Prompt 与业务文档：包括用户画像分析 Prompt、参考资料、需求与接口文档。
- `testcrawl` 子系统：独立的考试院信息采集工具，运行在单独端口，通过主后端进行状态检查与跳转联动。

## 技术栈

- 后端：Python `3.12`、FastAPI、SQLAlchemy、Pydantic Settings、LangChain
- 前端：Node.js、npm、Vite、React、TypeScript
- 本地运行：`uv`、PowerShell 脚本
- 默认开发数据库：SQLite

## 项目结构

按职责理解仓库，而不是把缓存、依赖和运行产物当成源码结构：

```text
.
├─ backend/                  # FastAPI API、服务层、配置、数据库访问、模型适配
├─ frontend/                 # React 页面、Vite 配置、前端 API 调用层
├─ prompts/                  # 用户画像分析 Prompt 与参考资料
├─ docs/                     # 接口文档、需求文档
├─ tests/                    # 主应用测试
├─ scripts/                  # 一键启动等本地脚本
├─ data/                     # 主应用本地 SQLite 数据与运行数据
├─ subprojects/
│  └─ testcrawl/             # 考试院信息采集子系统
├─ settings.yaml             # 主应用静态配置
├─ pyproject.toml            # Python 项目与依赖定义
└─ main.py                   # 主后端启动入口
```

关键目录说明：

- `backend/`
  - `api/`：路由注册与 HTTP 接口
  - `services/`：分析、会话、Prompt、模型、启动初始化等服务
  - `db/`：数据库模型、会话、基础设施
  - `config/`：`.env` 与 `settings.yaml` 读取逻辑
  - `model_adapters/`：模型适配层
- `frontend/src/`
  - `pages/`：当前主要页面为 `/`、`/education-tools`、`/persona-analysis`
  - `lib/`：前端对主后端的 API 封装
- `subprojects/testcrawl/`
  - `app/`：子系统后端 API、服务、模型
  - `web/`：子系统页面
  - `scripts/`：子系统本地启动与自检脚本
  - `tests/`：子系统测试

## 端口与服务关系

本地开发默认启动 3 个服务：

- 前端工作台：`http://127.0.0.1:3000`
- 主后端 API：`http://127.0.0.1:8000`
- `testcrawl` 子系统：`http://127.0.0.1:8001`

服务关系如下：

1. 前端工作台调用主后端 `/api/v1/*`。
2. 主后端负责用户画像分析、Prompt 管理，以及考试院工具的状态检查与跳转。
3. `testcrawl` 作为独立子服务运行在 `8001`，由主后端通过配置项 `EDUCATION_EXAM_CRAWLER_BASE_URL` 感知。

## 环境要求

建议本地环境：

- Python `3.12`
- `uv`
- Node.js + npm
- Windows PowerShell

## 初始化配置

根目录首次运行前，先初始化 `.env`：

```powershell
Copy-Item .env.example .env
```

至少确认以下变量存在：

```env
DEEPSEEK_API_KEY=your_key
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1
EDUCATION_EXAM_CRAWLER_BASE_URL=http://127.0.0.1:8001
```

配置边界说明：

- 根目录 `.env`：主后端使用，同时也为 `testcrawl` 联动提供基础地址。
- `settings.yaml`：主应用静态配置，包括应用名、API 前缀、默认数据库位置、模型选项、Prompt 路径。
- `subprojects/testcrawl/.env`：子系统自己的本地配置文件，后续需要进一步明确与根配置的职责边界。

## 快速启动

推荐使用根目录一键脚本，同时拉起 3 个服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-dev-all.ps1
```

脚本会尝试启动：

- `frontend`：`npm run dev`
- 主后端：`uv run python main.py`
- `testcrawl`：`subprojects/testcrawl/scripts/run_local_tool.ps1`

脚本末尾会执行健康检查：

- 前端：`http://127.0.0.1:3000/`
- 后端文档：`http://127.0.0.1:8000/docs`
- 子服务健康检查：`http://127.0.0.1:8001/health`

## 手动启动

### 1. 前端

```powershell
Set-Location .\frontend
npm install
npm run dev
```

### 2. 主后端

```powershell
uv python install 3.12
uv venv .venv --python 3.12
uv sync
uv run python main.py
```

### 3. `testcrawl` 子系统

推荐直接使用子项目脚本：

```powershell
Set-Location .\subprojects\testcrawl
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_tool.ps1
```

如需更多细节，可查看仓库内 `subprojects/testcrawl/README.md`。

## 测试入口

主应用测试位于根目录 `tests/`，子系统测试位于 `subprojects/testcrawl/tests/`。

常用测试命令：

```powershell
uv run pytest tests/backend/test_api_smoke.py -q
uv run pytest tests/backend/test_tools_launch.py -q
```

主应用全量测试：

```powershell
uv run pytest tests -q
```

子系统测试需在 `subprojects/testcrawl` 内按其依赖单独执行。

## 公共接口与入口

本轮不调整接口，但文档上需要明确这些入口是开发团队的公共使用面。

主后端：

- API 前缀：`/api/v1`
- 用户画像分析：`/persona-analysis/*`
- 考试院工具联动：`/tools/education-exam-crawler/*`
- Swagger 文档：`http://127.0.0.1:8000/docs`

`testcrawl` 子系统：

- 首页：`/`
- API 文档：`/docs`
- 健康检查：`/health`

前端页面：

- 工作台首页：`/`
- 教务工具页：`/education-tools`
- 用户画像分析页：`/persona-analysis`

## 文档索引

建议从以下位置继续了解业务与实现：

- `docs/api/`：接口文档
- `docs/tec_requirements/`：需求说明
- `prompts/`：用户画像分析 Prompt 与参考资料
- `subprojects/testcrawl/README.md`：子系统运行说明

## 当前工程现状与风险

以下问题已确认存在，本轮只记录，不直接执行清理或重构：

- 根目录当前不是 Git 工作树，后续需要补回正式仓库化管理。
- 根目录 `.gitignore` 过弱，尚未覆盖 `node_modules`、`__pycache__`、日志、数据库、虚拟环境等运行产物。
- 仓库视野中已混入 `.venv`、`.pytest_cache`、`node_modules`、SQLite 数据库、日志文件等内容，不利于识别真实源码结构。
- 根目录与子项目都存在 `.env`、数据库和缓存文件，后续需要定义更清晰的配置边界与数据边界。
- `frontend/README.md` 仍是模板文档，与当前项目事实不一致，后续应补齐为项目级前端说明。
- 当前页面与部分接口文本存在编码历史问题，后续需要统一文件编码和文本校验流程。

## 工业化演进路线

建议按以下阶段推进：

### Phase 1：文档与目录边界澄清

- 统一根 README、前端 README、子项目 README 的角色分工
- 让团队先对源码目录、运行入口、测试入口有一致认知
- 明确主应用与子系统的边界

### Phase 2：清理忽略规则与运行产物

- 补齐 `.gitignore`
- 从仓库中剥离依赖目录、缓存、日志、SQLite 数据库等本地运行产物
- 规范开发态数据目录与示例数据目录

### Phase 3：统一开发命令、测试入口、环境配置

- 统一根目录开发命令和子系统命令
- 明确 `.env`、`.env.example`、`settings.yaml`、子项目配置之间的职责
- 整理测试分层：单元测试、接口测试、端到端测试、子系统测试

### Phase 4：补齐 CI、部署、质量门禁、版本管理

- 恢复正式 Git 工作流
- 建立 CI 校验：测试、类型检查、基础质量门禁
- 补齐部署说明、环境区分、版本发布流程
- 为后续工业级应用演进预留监控、告警、配置管理与发布治理能力

## 当前已验证

以下主应用测试在当前仓库中已通过：

```powershell
uv run pytest tests/backend/test_api_smoke.py -q
uv run pytest tests/backend/test_tools_launch.py -q
```

## 后续建议

如果下一步要继续推进“工业级应用”，建议优先做这 3 件事：

1. 补齐根目录 `.gitignore`，把缓存、依赖、日志和数据库从协作视野里剥离。
2. 把 `frontend/README.md` 从模板文档改成真实项目文档。
3. 恢复正式 Git 仓库，并建立最小可用的 CI 校验链路。
