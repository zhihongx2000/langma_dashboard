需求名称：AI咨询数据复盘总结聊天记录

需求描述：通过接入大模型批量解析、分析所有咨询老师的企业微信自考咨询聊天记录，自动提取用户核心痛点、成交关键节点、用户流失核心原因，汇总提炼全团队 / 单任老师的高频共性问题与高转化话术；解决咨询团队转化能力参差不齐、用户高频问题重复解答、丢单原因无法精准定位的业务痛点，最终输出标准化的高频问答知识库、高转化话术库、个人 / 团队复盘报告，知识库，最终形成ai机器人，可直接对接企业微信实现用户咨询自动回复，同时赋能咨询老师优化沟通话术、提升报名转化率。

当前一期实现范围：

- 以前端现有的用户画像分析页为准，先完成单会话上传、解析、分析、结果回显闭环。
- 一期重点服务 [frontend/src/pages/PersonaAnalysis.tsx](frontend/src/pages/PersonaAnalysis.tsx) 页面，不在当前迭代内完成团队级批量复盘页。
- 一期输入先支持文本类聊天记录与结构化文本，不包含截图 OCR；docx 深解析作为后续增强项。
- 一期输出除结论外，必须附带触发判断的原话、说话人、时间点和理由，便于老师人工复核。
- 当前实现涉及的接口与字段定义见 [docs/api/user_profiling_analysis.md](docs/api/user_profiling_analysis.md)。
- 当前生效的结构化 Prompt 见 [prompts/prompt_for_user_profile.md](prompts/prompt_for_user_profile.md)。