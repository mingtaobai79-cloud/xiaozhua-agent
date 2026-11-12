---
name: v8-source-navigation
description: 在已挂载的 V8 源码中定位模块、符号定义和调用示例。适用于知识库不够、需要找代码位置时；不要用于写方案文档或直接改代码。
---

# V8 源码导航与检索

## 目标

把业务需求先映射到 V8 的代码源、模块和目录，再调用源码 MCP。路径文档只是导航，不替代实际源码核验；最终结论必须带代码源、相对路径和行号。

## 工具怎么选

不要把源码检索合成一个接口。按问题类型选工具：

1. 查文档、客开怎么做：`get_development_context` / `search_v8_knowledge`
2. 口语找公开接口，例如「同步部门有哪些增删改接口」：`resolve_v8_api`（向量命中后自动 Zoekt 定位）。只要签名时才用 `search_v8_public_apis`
3. 已知类名、方法名、要文件位置：`search_v8_code` / `find_v8_symbol`（Zoekt 全仓文本）
4. 已知类名要读类体：`get_v8_type_source`
5. 核对调用和测试：`get_v8_usage_examples` / `get_v8_code_context`
6. 按路径读片段：`read_v8_code`，带行号范围，不要整仓灌进对话

`search_v8_public_apis` 只覆盖 facade/api/services 的公开签名，不能替代 Zoekt，也不是知识库。


## 强制流程

1. 先调用 `get_platform_context`，确认 `code_directories` 中已登记的代码源别名。未启用源码工具时，只能基于 Markdown 并标记“源码未核实”。
2. 先检索 `01-源码导航与检索地图.md` 和相关知识库文档，确定业务域、前端/后端路线和候选模块。
3. 源码检索已建立全量索引：直接用类名、接口名、方法名查询即可，不必填 `path`。工作台会把定义排在调用前面。
4. `path` 只是可选过滤，例如已经确定模块时再传 `backend/organization-facade`。不要因为不会填 path 就放弃源码工具。
5. 已知类名要读类体时调用 `get_v8_type_source`。只要定位时调用 `search_v8_code` / `find_v8_symbol`。口语找公开接口时先用 `resolve_v8_api`。
6. 需要综合判断时调用 `get_v8_code_context`，检查定义、调用方、测试是否来自同一版本/模块。
7. 代码源未登记、目录不匹配或没有命中时，明确标记“源码未核实”，不得根据路径名称猜接口。

## MCP 参数

- `repository` 只能使用 `get_platform_context.code_directories` 返回的别名，通常是 `v8`。
- `backend`、`frontend`、`backend/bpm-facade` 都不是 repository。它们只出现在 `path`、知识库路径或检索后的相对路径里。
- 正确示例：`find_v8_symbol(repository="v8", symbol="BpmOpinionGroupService", path="backend/bpm-facade")`。
- 正确示例：`search_v8_code(repository="v8", query="OrgUnitSyncAppService", path="backend/organization-facade")`。
- 错误示例：`find_v8_symbol(repository="backend", symbol="BpmOpinionGroupService")`。
- 读取文件时：`read_v8_code(repository="v8", path="backend/bpm-facade/.../BpmOpinionGroupService.java")`。
- 默认省略 `path`，让工作台全量检索；只有结果太噪时才加 `path` 过滤。

## 路由规则

- 后端组织、部门、人员、岗位、职务、职级：优先相对路径 `backend/organization-facade` 与 `backend/organization/organization-biz`。
- 后端 BPM：优先相对路径 `backend/bpm-facade` 与 `backend/bpm/bpm-biz`。
- 后端 UDC：优先相对路径 `backend/udc-facade`、`backend/udc/udc-biz`。
- 后端集成/CIP：优先相对路径 `backend/cip-*`、`backend/ctp-*` 相关 facade/biz。
- 前端组织：优先相对路径 `frontend/apps/organization/src/pages` 与 `src/services`。
- 前端 BPM/审批：优先相对路径 `frontend/apps/bpm` 与 `frontend/apps/app-approval`。
- 前端 UDC：优先相对路径 `frontend/apps/udc`；客开页面通常在独立 UDC 扩展工程，不在基线 `frontend/apps`。
- 公共组件和运行时能力：优先相对路径 `frontend/libs/xiaozhua-global`、`frontend/libs/biz-*`、`frontend/libs/syf`。

## 线上 URL 定位

对 `/main/<appId>/<page>`，先在代码源 `v8` 下查相对路径 `frontend/apps/<appId>`；`/main-mobile` 对应 `*-mobile` 目录。`/main/portal/<custom-app>/...` 通常是 UDC 客开应用，应转查扩展工程和知识库，不要在基线应用中臆造文件。

## 证据要求

- 先返回定义，再返回调用方和测试；`search_v8_code` 会把定义排在调用和测试前面，并标记 `kind=definition|call|test`。动态反射、配置注册或泛化调用须标注人工确认。
- 每条源码证据使用 `别名:相对路径#Lx-Ly`，例如 `v8:backend/organization-facade/.../OrgUnitSyncAppService.java#L20-L45`。
- 路径地图与源码不一致时以当前源码为准，并在回答中说明差异。
- 源码阅读遵守脱敏和大小限制，不请求整个大文件或整个仓库内容。
