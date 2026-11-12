# 设计态构建/部署写契约族（R18，test2 活体 2026-09-24 全链实证）

> 性质：把 2026-09-24 test2 上「需求→实体+属性→**建页(LIST+DETAIL)**→RELEASE 构建→物理表落库」这条
> 设计态写链固化成 agent 的**可执行方案 data**（`components/platform_operations/deployment.py`
> + `xiaozhua_host_bootstrap.deploy_plan`）。agent 保持 readonly：写契约在
> `layer.py` 仍判 DENIED（`contract.write` → POLICY_DENIED），宿主（Hermes/CC/Codex）
> 按方案 steps 执行真实端点。证据等级分列，不升级、不臆造。

## 一、全链实证（LIVE，非声明）

| 环节 | 证据 | 等级 |
|---|---|---|
| 建实体 | `POST /service/udc/entity` → `BOOT_0000`，实体 id `7670732978062038177`（YanshouDan/验收单，stereotype=bill） | OBSERVED_LIVE |
| 建属性 | `POST /service/udc/entity/attribute` ×4（acceptanceDate/acceptor/conclusion/amount）全部 SUCCESS | OBSERVED_LIVE |
| 建页 | `POST /service/udc/page-info/base-info/create` ×2（验收单列表 LIST id `1871471844026226944` / 验收单详情 DETAIL id `2146495017352265083`，relationGroupId 各自返回）全部 `BOOT_0000` | OBSERVED_LIVE |
| 页面回读 | `GET /service/udc/page-info/select-by-appId/{appId}` 200，验收单 2 命中（id=-6629355753974142446 / -6832321505567116615 即 relationGroupId；按 id 回读 404=该读面仅认 relationGroupId，UNVERIFIED） | OBSERVED_LIVE |
| 构建触发 | 用户在设计器点「立即构建」，body `{appId, deployType:RELEASE, projectType:ALL, terminalType:ALL}` → `udc_deploy_record` 当日 `deploy_type=2 state=1 内部流水线构建成功`（15:52 行） | OBSERVED_LIVE |
| 物理表 | RDS 直连 `9000000000000000001_test2`：表 `yanshouda_m5654091886000795633` 存在，DDL 带 4 业务列 + 全套单据系统列（中文注释） | OBSERVED_LIVE |

关键认知修正：构建走的是**应用级 sandbox 部署**（`boot-starter-sandbox` 的
`UdcAppDeployService` + `PipelineProperties` 流水线 + `SandboxK8sService`），
**不是**实体级 `PublishStateController.update`（那条要 `entityClassName/ids/password`，
测试中报 `password must not be null` 即此面）。两者是不同链路，勿混。
前端页面**不是构建送的**：页面是独立设计态动作（`PageInfoController.createBaseInfo`），
需在建实体后显式创建，再随构建发布——deploy_plan 已按此顺序固化第 3 步。

## 二、页面创建契约（2026-09-24 活体逐步试出错路标定）

`PageInfoController`（udc-web-5.3.517.jar，活体 javap）：类级路径 `/udc/page-info`，
方法级 `/base-info/create`（RestApiOperation「创建新页面(只包含基础信息，会同时新建多个页面类型为一组)」）。

必填链（缺一即拒，均为 LIVE 实测错误码）：
1. `pageType` 缺 → `BOOT_1001 pageType must not be null`
2. `pageUrl` 缺（顶层与 pageItems 皆需）→ `BOOT_1001 pageUrl must not be null`
3. `curTerminalType` 缺 → `BOOT_1000 页面终端信息为空，请选择`
4. `actionType` ∈ `{NORMAL, INSERT, UPDATE, DELETE}`（`com.seeyon.boot.enums.ActionType` javap；VIEW 不存在 → `BOOT_3002`）
5. `masterEntityIds` = 实体数字 id；页面 urlType ∈ `{PC, MOBILE}`（TerminalTypeEnum 同源）

`PageTypeEnum` 12 值（javap）：PORTAL/WELCOME/REPORT_FORM/DETAIL/LIST/APPROVAL/PORTLET/SEARCH_LIST/EDIT_LIST/LIST_DETAIL/ASSIST_INFO/OTHER。
`PageDefinitionDto` 关键字段：appId(数字)/caption/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems[]。

## 三、契约登记（registry.py R18）

- `udc.deploy.normal`：`POST /service/udc/runtime/deploy-normal`（DeployNormalDto），**write=True，LIVE**。
  类级前缀 **09-27 确诊 = `udc/runtime`**（`@RequestMapping("udc/runtime")` + 方法级 `deploy-normal`）。
  探针复核：正确路径 `GET`→**405**（映射在、POST-only），裸 `/service/udc/deploy-normal` `GET`→**404**（无映射）
  —— 前批"Spring404 探测"结论成立但**归因修正**：错在路径缺类级前缀，非前缀不存在。
  body 须按形参名包成 `{"deployDto":{...}}`（`@MultiRequestBody` 语义；平铺 → `EL1007E: Property or field 'appId' cannot be found on null`，09-27 实证）。
- `udc.deploy.search_status`：`GET deploy/search-status/{id}`（读部署记录），UNVERIFIED
  （类级前缀未单独实测，同控制器族**推定** `udc/runtime`；禁擅自拼前缀执行，待实测）。

## 四、受控词表（活体快照，随活体复核刷新，非发明）

- **stereotype** ∈ `{archive, standard, bill, archiveTree}`：test2 目标应用 169 实体回读统计。
- **dataType** ∈ `{ENTITY, DATETIME, ENUM, STRING, MULTILINESTRING, BOOLEAN, BIGINTEGER, INTEGER, DECIMAL, DATE, Serial}`：bill 实体 51 属性回读。
- **DeployTypeEnum** ∈ `{TEST, RELEASE, ON_ONLINE, DELTA}` / **ProjectTypeEnum** ∈ `{FRONTEND, BACKEND, ALL}` / **TerminalTypeEnum** ∈ `{ALL, PC, MOBILE}`：活体 pod 反编译 `javap`。
- 数字编码：`deploy_type` 2=RELEASE / 0=TEST；`state` 1=成功 / 2=失败（`udc_deploy_record` LIVE，09-24 RELEASE 成功 + 09-27 TEST 失败双观测）。

### 三·补 09-27 LIVE 复核（构建链路端到端）

- TEST 构建真实跑通至业务校验点：`POST /service/udc/runtime/deploy-normal`
  `{"deployDto":{appId, deployType:"TEST", projectType:"ALL", terminalType:"ALL"}}` → `200 BOOT_0000` + `deployId`；
  落库 `udc_deploy_record`（`deploy_type=0`、`state=2`）。
- 流水线时序：`CdpDeployTask`（数据预置，~2.2s）→ `CdpDataDetectionTask`（一致性检测，~108s）
  → 未过则 `AbstractDeployService.doParallel(AbstractDeployService.java:242)` 抛 `Business Error[一致性检测未通过]`，**整单失败、无部分成功**。
- 检测明细**不落 MySQL**（`SHOW TABLES LIKE '%detect%' / '%check%'` 均空）→ 仅在 Redis
  `test2:udc:5.3.517:DetectionError:Data::<appId>:<ENTITY|PAGE|MICRO>:<类全名>`；
  读取面 `POST /udc/graphql`（自定义 GraphQL，仅路由预生成接口，introspection 被拒）+ `/udc/application/search/front-detection`（入参名未探明）。
- 本轮失败归因 = **被拷应用自身数据悬空**（页面数据源缺失 146 次 / 参照悬空 30+ / 关联枚举元数据为空 / 页面表达式失效），链路侧无缺陷。
- 语义印证：RELEASE 前需有成功 TEST —— UI 曾提示"应用未成功发布过，请先【测试】操作"（09-24 LIVE 文案）。

## 五、agent 暴露面（xiaozhua_host_bootstrap.deploy_plan）

```
host["deploy_plan"](application_id, entity_name, attributes, caption,
                    stereotype="bill", deploy_type="RELEASE")
  → {"schema": "xiaozhua-deployment-plan.v1", "readonly_plan": True,
     "steps": [entity.create, attribute.create, deploy.normal],
     "enums": {...}, "evidence": [...], "unknowns": [...]}
```

- 每个 step 带 `verify`（怎么确证成功）。`dataType` 缺省按字段名保守推断并标
  `unknowns`（不臆造）；`stereotype` 出值域进 `unknowns`。
- **宿主执行边界**：steps 是 data，agent 不发写；宿主拿 steps + gateway_base + 凭据引用
  自己调端点。写门（`layer.py`）对 `udc.deploy.normal` 仍返回 `DENIED`（POLICY_DENIED），
  readonly 纪律不破。

## 六、未验证项（UNVERIFIED / BLOCKED）

- deploy 读面类级前缀（LIVE 404）→ 完整路由 UNVERIFIED，不拼前缀。
- `deploy_normal` 的 `pushEnv` / `extraParamMap` 必填性 → 未在活体确证，方案带默认 RELEASE/ALL/ALL。
- 前端页面/列表是否随 RELEASE 构建生成 → 需活体回读页面面确认（本轮未探）。
- 生成的 Java 工程是否已落 OSS/仓库（`schema_storage_key`/`sql_storage_key` 指向的存储对象）→ 未直读。

## 七、铁律

- 写面 agent 不出（gate DENIED），宿主授权执行；凭据仅路径引用，值 0 入件。
- 值域/枚举/数字编码 = 活体快照，随活体复核刷新；不得当永久常量硬编码进调用方。
- 物理表落**应用自身库**（`{app}_test2` / `{app}_uat`），非 `udc_test2`——验证时连对库。
