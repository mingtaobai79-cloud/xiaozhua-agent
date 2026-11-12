# 应用域契约索引（应用内功能页 / 依赖设置 / 沙箱构建）

> 覆盖 test2 实测（2026-10-22）的应用设计器右侧「应用内功能页」全部子页 + 工具栏「测试」构建链路。
> registry 键名以本表为准（`UdcOperationRegistry.default()` 可自检）。
> 逐条请求体与错误字典见 `core/facts/udc/application/app-inner/app-inner-write-chain.md`；
> 全量原始记录见同目录 `udc-app-inner-readonly-2026-10-22.md`。

## 1. 读面

| registry key | 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|---|
| `udc.deployment.app_ready_state` | POST | `udc/graphql?udcDeploymentAppReadyStatePost` | OBSERVED | 沙箱就绪态，`state=RUNNING` / `msg=DEPLOY_SUCCESS` |
| `udc.deployment.latest_test_info` | POST | `udc/deployment/latest-test-info` | OBSERVED | 工具栏「测试」前查最近一次测试版本 |
| `ctp.version.list` | POST | `ctp-application/appcenter/search-app-edition` | OBSERVED | 发布版本列表；**裸数组**，`IN_appId` 传 appName |
| `udc.dependency.list` | POST | `udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | OBSERVED | 依赖列表；SERVICE 与 FRONTEND **同一口**，按 `dependentAppType` 区分 |
| `udc.dependency.available_apps` | POST | `udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost` | OBSERVED | 候选应用；组件依赖不走它（前端内置目录） |
| `udc.sandbox.build_info` | POST | `udc/graphql?udcSandboxBuildInfoAppGet` | OBSERVED | 构建信息 **含 `logs[]`**，别名是 `path:` |
| `udc.sandbox.delta_build_info` | GET | `udc/sandbox/delta-build-info/{appId}` | OBSERVED | 增量构建信息，`state=NONE` |
| `udc.sandbox.is_deploy_war` | GET | `udc/sandbox/system/config/is-deploy-war` | OBSERVED | 是否 war 部署 |
| `udc.operation_log.init_data` | POST | `udc/graphql?udcOperationLogSearchInitDataAppGet` | OBSERVED | 操作日志筛选元数据 |
| `udc.applog.search.microflow` | POST | `{app_name}/udc-runtime/app-log/search/microflow` | OBSERVED | 微流程运行日志（实测 10 行） |
| `udc.applog.search.dataflow` | POST | `{app_name}/udc-runtime/app-log/search/dataflow` | OBSERVED | 生单规则运行日志（200 + 空） |
| `udc.applog.search.deduction` | POST | `{app_name}/udc-runtime/app-log/search/deduction` | OBSERVED | 扣减规则运行日志（200 + 空） |
| `udc.applog.search.absent_kinds` | POST | `{app_name}/udc-runtime/app-log/search/{design|page|bizrule|sandbox|build|deploy|other}` | DENIED | 7 种候选全 404，**证伪族**，别再拼 |
| `udc.ws.business_channels` | WS | 会话 WebSocket，帧 `{operate,data}` | OBSERVED | `udc_detection_channel` / `udc_deploy_channel` / `common-message` |

## 2. 写面（本仓库默认不发，仅在明确授权的收口批次内使用后必须复原）

| registry key | 方法 | 路径 | 状态 | 说明 |
|---|---|---|---|---|
| `udc.dependency.create_batch` | POST | `udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | DENIED | 应用依赖（SERVICE）加一条；`params0` 是**数组** |
| `udc.dependency.component_create` | POST | 同上一行 | DENIED | 组件依赖（FRONTEND）加一条，多 10 字段 |
| `udc.dependency.delete_by_id` | POST | `udc/graphql?udcApplicationDependentApplicationDeleteByIdPost` | DENIED | `{id: 依赖行 id}`，**不是** appId |
| `udc.dependency.delete_by_ids` | POST | `udc/application/dependent-application/delete-by-ids` | DENIED | 组件依赖批量删，**REST** `{ids:[...]}` |
| `udc.application.detection` | POST | `udc/graphql?udcApplicationSearchDetectionPost` | DENIED | 一致性检测；写后平台自动串发 |
| `udc.deploy.deploy_normal` | POST | `udc/graphql?udcRuntimeDeployNormalPost` | DENIED | 沙箱「立即构建」；声明成 `query` 实为写 |

`udc.deploy.normal`（REST `udc/runtime/deploy-normal`）与上面的 `udc.deploy.deploy_normal`
**不是同一个入口**：REST 那条出现在发布/升级链路，GraphQL 这条才是沙箱构建。

## 3. 响应层级（三个坑）

```
GraphQL 统一     raw["data"]["data0"]["data"]["content"]     ← 外层多一层 data
依赖列表         data.data0.data.content + data0.data.total   ← 只传 appId 时 total=0
search-app-edition  顶层裸数组                                 ← 不套 code 信封
```

## 4. 白名单（除这六条写面外的应用域动作，本仓库不做）

发布 / `app-online` / 沙箱 flexible `create|delete|restart` / `front-log/create` /
`disable-last-version-metadata` / page-info `create|update|delete` / 清除应用数据 / 移交应用。

## 5. 关联

| 类别 | 位置 |
|---|---|
| 实现 | `components/udc/application/app_inner_ops.py`、`components/udc/application/dependency_constraints.py` |
| 事实格 | `core/facts/udc/application/app-inner/create.md` |
| 写链与坑 | `core/facts/udc/application/app-inner/app-inner-write-chain.md` |
| 页面叙事 | `core/facts/udc/application/app-inner-pages.md` |
| 证据 | `core/facts/udc/application/evidence/app-inner-build-2026-10-22/` |
| skill | `skills/seeyon-udc-application-app-inner/SKILL.md` |
