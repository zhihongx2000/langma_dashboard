# 项目级工程规范

## 项目背景
- 本项目用于建设教育公司内部使用的 AI 工作台，服务于自考咨询、教务支持和后续内容协同场景。
- 一期重点是完成前端看板与核心工具骨架，其中“用户画像分析工具”是优先落地的三级页面；“考试院信息收集工具”和“考试计划生成工具”先完成信息架构与占位设计；内容分发工具暂不纳入一期真实实现。
- 当前仓库处于前期规划和脚手架搭建阶段。新增实现时，优先补齐目录结构、配置边界、接口约束和测试骨架，避免先堆业务代码再返工。
- 系统一期默认仅供内部老师使用，不做登录与角色权限；涉及 AI 的页面需要保留模型切换、Prompt 切换和版本管理入口。

## 项目结构
- .github/copilot-instructions.md：项目级统一规范，约束代码组织、技术栈、配置和提交流程。
- docs/tec_requirements/：存放业务需求文档、工具说明、页面需求和后续技术需求补充。
- docs/git提交规范.md：记录 Git 提交、推送、拉取、同步和冲突处理的统一流程。
- prompts/：统一存放 Prompt 文件，按工具和任务拆分，支持版本管理。
- 仓库根目录的 .env：仅存放敏感信息，例如 API Key、模型接入地址、密钥类配置。
- 仓库根目录的 settings.yaml：仅存放非敏感配置，例如默认模型、工具开关、Prompt 映射、页面元数据。

## 目标目录规划
- frontend/：react + typescript + vite 前端工程，负责首页、二级工具页、三级工具页和配置实验区。
- backend/：Python 后端工程，负责聊天解析、AI 编排、Prompt 版本管理、工具接口和配置加载。
- backend/tests/：后端测试目录，所有新增业务能力优先补测试。
- docker/ 或根目录 Dockerfile：用于本地联调和后续服务器部署。
- docs/：除需求文档外，后续补充架构说明、接口说明、测试约定等文档。

## 技术栈约束

### 后端约束
- 后端统一使用 Python。
- Python 依赖与环境统一使用 uv 管理，新增依赖优先使用 uv add，不使用 pip install 直接改环境。
- 运行、测试、脚本执行统一优先使用 uv run，确保命令都在受控环境内执行。
- LangChain 必须使用 1.0 以上版本，禁止继续使用 0.3 及更早版本的旧语法、旧导入路径和旧式链路封装。
- 若需求较为复杂，需使用 react agent 时，优先选择 langchain.agents 中所预定义的 agent 接口，示例用法如下：
```python
from langchain.tools import tool
from langchain.agents import create_agent

@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
```
- 如需暴露 HTTP 接口，默认使用 FastAPI，除非用户明确要求其他框架。
- 后端实现应拆分为配置层、解析层、服务层、模型适配层、接口层，不要把 Prompt、配置读取、业务逻辑和路由处理混写在一个文件里。
- 虚拟环境采用 uv 进行管理，禁止在项目中提交 .venv、env、venv 等虚拟环境目录。启动命令为：
```bash
cd /home/hong/lang_ma_dashboard

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv add <package_name>
```

### 前端约束
- 前端统一使用 React + TypeScript。
- 页面和组件默认使用 Composition API 组织，页面负责流程编排，组件负责展示和交互拆分。
- 页面状态必须显式设计并实现，至少覆盖空态、加载态、成功态、失败态。
- 一期页面以桌面端为主，同时保留平板和移动端的基础浏览能力。
- 涉及 AI 输出的三级工具页，底部统一预留模型切换、Prompt 切换、版本管理和运行参数折叠区。

### 配置与环境管理
- 敏感信息只能放在 .env，不得硬编码到源码、settings.yaml、Prompt 文件、测试样例或文档示例中。
- 非敏感配置统一放在 settings.yaml，不要把功能开关、默认模型、页面元数据散落到代码常量里。
- 若需要示例环境变量，提交 .env.example，不提交真实 .env 内容。
- Prompt 统一存放在 prompts/ 目录，按“工具名/任务名/版本”组织，禁止把 Prompt 直接硬编码在业务函数中。
- Prompt 文件中不得出现 API Key、账号密码、真实用户隐私信息。
- 本地环境、CI 环境和 Docker 环境使用的关键版本要保持一致；若调整 Python 或 Node 版本，需要同步更新项目文档和容器配置。

### 测试与质量要求
- 本项目采用 TDD 导向开发。新增功能时，优先补测试或至少同步补齐最小可验证测试。
- 后端默认使用 pytest 构建测试体系；若引入前端测试，优先选择与 Vite 兼容的测试方案。
- 每次变更应只解决一个明确问题，避免在同一次提交中混入无关重构。
- 接口、配置结构、Prompt 目录规则发生变化时，必须同步更新对应文档。

## AI 工具开发约束
- 用户画像分析工具是一期优先工具，页面结构应围绕“左侧聊天预览、右侧结果面板、底部实验区”组织。
- 一期聊天输入支持粘贴文本、文本类文件、企业微信或 CRM 的结构化导出文件；截图 OCR 不在一期实现范围内。
- AI 输出结果应强调“辅助判断”，避免绝对化结论，尤其是风险判断、流失原因和话术推荐。
- 聊天解析层需要考虑角色识别、时间戳提取、异常昵称、乱码和角色纠正入口，不要假设所有原始数据都结构完整。

## Git 提交规范
- 提交前先看清当前分支和工作区状态，避免把无关改动一并提交。
- 提交粒度保持单一：一个提交只做一类变更，例如单独的功能、文档、修复或测试补充。
- 提交说明建议使用 Conventional Commits 风格，例如 feat、fix、docs、refactor、test、chore。
- 没有验证的改动不要直接提交；至少运行与本次改动直接相关的最小测试或检查。
- 不要提交 .env、密钥文件、构建产物、临时调试文件和本地缓存目录。
- 不要在未同步远程最新代码的情况下直接推送长期分支。
- 详细的本地提交、推送、拉取、同步和单文件恢复流程见 docs/git提交规范.md。

## 文档维护要求
- 新增工具、接口、Prompt 目录或配置项时，优先同步补齐 docs/ 下的说明。
- 需求仍在变化时，先更新需求文档和页面说明，再推进大规模实现。
- 如果实现方案与现有文档不一致，应先修正文档或在提交说明中明确原因。
