# 用户画像分析接口说明

## 1. 文档目标

本文档用于支持当前用户画像分析页的一期开发，范围仅覆盖单会话聊天记录的上传、解析、分析、结果回显，以及 Prompt 版本管理。

当前页面来源：

- [frontend/src/pages/PersonaAnalysis.tsx](frontend/src/pages/PersonaAnalysis.tsx)

本文档默认后端技术栈为：

- FastAPI
- SQLite
- LangChain 1.0+

## 2. 一期范围

### 已纳入一期

- 左侧侧栏的文件夹与会话项管理。
- 从文件夹上传文本聊天记录并自动生成会话。
- 读取标准化消息列表并渲染聊天预览。
- 触发 AI 分析并回显用户标签、痛点、成交节点、流失节点、高频节点、风险评估和推荐话术。
- 模型列表读取。
- Prompt 版本列表、保存、编辑、启用。

### 不在一期

- 团队维度批量复盘。
- docx 深解析。
- 截图 OCR。
- 企业微信实时回写。
- 登录与权限。

## 3. 统一约定

### 3.1 基础路径

- 接口前缀：/api/v1/persona-analysis

### 3.2 鉴权

- 一期不做登录与权限，暂不设计鉴权头。
- 若后续补鉴权，优先在网关或通用中间件层扩展，不改业务字段结构。

### 3.3 内容类型

- JSON 接口：application/json
- 文件上传接口：multipart/form-data

### 3.4 时间格式

- 对外统一返回 ISO 8601 UTC 字符串，字段名使用 _at 结尾，例如 created_at。
- 若原始聊天记录只有文本时间，保留原值在 timestamp_text 字段。

### 3.5 通用成功响应

```json
{
  "request_id": "req_01JXYZ...",
  "data": {}
}
```

### 3.6 通用错误响应

```json
{
  "request_id": "req_01JXYZ...",
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "当前文件类型暂不支持",
    "details": []
  }
}
```

### 3.7 关键枚举


| 枚举字段            | 允许值                                                                                                      | 说明       |
| --------------- | -------------------------------------------------------------------------------------------------------- | -------- |
| item_type       | folder, session                                                                                          | 侧栏项类型    |
| source_type     | upload_file, pasted_text, imported_structured_text                                                       | 导入来源     |
| parse_status    | pending, parsing, parsed, failed                                                                         | 原始内容解析状态 |
| speaker_role    | teacher, student, unknown                                                                                | 标准化消息角色  |
| analysis_status | pending, running, succeeded, failed                                                                      | 分析状态     |
| finding_type    | pain_point, deal_closing_point, churn_point, high_frequency_point, persona_tag, risk_reason, smart_reply | 结构化结论类型  |
| risk_level      | low, medium, high, unknown                                                                               | 风险等级     |
| trigger_source  | upload_auto, manual_rerun, prompt_change                                                                 | 分析触发来源   |


## 4. 核心对象字段表

### 4.1 SidebarItem


| 字段                 | 类型              | 必填  | 说明                             |
| ------------------ | --------------- | --- | ------------------------------ |
| item_id            | string          | 是   | 侧栏项主键，folder 与 session 共用此字段名  |
| item_type          | string          | 是   | folder 或 session               |
| title              | string          | 是   | 展示标题                           |
| is_pinned          | boolean         | 是   | 是否置顶                           |
| folder_id          | string or null  | 否   | 当 item_type=session 时可关联所属文件夹  |
| session_count      | integer or null | 否   | 当 item_type=folder 时返回该文件夹下会话数 |
| latest_activity_at | string or null  | 否   | 最近活动时间                         |
| created_at         | string          | 是   | 创建时间                           |
| updated_at         | string          | 是   | 更新时间                           |


### 4.2 ConversationMessage


| 字段             | 类型             | 必填  | 说明                      |
| -------------- | -------------- | --- | ----------------------- |
| message_id     | string         | 是   | 消息主键                    |
| message_index  | integer        | 是   | 会话内顺序号，从 1 开始           |
| speaker_role   | string         | 是   | teacher、student、unknown |
| speaker_name   | string         | 否   | 原始昵称                    |
| timestamp_text | string or null | 否   | 原始文本时间                  |
| timestamp_at   | string or null | 否   | 标准化后的时间                 |
| content        | string         | 是   | 标准化正文                   |
| raw_content    | string         | 否   | 原始正文                    |
| parse_note     | string or null | 否   | 解析备注，例如“昵称无法稳定识别”       |


### 4.3 EvidenceItem


| 字段            | 类型             | 必填  | 说明         |
| ------------- | -------------- | --- | ---------- |
| evidence_id   | string         | 是   | 证据主键       |
| message_id    | string         | 否   | 关联的标准化消息主键 |
| message_index | integer        | 否   | 关联消息序号     |
| speaker       | string         | 否   | 说话人        |
| speaker_role  | string         | 否   | 角色         |
| quote         | string         | 是   | 触发判断的原话    |
| timestamp     | string or null | 否   | 触发判断的时间点   |
| note          | string or null | 否   | 证据补充说明     |


### 4.4 FindingItem


| 字段                | 类型             | 必填  | 说明                                     |
| ----------------- | -------------- | --- | -------------------------------------- |
| finding_id        | string         | 是   | 结论主键                                   |
| finding_type      | string         | 是   | 见 finding_type 枚举                      |
| title             | string         | 是   | 结论标题或标签名                               |
| summary           | string         | 是   | 结论摘要                                   |
| reason            | string         | 是   | 判断理由                                   |
| confidence        | number         | 是   | 0 到 1 之间的小数                            |
| severity          | string or null | 否   | low、medium、high，仅对部分结论适用               |
| resolution_status | string or null | 否   | unresolved、partially_resolved、resolved |
| evidences         | array          | 是   | 触发判断的原话与时间点                            |


### 4.5 RiskAssessment


| 字段        | 类型      | 必填  | 说明                      |
| --------- | ------- | --- | ----------------------- |
| level     | string  | 是   | low、medium、high、unknown |
| score     | integer | 是   | 0 到 100                 |
| summary   | string  | 是   | 风险摘要                    |
| reason    | string  | 是   | 风险判断原因                  |
| evidences | array   | 是   | 风险判断证据                  |


### 4.6 SmartReply


| 字段        | 类型     | 必填  | 说明            |
| --------- | ------ | --- | ------------- |
| reply_id  | string | 是   | 话术主键          |
| style     | string | 是   | 例如专业型、安抚型、推进型 |
| content   | string | 是   | 推荐回复内容        |
| reason    | string | 是   | 生成该话术的理由      |
| evidences | array  | 是   | 话术对应的证据来源     |


### 4.7 PromptVersion


| 字段                | 类型             | 必填  | 说明                          |
| ----------------- | -------------- | --- | --------------------------- |
| prompt_version_id | string         | 是   | Prompt 版本主键                 |
| tool_key          | string         | 是   | 固定为 user_profiling_analysis |
| task_key          | string         | 是   | 固定为 analyze_chat            |
| version_label     | string         | 是   | 例如 v1、v1.1                  |
| version_note      | string or null | 否   | 版本备注                        |
| content           | string         | 是   | Prompt 正文                   |
| is_active         | boolean        | 是   | 是否当前启用                      |
| created_at        | string         | 是   | 创建时间                        |
| updated_at        | string         | 是   | 更新时间                        |


### 4.8 ModelOption


| 字段             | 类型      | 必填  | 说明             |
| -------------- | ------- | --- | -------------- |
| provider_key   | string  | 是   | 模型供应商键         |
| provider_label | string  | 是   | 供应商显示名         |
| model_key      | string  | 是   | 模型键            |
| model_label    | string  | 是   | 模型显示名          |
| is_default     | boolean | 是   | 是否默认模型         |
| is_enabled     | boolean | 是   | 是否可选           |
| temperature    | number  | 否   | 默认 temperature |
| max_tokens     | integer | 否   | 默认 max tokens  |


## 5. 接口清单

### 5.1 获取侧栏数据

- 方法：GET
- 路径：/api/v1/persona-analysis/sidebar
- 用途：加载左侧文件夹和会话项。

请求字段：无。

响应字段：


| 字段                     | 类型             | 必填  | 说明                      |
| ---------------------- | -------------- | --- | ----------------------- |
| data.items             | array          | 是   | 侧栏平铺列表，前端按 item_type 渲染 |
| data.active_session_id | string or null | 否   | 最近活跃会话                  |


### 5.2 新建文件夹

- 方法：POST
- 路径：/api/v1/persona-analysis/folders
- 用途：对应右键空白处“新建文件夹”。

请求字段：


| 字段        | 类型      | 必填  | 说明                   |
| --------- | ------- | --- | -------------------- |
| title     | string  | 否   | 文件夹标题，缺省时后端生成“新建文件夹” |
| is_pinned | boolean | 否   | 是否置顶，默认 false        |


响应字段：


| 字段        | 类型          | 必填  | 说明       |
| --------- | ----------- | --- | -------- |
| data.item | SidebarItem | 是   | 新建后的文件夹项 |


### 5.3 更新文件夹

- 方法：PATCH
- 路径：/api/v1/persona-analysis/folders/{folderId}
- 用途：重命名、置顶或取消置顶文件夹。

请求字段：


| 字段        | 类型      | 必填  | 说明     |
| --------- | ------- | --- | ------ |
| title     | string  | 否   | 新标题    |
| is_pinned | boolean | 否   | 新的置顶状态 |


响应字段：


| 字段        | 类型          | 必填  | 说明       |
| --------- | ----------- | --- | -------- |
| data.item | SidebarItem | 是   | 更新后的文件夹项 |


### 5.3.1 删除文件夹

- 方法：DELETE
- 路径：/api/v1/persona-analysis/folders/{folderId}
- 用途：删除文件夹。若该文件夹下仍有会话，会连同消息、分析结果和证据一起删除。

请求字段：无。

响应字段：


| 字段             | 类型     | 必填  | 说明         |
| -------------- | ------ | --- | ---------- |
| data.item_id   | string | 是   | 已删除文件夹主键   |
| data.item_type | string | 是   | 固定为 folder |


### 5.4 新建空会话

- 方法：POST
- 路径：/api/v1/persona-analysis/sessions
- 用途：对应页面顶部“新建对话”。

请求字段：


| 字段        | 类型             | 必填  | 说明                |
| --------- | -------------- | --- | ----------------- |
| title     | string         | 否   | 会话标题，缺省时后端生成“新对话” |
| folder_id | string or null | 否   | 所属文件夹             |
| is_pinned | boolean        | 否   | 是否置顶，默认 false     |


响应字段：


| 字段        | 类型          | 必填  | 说明      |
| --------- | ----------- | --- | ------- |
| data.item | SidebarItem | 是   | 新建后的会话项 |


### 5.5 通过粘贴文本创建会话

- 方法：POST
- 路径：/api/v1/persona-analysis/sessions/import-text
- 用途：支持后续从文本输入框直接粘贴聊天记录并生成会话。

请求字段：


| 字段                | 类型             | 必填  | 说明               |
| ----------------- | -------------- | --- | ---------------- |
| raw_text          | string         | 是   | 原始聊天文本           |
| title             | string         | 否   | 会话标题             |
| folder_id         | string or null | 否   | 所属文件夹            |
| source_type       | string         | 否   | 默认 pasted_text   |
| auto_analyze      | boolean        | 否   | 是否导入后自动分析        |
| model_key         | string         | 否   | 自动分析所用模型         |
| prompt_version_id | string         | 否   | 自动分析所用 Prompt 版本 |


响应字段：


| 字段                   | 类型             | 必填  | 说明                                  |
| -------------------- | -------------- | --- | ----------------------------------- |
| data.session         | SidebarItem    | 是   | 新创建的会话项                             |
| data.source_id       | string         | 是   | 原始导入记录主键                            |
| data.parse_status    | string         | 是   | parsed 或 failed                     |
| data.message_count   | integer        | 是   | 成功解析出的消息数                           |
| data.role_summary    | object         | 是   | 角色分布汇总                              |
| data.latest_analysis | object or null | 否   | 若 auto_analyze=true 且成功，则返回最新分析结果摘要 |


### 5.6 更新会话元信息

- 方法：PATCH
- 路径：/api/v1/persona-analysis/sessions/{sessionId}
- 用途：重命名会话、置顶或调整所属文件夹。

请求字段：


| 字段        | 类型             | 必填  | 说明     |
| --------- | -------------- | --- | ------ |
| title     | string         | 否   | 新标题    |
| is_pinned | boolean        | 否   | 新的置顶状态 |
| folder_id | string or null | 否   | 目标文件夹  |


响应字段：


| 字段        | 类型          | 必填  | 说明      |
| --------- | ----------- | --- | ------- |
| data.item | SidebarItem | 是   | 更新后的会话项 |


### 5.6.1 删除会话

- 方法：DELETE
- 路径：/api/v1/persona-analysis/sessions/{sessionId}
- 用途：删除单个会话及其导入源、标准化消息、分析运行记录和证据。

请求字段：无。

响应字段：


| 字段             | 类型     | 必填  | 说明          |
| -------------- | ------ | --- | ----------- |
| data.item_id   | string | 是   | 已删除会话主键     |
| data.item_type | string | 是   | 固定为 session |


### 5.7 从文件夹上传聊天记录

- 方法：POST
- 路径：/api/v1/persona-analysis/folders/{folderId}/uploads
- 用途：对应文件夹右键“上传对话记录”，上传后创建会话、解析文本，并可自动触发分析。

请求字段：


| 字段                | 类型      | 必填  | 说明                                |
| ----------------- | ------- | --- | --------------------------------- |
| file              | binary  | 是   | 上传文件，首版仅支持 txt、csv、json 等文本或结构化文本 |
| auto_analyze      | boolean | 否   | 是否上传后自动分析，默认 true                 |
| model_key         | string  | 否   | 自动分析所用模型                          |
| prompt_version_id | string  | 否   | 自动分析所用 Prompt 版本                  |


响应字段：


| 字段                              | 类型             | 必填  | 说明                                  |
| ------------------------------- | -------------- | --- | ----------------------------------- |
| data.session                    | SidebarItem    | 是   | 新创建的会话项                             |
| data.source_id                  | string         | 是   | 原始导入记录主键                            |
| data.parse_status               | string         | 是   | parsed 或 failed                     |
| data.message_count              | integer        | 是   | 成功解析出的消息数                           |
| data.role_summary               | object         | 是   | 角色分布汇总                              |
| data.role_summary.teacher_count | integer        | 是   | 识别为 teacher 的消息数                    |
| data.role_summary.student_count | integer        | 是   | 识别为 student 的消息数                    |
| data.role_summary.unknown_count | integer        | 是   | 识别为 unknown 的消息数                    |
| data.latest_analysis            | object or null | 否   | 若 auto_analyze=true 且成功，则返回最新分析结果摘要 |


### 5.8 获取会话消息列表

- 方法：GET
- 路径：/api/v1/persona-analysis/sessions/{sessionId}/messages
- 用途：加载中间聊天预览区。

请求字段：无。

响应字段：


| 字段                   | 类型     | 必填  | 说明      |
| -------------------- | ------ | --- | ------- |
| data.session_id      | string | 是   | 会话主键    |
| data.title           | string | 是   | 会话标题    |
| data.parse_status    | string | 是   | 当前解析状态  |
| data.analysis_status | string | 是   | 最新分析状态  |
| data.messages        | array  | 是   | 标准化消息列表 |


### 5.9 触发分析

- 方法：POST
- 路径：/api/v1/persona-analysis/sessions/{sessionId}/analyze
- 用途：手动重跑分析，或在切换模型、切换 Prompt 后重新执行。

请求字段：


| 字段                | 类型     | 必填  | 说明                                     |
| ----------------- | ------ | --- | -------------------------------------- |
| model_key         | string | 是   | 本次分析使用的模型                              |
| prompt_version_id | string | 是   | 本次分析使用的 Prompt 版本                      |
| trigger_source    | string | 是   | upload_auto、manual_rerun、prompt_change |


响应字段：


| 字段                   | 类型     | 必填  | 说明                 |
| -------------------- | ------ | --- | ------------------ |
| data.analysis_run_id | string | 是   | 分析运行主键             |
| data.session_id      | string | 是   | 会话主键               |
| data.analysis_status | string | 是   | succeeded 或 failed |
| data.result          | object | 是   | 完整分析结果，字段与 5.9 相同  |


### 5.10 获取最新分析结果

- 方法：GET
- 路径：/api/v1/persona-analysis/sessions/{sessionId}/analysis/latest
- 用途：加载右侧分析面板。

请求字段：无。

响应字段：


| 字段                         | 类型             | 必填  | 说明              |
| -------------------------- | -------------- | --- | --------------- |
| data.analysis_run_id       | string         | 是   | 最新分析运行主键        |
| data.session_id            | string         | 是   | 会话主键            |
| data.analysis_status       | string         | 是   | 最新分析状态          |
| data.model                 | ModelOption    | 是   | 本次使用的模型信息       |
| data.prompt_version        | PromptVersion  | 是   | 本次使用的 Prompt 版本 |
| data.persona_tags          | array          | 是   | 用户标签            |
| data.pain_points           | array          | 是   | 痛点列表            |
| data.deal_closing_points   | array          | 是   | 成交节点列表          |
| data.churn_points          | array          | 是   | 流失节点列表          |
| data.high_frequency_points | array          | 是   | 高频问题列表          |
| data.risk_assessment       | RiskAssessment | 是   | 风险评估            |
| data.smart_replies         | array          | 是   | 推荐话术列表          |
| data.summary               | string         | 否   | 面向页面顶部摘要区的总述    |


### 5.11 获取 Prompt 版本列表

- 方法：GET
- 路径：/api/v1/persona-analysis/prompt-versions
- 用途：加载 Prompt 版本下拉框与编辑器内容。

请求字段：


| 字段              | 类型      | 必填  | 说明                         |
| --------------- | ------- | --- | -------------------------- |
| tool_key        | string  | 否   | 默认 user_profiling_analysis |
| task_key        | string  | 否   | 默认 analyze_chat            |
| include_content | boolean | 否   | 是否返回 content，默认 true       |


响应字段：


| 字段                            | 类型     | 必填  | 说明          |
| ----------------------------- | ------ | --- | ----------- |
| data.items                    | array  | 是   | Prompt 版本列表 |
| data.active_prompt_version_id | string | 否   | 当前启用版本主键    |


### 5.12 新建 Prompt 版本

- 方法：POST
- 路径：/api/v1/persona-analysis/prompt-versions
- 用途：保存新 Prompt 版本。

请求字段：


| 字段                         | 类型      | 必填  | 说明                          |
| -------------------------- | ------- | --- | --------------------------- |
| tool_key                   | string  | 是   | 固定为 user_profiling_analysis |
| task_key                   | string  | 是   | 固定为 analyze_chat            |
| version_label              | string  | 是   | 版本号，例如 v1.1                 |
| version_note               | string  | 否   | 版本备注                        |
| content                    | string  | 是   | Prompt 正文                   |
| based_on_prompt_version_id | string  | 否   | 基于哪个版本派生                    |
| is_active                  | boolean | 否   | 是否创建后立即启用，默认 false          |


响应字段：


| 字段        | 类型            | 必填  | 说明             |
| --------- | ------------- | --- | -------------- |
| data.item | PromptVersion | 是   | 新建后的 Prompt 版本 |


### 5.13 更新 Prompt 版本

- 方法：PATCH
- 路径：/api/v1/persona-analysis/prompt-versions/{promptVersionId}
- 用途：编辑 Prompt 内容或备注。

请求字段：


| 字段           | 类型     | 必填  | 说明          |
| ------------ | ------ | --- | ----------- |
| version_note | string | 否   | 新备注         |
| content      | string | 否   | 新 Prompt 内容 |


响应字段：


| 字段        | 类型            | 必填  | 说明             |
| --------- | ------------- | --- | -------------- |
| data.item | PromptVersion | 是   | 更新后的 Prompt 版本 |


### 5.14 启用 Prompt 版本

- 方法：POST
- 路径：/api/v1/persona-analysis/prompt-versions/{promptVersionId}/activate
- 用途：切换当前启用的 Prompt 版本。

请求字段：


| 字段              | 类型     | 必填  | 说明   |
| --------------- | ------ | --- | ---- |
| activation_note | string | 否   | 启用备注 |


响应字段：


| 字段        | 类型            | 必填  | 说明     |
| --------- | ------------- | --- | ------ |
| data.item | PromptVersion | 是   | 最新启用版本 |


### 5.15 获取模型选项

- 方法：GET
- 路径：/api/v1/persona-analysis/model-options
- 用途：加载模型下拉框。

请求字段：无。

响应字段：


| 字段         | 类型    | 必填  | 说明     |
| ---------- | ----- | --- | ------ |
| data.items | array | 是   | 可用模型列表 |


## 6. SQLite 表映射


| 接口对象                   | SQLite 表              | 说明             |
| ---------------------- | --------------------- | -------------- |
| SidebarItem 中的 folder  | conversation_folders  | 文件夹元信息         |
| SidebarItem 中的 session | conversation_sessions | 会话元信息          |
| 上传来源                   | conversation_sources  | 原文件、原始文本、解析状态  |
| ConversationMessage    | conversation_messages | 标准化消息          |
| PromptVersion          | prompt_versions       | Prompt 版本与启用状态 |
| 分析运行                   | analysis_runs         | 每次模型调用记录       |
| FindingItem            | analysis_findings     | 结构化分析结论        |
| EvidenceItem           | finding_evidences     | 证据原话与时间点       |


## 7. 实施建议

1. 上传接口内部建议自动完成“落原文、解析消息、创建会话、可选自动分析”四步，减少前端多次调用。
2. 分析接口虽为同步返回，但后端仍应持久化 analysis_runs，便于后续切换为异步执行。
3. 高频节点在单会话场景中，只能判定“是否属于常见高频咨询类型”，不能生成真实团队频次统计。
4. 所有 finding 类型都必须有 evidences；若证据不足，返回空数组而不是猜测结论。

