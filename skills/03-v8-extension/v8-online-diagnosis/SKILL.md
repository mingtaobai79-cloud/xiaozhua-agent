---
name: v8-online-diagnosis
description: 用脱敏日志加上知识库/源码证据分析 V8 线上问题。适用于故障排查；不要用于写方案文档或直接改代码。
---

# V8 线上问题辅助判断

先调用 `get_platform_context`，该调用会按安装器绑定的员工身份自动统计。再要求版本、模块、现象和脱敏日志。调用 `diagnose_online_issue`，按“版本模块、入口/SPI/API、源码调用链、规范配置、待验证步骤”输出。不得保存原始敏感日志；员工确认后才调用 `create_incident_card(title, symptom, ...)`。不要向员工索要 UUID 或显示姓名，也不要传 user_id、display_name。
