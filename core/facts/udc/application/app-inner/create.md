# udc.application.app-inner｜应用内功能页事实格

> **状态：LIVE**（2026-10-22 test2 实机：只读面 9 探针 + 依赖加删双向 + 一次完整构建）
> 目标环境：test2，`<gateway-host>`，网关前缀 `/service/udc`，应用 `9000000000000000001`
> 平台版本：`udc-web` 5.3.517（`/ 5.3.517`）
> 详细请求体、踩坑与未解项见 **`core/facts/udc/application/app-inner/app-inner-write-chain.md`**
> 全量操作表见 **`docs/operation-contracts/udc/application/app-inner-contracts.md`**
> 页面级叙事（每页怎么点、抓包怎么做）见 `core/facts/udc/application/app-inner-pages.md`

## R-A1 Capability

| 能力 | 端点 | 方法 | 状态 |
|---|---|---|---|
| 应用内子路由 | `app-basic-info/{testPage,testVersion,version,dependentApp,dependentCmp,team,appTheme}` | GET | LIVE |
| 沙箱就绪态 | `udc/graphql?udcDeploymentAppReadyStatePost` | POST | LIVE PASS（`state=RUNNING`、`msg=DEPLOY_SUCCESS`） |
| 一致性检测 | `udc/graphql?udcApplicationSearchDetectionPost` | POST | OBSERVED（写后串发，未主动触发） |
| 构建+部署 | `udc/graphql?udcRuntimeDeployNormalPost` | POST | OBSERVED（声明成 query，实为写） |
| 构建信息/日志 | `udc/graphql?udcSandboxBuildInfoAppGet` | POST | **LIVE PASS**（`state=SUCCESS`、`progress=100`、`logs[37]`） |
| 构建实时状态 | WS `udc_detection_channel` / `udc_deploy_channel` / `common-message` | WS | LIVE |
| 发布版本列表 | `ctp-application/appcenter/search-app-edition` | POST | LIVE PASS（裸数组，`IN_appId` 传 appName） |
| 依赖列表 | `udc/graphql?udcApplicationDependentApplicationSelectByConditionPost` | POST | LIVE PASS（44 行 = SERVICE 11 + FRONTEND 33） |
| 可选应用 | `udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost` | POST | LIVE PASS |
| 添加依赖 | `udc/graphql?udcApplicationDependentApplicationCreateBatchPost` | POST | **LIVE**（实测加一条再复原） |
| 移除应用依赖 | `udc/graphql?udcApplicationDependentApplicationDeleteByIdPost` | POST | **LIVE**（实测移除再复原） |
| 组件依赖批量删 | `udc/application/dependent-application/delete-by-ids` | POST | **LIVE**（REST，`{"ids":[...]}`） |
| 团队设置 | `udc/graphql?udcCollaborationAppGet` | POST | LIVE PASS（`isCreator` / `role`） |
| 应用主题 | `udc/graphql?appCommonThemeSelectDefaultBrandPost` | POST | DENIED（mutation） |
| 应用日志（微流程） | `{appName}/udc-runtime/app-log/search/microflow` | POST | LIVE PASS（10 行） |
| 应用日志（生单/扣减） | 同上 `dataflow` / `deduction` | POST | LIVE（200 + `content=[]`） |
| 操作日志 init | `udc/graphql?udcOperationLogSearchInitDataAppGet` | POST | LIVE PASS |

**入口路径**：应用设计器 → 左侧「应用内功能页」区；构建入口是工具栏「测试」→ 弹窗「立即构建」。

## R-A2 Version

- `udc-web` 5.3.517 / `bpm-facade` 3.12.101（契约字节码已在本仓库别处证实）
- 除 `search-app-edition` 与 `delete-by-ids` 外，其余读面全部走 GraphQL：
  `POST /service/udc/graphql?<operationName>`，**不存在** `/udc/<name>` 形式的 REST 等价物（GET 全 404）

## R-A3 Input（必填槽位）

```
构建信息   {appId}                                  ← 别名 path:（不是 body:）
构建部署   {deployDto:{projectType,terminalType,deployType,appId,generateLog}}
依赖列表   {appId, keyword?, versionType?}
可选应用   {appId, keyword?, versionType?}
添加依赖   [{appId, depAppName, depAppCaption, depAppVersion, depAppBasePackage,
             dependentAppType}]                      ← 数组！FRONTEND 多 10 字段
移除依赖   {id}                                      ← 依赖行 id，不是 appId
组件批删   {ids:[依赖行 id]}                          ← REST，不是 GraphQL
版本列表   {pageInfo:{needTotal,pageNumber,pageSize}, params:{IN_appId:[appName], clientType:"PC"}}
```

## R-A4 响应层级（三个坑，都实测过）

| 接口 | 层级 | 坑 |
|---|---|---|
| GraphQL 通用 | `data.data0.data.content` | 外层**多一层** `data`（`{traceId, data:{data0:…}}`），直接取顶层 `data0` → KeyError |
| 依赖列表 | `data.data0.data.content` + `total` | 只传 `appId` 时 `total=0`；必须带 `versionType`/分页才回 44 行 |
| `search-app-edition` | 顶层裸数组 | 不套 `code` 信封，别找 `BOOT_0000` |

## R-A5 写面边界

- 依赖加删是**唯一**实测放行的写面（加 → 复原，移除 → 复原，均回到 2 行）。
- 构建 `udcRuntimeDeployNormalPost` 实测放行一次，但它会覆盖沙箱态，不属于可随意重放的读面。
- 明确**不碰**：发布 / `app-online` / 沙箱 flexible `create|delete|restart` / `front-log/create` /
  `disable-last-version-metadata` / page-info `create|update|delete` / 清除应用数据。

## R-A6 四类资产互链

| 类别 | 位置 |
|---|---|
| 实现 | `components/udc/application/app_inner_ops.py`、`dependency_constraints.py` |
| 事实 | 本文件 + `app-inner-write-chain.md` |
| 契约 | `docs/operation-contracts/udc/application/app-inner-contracts.md` |
| 测试 | `tests/udc/test_application_app_inner_asset_layout.py` |
| skill | `skills/seeyon-udc-application-app-inner/SKILL.md` |
| 证据 | `core/facts/udc/application/evidence/app-inner-build-2026-10-22/`（4 个 json） |
