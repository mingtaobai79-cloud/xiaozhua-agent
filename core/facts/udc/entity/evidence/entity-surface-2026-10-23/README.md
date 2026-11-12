# 实体域接口面取证 · 2026-10-23

原始抓包（保留平台原文，供复核；含平台侧标识，属原始证据区）。

| 文件 | 来源动作 | 内容 |
|---|---|---|
| capture-entity-switch.json | 在设计器实体页点击左侧另一个实体 | 6 条请求：实体全量列表、版型列表、数据类型全集、特性列表、字段分组+字段、openAPI 动作、预设属性容量、编辑锁 |
| capture-page-boot.json | 点顶部「应用」tab 再切回「实体」tab | 8 条请求：依赖应用、应用详情、业务实体目录、扩展实体列表 |

另：`docs/audit/artifacts/udc-frontend-ops/frontend_ops_contracts.json`
= 从设计器前端 bundle（src_redux_store_ts 单文件 2.4MB）静态提取的 291 条 GraphQL 操作契约，
含 `loader`(query/mutation)、`paramsType`、`paramsKey`(path/body)、`queryFields`。
其中实体域相关 90 条，是本轮接口面清单的权威来源（比点页面更全）。

取数方式：CDP 连已打开的实体设计页 → 页面内注入 XHR/fetch hook → 操作页面 → 读 `window.__CAP__`。
只读查询复核走页面内 XHR（自动带会话），不落 cookie。
