# AstrBot Smart Reply Plugin

LLM 自主判断是否回复群聊消息，替代固定概率的随机回复。

## 功能

- 每收到群消息，取最近聊天记录让 LLM 判断是否该回复
- LLM 返回 YES 则触发 AstrBot 正常生成回复
- LLM 返回 NO 则忽略
- 比固定概率（10%）更智能，不会乱插话，该回的时候会回

## 安装

在 AstrBot 插件市场搜索 `smart_reply` 安装。

## 配置

- **prompt**: 判断提示词（可调优让回复更精准或更安静）
- **history_count**: 上下文条数（默认 12）
- **whitelist**: 群聊白名单
- **provider_id**: 判断用模型（留空用默认）
