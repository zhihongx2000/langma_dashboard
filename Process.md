# Process

更新时间：2026-03-31

## 1. 当前任务目标

一期优先目标是完成“用户画像分析工具”的可用闭环，范围分为两部分：

1. 后端闭环
   - 导入聊天记录文本。
   - 解析为结构化消息。
   - 调用 LLM 生成结构化分析结果。
   - 将结论、理由、原话、时间点落库到 SQLite。
   - 通过 FastAPI 对前端提供稳定接口。

2. 前端联调
   - 以现有页面为基础，把 PersonaAnalysis 页从 mock 数据切换到真实后端接口。
   - 保留模型切换、Prompt 版本切换和实验区能力。
   - 前端最终展示的分析结果要能回溯到原始证据。

## 2. 当前已完成内容

### 2.1 文档与契约

- 已有需求文档：[docs/tec_requirements/user_profiling_analysis.md](docs/tec_requirements/user_profiling_analysis.md)
- 已有接口文档：[docs/api/user_profiling_analysis.md](docs/api/user_profiling_analysis.md)
- 已有结构化 Prompt：[prompts/prompt_for_user_profile.md](prompts/prompt_for_user_profile.md)

### 2.2 后端基础能力

后端已经具备以下能力：

- FastAPI 应用入口：[backend/main.py](backend/main.py)
- 根级启动封装：[main.py](main.py)
- SQLite ORM 表定义：[backend/db/models.py](backend/db/models.py)
- 用户画像分析路由：[backend/api/routes/persona_analysis.py](backend/api/routes/persona_analysis.py)
- 分析服务：[backend/services/analysis_service.py](backend/services/analysis_service.py)
- 模型配置服务：[backend/services/model_service.py](backend/services/model_service.py)
- 模型适配层：[backend/model_adapters/persona_analysis.py](backend/model_adapters/persona_analysis.py)

目前后端已经支持：

- 获取模型列表
- 获取 Prompt 版本列表
- 粘贴文本导入会话
- 获取会话消息
- 手动触发分析
- 获取最近一次分析结果

### 2.3 结构化分析与落库

当前结构化结果已经支持以下大类：

- persona_tags
- pain_points
- deal_closing_points
- churn_points
- high_frequency_points
- risk_assessment
- smart_replies

每条结论都支持理由与证据，证据包含：

- message_index
- speaker
- speaker_role
- quote
- timestamp
- note

SQLite 中已落地的核心表：

- conversation_sessions
- conversation_sources
- conversation_messages
- analysis_runs
- analysis_findings
- finding_evidences
- prompt_versions

## 3. 已完成的真实联调验证

### 3.1 使用样例

真实联调用的样例文件：

- [tests/e2e/user_profile_example.md](tests/e2e/user_profile_example.md)

### 3.2 联调过程中修复的问题

已修复两个影响真实调用的问题：

1. Prompt 模板转义问题
   - 原因：Prompt 中的 JSON 示例花括号被 LangChain 的 ChatPromptTemplate 当成模板变量解析。
   - 修复位置：[backend/model_adapters/persona_analysis.py](backend/model_adapters/persona_analysis.py)
   - 处理方式：把 system prompt 改成静态 SystemMessage。

2. 超时策略过短
   - 原因：结构化输出较长时，请求在 60 秒超时内无法稳定返回。
   - 修复位置：[backend/model_adapters/persona_analysis.py](backend/model_adapters/persona_analysis.py)
   - 处理方式：将 request_timeout 提高到 180 秒，并关闭自动重试。

### 3.3 已验证成功的端到端结果

已成功走通以下完整链路：

- POST /api/v1/persona-analysis/sessions/import-text
- POST /api/v1/persona-analysis/sessions/{session_id}/analyze
- GET /api/v1/persona-analysis/sessions/{session_id}/analysis/latest
- 回查 SQLite 的 analysis_runs / analysis_findings / finding_evidences

#### 成功样例 1：gpt-4o-academic

- 数据库文件：[data/e2e_real_analysis_chat_1774947802.db](data/e2e_real_analysis_chat_1774947802.db)
- model_key：gpt-4o-academic
- 导入消息数：18
- 分析耗时：90.96 秒
- 分析结果：succeeded
- SQLite 落库结果：
  - analysis_run：1 条
  - findings：6 条
  - evidences：18 条
  - raw_response：已保存

#### 成功样例 2：langma-o1-pro（当前默认模型）

- 数据库文件：[data/e2e_real_analysis_reasoner_1774947955.db](data/e2e_real_analysis_reasoner_1774947955.db)
- model_key：langma-o1-pro
- 导入消息数：18
- 分析耗时：234.35 秒
- 分析结果：succeeded
- SQLite 落库结果：
  - analysis_run：1 条
  - findings：9 条
  - evidences：24 条
  - raw_response：已保存

结论：

- 真实模型调用已经跑通，不是 mock。
- 结构化结果已经能成功写入 SQLite。
- 默认模型可用，但延迟明显更高。
- 前端联调阶段建议优先使用 gpt-4o-academic 以降低等待时间。

## 4. 当前测试状态

后端回归测试已通过：

- tests/backend/test_chat_parser.py
- tests/backend/test_api_smoke.py
- tests/backend/test_analysis_service.py

最近一次回归结果：3 passed。

## 5. 当前未完成事项

### 5.1 前端仍然是 mock 页面

当前页面文件：[frontend/src/pages/PersonaAnalysis.tsx](frontend/src/pages/PersonaAnalysis.tsx)

现状：

- 对话预览使用本地 MOCK_CHAT_DATA。
- 右侧分析结果也是写死的静态展示。
- 上传按钮仍然只是前端提示，未真正上传到后端。
- 当前页面还没有调用 /api/v1/persona-analysis 接口。

### 5.2 前端与后端还没有真正连通

需要继续完成：

1. 在前端新增 API 调用层。
2. 用真实接口替换 PersonaAnalysis.tsx 中的 mock 数据。
3. 将上传、导入、分析触发、结果刷新接到后端。
4. 处理开发环境跨域。

注意：

- 当前后端入口中还没有配置 CORS 中间件。
- 如果前端直接从 3000 调 8000，需要补 CORS 或改 Vite 代理。

### 5.3 模型运行参数还未配置化

当前 request_timeout 和 max_retries 仍写在 [backend/model_adapters/persona_analysis.py](backend/model_adapters/persona_analysis.py) 中。

更合理的下一步是把它们迁移到 [settings.yaml](settings.yaml) 中，便于后续调参。

## 6. 建议下一步优先级

建议下一位接手的人按这个顺序继续：

1. 给后端补 CORS 或给前端补代理。
2. 在前端封装 persona-analysis API 调用层。
3. 先接通以下最小闭环：
   - 获取模型列表
   - 获取 Prompt 版本列表
   - 导入文本
   - 触发分析
   - 拉取最新结果
4. 用真实返回结果替换右侧分析面板。
5. 把左侧对话预览切换到后端消息列表。
6. 最后再优化加载态、失败态、证据展示和实验区交互。

## 7. 前端当前状态说明

前端工程入口：

- [frontend/package.json](frontend/package.json)
- [frontend/src/main.tsx](frontend/src/main.tsx)
- [frontend/src/App.tsx](frontend/src/App.tsx)

PersonaAnalysis 页面访问路径：

- /persona-analysis

当前前端不是后端联调版，而是 Stitch / AI Studio 产出的静态原型页面。其 README 和 Vite 配置仍保留 Gemini 相关配置，但当前 PersonaAnalysis 页面本身并没有真正调用 Gemini，也没有真正调用本仓库的 FastAPI 后端。

## 8. 启动命令

### 8.1 后端启动

首次安装依赖：

```bash
cd /home/hong/lang_ma_dashboard
uv sync --dev
```

启动后端：

```bash
cd /home/hong/lang_ma_dashboard
uv run python main.py
```

启动后可访问：

- FastAPI 服务：http://127.0.0.1:8000
- Swagger 文档：http://127.0.0.1:8000/docs

### 8.2 前端启动

首次安装依赖：

```bash
cd /home/hong/lang_ma_dashboard/frontend
npm install
```

启动前端：

```bash
cd /home/hong/lang_ma_dashboard/frontend
npm run dev
```

启动后可访问：

- 前端首页：http://127.0.0.1:3000
- 用户画像页：http://127.0.0.1:3000/persona-analysis

### 8.3 当前调试预期

请注意：

- 现在同时启动前后端，只能做到“前端静态页面可看、后端接口可调”。
- PersonaAnalysis 页面默认不会自动显示后端真实分析结果，因为前端尚未接线。
- 如果你的目标是“在页面里直接看到真实分析结果”，下一步必须继续做前端接口接入。

## 9. 调试时推荐模型

前端或接口联调阶段建议优先使用：

- gpt-4o-academic

原因：

- 已验证真实可用。
- 返回结构化结果稳定。
- 明显快于默认的 langma-o1-pro。

## 10. 接手时最值得先读的文件

建议下一位接手的人先读这些文件：

1. [docs/api/user_profiling_analysis.md](docs/api/user_profiling_analysis.md)
2. [prompts/prompt_for_user_profile.md](prompts/prompt_for_user_profile.md)
3. [backend/api/routes/persona_analysis.py](backend/api/routes/persona_analysis.py)
4. [backend/services/analysis_service.py](backend/services/analysis_service.py)
5. [backend/model_adapters/persona_analysis.py](backend/model_adapters/persona_analysis.py)
6. [frontend/src/pages/PersonaAnalysis.tsx](frontend/src/pages/PersonaAnalysis.tsx)
7. [tests/e2e/user_profile_example.md](tests/e2e/user_profile_example.md)
