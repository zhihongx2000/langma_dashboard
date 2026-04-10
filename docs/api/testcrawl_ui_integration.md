# testcrawl UI 接入文档

## 1. 目标与定位

`testcrawl` 是 `langma_dashboard` 下的一个子项目，提供「考试院信息收集工具」对应的爬虫看板 UI 与后端接口。

- 子项目路径：`subprojects/testcrawl`
- 主项目路径：`D:\kanban\langma_dashboard`
- UI 入口（本地）：`http://127.0.0.1:8000/test-ui`

本文件用于后续开发接入该 UI、理解项目结构与接口边界。

## 2. 子项目结构（核心）

`subprojects/testcrawl` 关键目录：

- `app/main.py`：FastAPI 启动入口，挂载页面与路由
- `app/routers/`：业务 API 路由
  - `provinces.py` / `sections.py` / `contents.py`：省份、栏目、内容查询
  - `crawl.py`：触发爬虫任务、任务状态、更新报告
  - `test_local.py`：各省“一级/二级板块”抓取接口 + 聊天/总结接口
  - `updates.py`：更新日志查询与标记
- `app/services/`：各省站点解析与抓取实现
- `ui/test_ui.html`：当前主要联调与展示 UI（四宫格看板）
- `ui/index.html`：基础版 UI
- `scripts/run_local_test.ps1`：本地测试启动脚本
- `tests/`：接口与解析逻辑测试

## 3. 启动方式

在 `subprojects/testcrawl` 下：

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

快捷本地测试：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_test.ps1
```

## 4. 页面入口与路由挂载

`app/main.py` 中：

- `GET /` -> `ui/index.html`
- `GET /test-ui` -> `ui/test_ui.html`
- `GET /health` -> 健康检查
- `include_router(...)` 挂载了 provinces/sections/contents/crawl/updates/debug/test-local

## 5. UI 主要接口（当前 test-ui 使用）

### 5.1 基础数据流

- `GET /api/provinces`
- `GET /api/provinces/{province_id}/sections`
- `GET /api/sections/{section_id}/contents?page=1&page_size=50`
- `GET /api/contents/{content_id}`

### 5.2 搜索

- `GET /api/contents/search?keyword=...&province_id=...`
- `GET /api/search/ai?query=...&province_id=...`

### 5.3 爬虫触发与报告

- `POST /api/crawl/trigger`
  - body: `{ "type": "province|section|full", "province_id"?: number, "section_id"?: number }`
- `GET /api/crawl/status/{job_id}`
- `GET /api/crawl/report-latest`
- `GET /api/crawl/report/{job_id}`

### 5.4 test-local 省份板块接口

统一前缀：`/api/test/*/levels`

例如：

- `/api/test/sichuan/levels`
- `/api/test/qinghai/levels`
- `/api/test/hainan/levels`
- `/api/test/jiangsu/levels`
- `/api/test/xinjiang/levels`
- `/api/test/xizang/levels`
- 以及 `test_local.py` 中其他省份 levels 接口

正文抓取：

- `GET /api/test/page/content?url=...`
- `GET /api/test/sichuan/content?url=...`

聊天与摘要：

- `POST /api/test/chat`
- `POST /api/test/ai/chat`（兼容路径）
- `POST /api/test/summarize-policy`

## 6. 当前前端交互特性（test_ui）

`ui/test_ui.html` 已实现：

- 顶栏操作：
  - 刷新当前省份
  - 爬虫加载（并发 5 预热所有省份一/二级）
  - 近一周爬虫信息（读取本地缓存的二级日期并排序）
- 省份详情：
  - 「查看原网址」按钮
  - 「成绩查询」按钮（位于标题右侧）
- 自动行为：
  - 页面初始化后后台静默预热（不弹窗）
- 缓存机制：
  - `jget` 请求结果在页面内存缓存，后续切换省份可秒开

## 7. 与主项目前端的接入方式

主项目文件：`frontend/src/pages/EducationTools.tsx`

「考试院信息收集工具」已接入同款按钮（与“立即开始分析”同风格）并跳转：

- `window.location.href = "http://127.0.0.1:8000/test-ui"`

如需改为新标签页：

```ts
window.open("http://127.0.0.1:8000/test-ui", "_blank", "noopener,noreferrer");
```

## 8. 对接注意事项

1. 先确保 `testcrawl` 服务已启动，再从主项目点击跳转。
2. 若端口不是 `8000`，同步修改主项目跳转地址。
3. `POST /api/crawl/trigger` 当前为无鉴权（仅适合本机/内网），公网部署需在网关或服务层恢复鉴权。
4. 若看板数据为空，优先检查：
   - 站点可达性（网络/反爬）
   - Playwright 浏览器是否安装
   - `.env` 中爬虫相关配置

## 9. 推荐后续工作

- 把 `testcrawl` 的 base URL 抽到主项目环境变量（例如 `VITE_TESTCRAWL_UI_BASE_URL`）
- 增加一个主项目内嵌页（iframe 或代理路由）替代直接跨服务跳转
- 为 `testcrawl` 增加统一 OpenAPI 摘要文档，方便多人协作对接

