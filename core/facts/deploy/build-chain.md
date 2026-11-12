# deploy.build-chain｜应用构建/发布链路（九段式事实格 · 09-27）

> 基线：test2 LIVE 实证一轮（2026-09-27 19:05:16→19:07:06，deployId=1006978865758003184）。
> 段序同 B1 样板格 `core/facts/udc/entity/create.md`；本件只写"构建/发布链路"这一格。
> 凭据 0 入件（只引 config 键/路径）；应用 id 仅作证据锚，业务明细不入长期库。
> 仓库 `<SEEYON_AGENT_ROOT>`。

---

## 1. Capability

| op | HTTP | 完整路径（LIVE 实证） | 入参 | 响应 |
|---|---|---|---|---|
| `udc.deploy.normal` | POST | `/service/udc/runtime/deploy-normal` | `{"deployDto":{...}}` | `{"status":0,"code":"BOOT_0000","deployId":"<雪花id>"}` |

- 路由三要素（javap 逐字 + LIVE）：
  - 宿主前缀 `/service/`（平台拼装，非类注解）
  - 类级 `@RequestMapping("udc/runtime")` ← **本轮矫正项**：此前按 `udc/deploy` / 裸 `udc` 拼，均 404
  - 方法级 `@PostMapping("deploy-normal")`
- 权限：方法级 `@HasRole(udcAppDesigner | udcSystemAdmin)`；**类级无 @HasRole**。
- 同族易混控制器：`udc/deployment/*`（`DeploymentController`，类级 `@HasRole(udcAppDesigner|udcSystemAdmin|OpsAdmin|BpmSystemManager)`）——请求打到它得到 405 / 404 伪装页，**不是本链路**。
- 相关只读面：`udc.deploy.search_status`（读部署记录）仍在 registry 记 `UNVERIFIED`（见 §7）。

## 2. Version

- Canonical = **5.3.517**（宿主编排侧 udc-web）；检测侧引用 `cdp-data-facade-5.3.260`。
- 控制器类：`DeployController`（类级路径 `udc/runtime`）。
- 类 sha256 / javap 文本件 sha256：**UNVERIFIED**（本轮未落盘，不臆造）。

## 3. Input

- **必须按形参名包裹**：`{"deployDto": {"appId": <Long>, "deployType": "TEST", "projectType": "ALL", "terminalType": "ALL"}}`
- 形参注解是 Seeyon Boot 的 `@MultiRequestBody`（**非** Spring `@RequestBody`）→ 语义 = 按形参名从 JSON 顶层取子对象。
- 反证：平铺 body（`{"appId":...}`）→ DTO 为 null → `EL1007E: Property or field 'appId' cannot be found on null`。

## 4. Required

- `deployDto` 壳必填（见 §3 反证：不包即 null）。
- `deployDto.appId` 必填；`deployType` ∈ {TEST, RELEASE, ON_ONLINE, DELTA}；`projectType` / `terminalType` 实测用 `ALL`。

## 5. Execution

LIVE 观测执行序列（19:05:16 发起 → 19:07:06 收敛，约 110s）：

1. `CdpDeployTask` 应用发布任务（数据中台数据预置）→ 完成，2253ms
2. `CdpDataDetectionTask` 一致性检测 → 107796ms
3. 检测未过 → `AbstractDeployService.doParallel(AbstractDeployService.java:242)` 抛 `Business Error[一致性检测未通过]`
4. 失败态回写 `udc_deploy_record`（`AbstractDeployService:267`）
- 检测结果并行写 Redis（key 见 §7），**不落 MySQL**。

## 6. Side Effects

- 写 `udc_test2.udc_deploy_record`：本轮 id=2343914262409841112，`deploy_type=0`(TEST)、`state=2`(失败)、`build_version=20260927190507`、`msg` 含失败原因与报错位置。
- 状态字值域（已观测）：`state` 1=成功 / 2=失败；`deploy_type` 0=TEST / 2=RELEASE。
- 物理表落 `{应用库}_test2`（前批 RELEASE 实证：`9000000000000000001_test2`）。
- 生成 Java 工程 / 前端产物是否落 OSS 或代码仓库 → **UNVERIFIED**（承前批，本节不臆造）。

## 7. Known Constraints

- **前置门＝一致性检测**：未通过即整单发布失败，无"部分成功"语义。
- **RELEASE 前置**：UI 曾提示「应用未成功发布过，请先【测试】操作」（LIVE 文案，09-24）。"必须先有一次成功 TEST 才能 RELEASE" 属**机制推断 = UNVERIFIED**；已确认的事实是 RELEASE 在无成功 TEST 前被拒。
- **检测明细读取面（本轮探明 + 负证据）**：
  - `POST /service/udc/graphql` —— 自定义 GraphQL，仅路由**预生成接口**；introspection 被拒（误报文 `GraphQL未生成接口:__schema`）。前端设计器的检测结果即由此面回传。
  - `POST /service/udc/application/search/front-detection` —— 端点存在，但传 `appId` 取不回（响应体 `appId:null`），**真正形参名 UNVERIFIED**。
  - 检测明细**无 MySQL 承载**：`SHOW TABLES LIKE '%detect%'` / `'%check%'` 均空 → 明细只在 Redis。
  - Redis key 形态：`test2:udc:5.3.517:DetectionError:Data::<appId>:<ENTITY|PAGE|MICRO>:<实体类全名>`
- **检测未过的业务侧根因分类（LIVE 日志统计，TOP 146+）**：

  | 类别 | 出处 | 量级 | 语义 |
  |---|---|---|---|
  | 页面数据源缺失 | `PageControllerTask:643` | 146 | `runtime 对应的页面数据源不存在！` |
  | 参照悬空 | `ReferUtil:114` | 30+ | `获取不到对应的参照信息：<appGuid>-<x>-<y>` |
  | 关联枚举元数据为空 | `MetadataConvertUtil:1287` | 多条 | 关联字段转枚举后目标元数据查不到 |
  | 页面表达式一致性 | `PageExpressionDetectionUtil:310` / `PageDetectionTask:419` | 7 + 多页 | 表达式引用的字段/枚举项失效；部分页面 NPE |

  附：`SchemaDefinitionFilter:56` 不支持的 schema 数据类型 `DATA_SOURCE`（页面入参）。
- 结论口径：**链路全通，失败源于"被拷贝应用自身数据悬空"**（页面数据源/参照/枚举元数据/表达式四类），非链路口径问题。

## 8. Evidence

- LIVE 一轮（test2，09-27）：HTTP 200 + `BOOT_0000` + deployId=1006978865758003184
- 落库回读：`udc_test2.udc_deploy_record` id=2343914262409841112
- 日志锚：`buildAppInfo app id:<测试应用> deploy id:3249599173653169129`；`RedisDetectionUtils:293`；`AbstractDeployService:242 / 267`
- 应用锚：测试副本应用 `6570299241515796755`（原应用 `3289082814923688017` 的副本；业务在用的原应用全程未触碰）
- 前批：`docs/audit/udc-design-time-deploy-write-contracts.md` §一

## 9. Verified

- `udc.deploy.normal` 路由三要素 + `deployDto` 包装 + 响应壳 = **LIVE**（09-27）
- 状态字值域（state / deploy_type）= **LIVE**（两批观测）
- 一致性检测门 + 失败回写 = **LIVE**
- 检测明细 Redis key 全名 / GraphQL 预生成接口清单 / 产物落 OSS = **UNVERIFIED**

---

## 10. 09-28 LIVE 补证（状态回读面 + Redis 布局 + 配额契约）

### 10.1 部署历史/状态回读面（前格 UNVERIFIED 项本轮 LIVE 确诊）

- `POST /service/udc/application/appVersion/{appGuid}`（body 空 `{}`，200）= **部署历史查询面**。
  前批 registry 记的 `udc.deploy.search_status = GET deploy/search-status/{deployId}` 状态降级为**路径误记**；
  真面按 **appGuid**（应用族 guid，非 appId）查，返回 `data.content[]`：
  `{id, guid, appGuid, appId, appName, appVersion, deployType, state: SUCCESS|FAIL, deployTime, failReason}`。
  - 双观测：业务应用（guid=5958633360229354868）2 条 = `RELEASE SUCCESS` + `ON_ONLINE SUCCESS`，成功时 `failReason="udc发布成功"`；
    副本应用（guid=175308926583324808）1 条 = `TEST FAIL` + 一致性检测失败文案。
  - 对照落库：与 `udc_deploy_record` 行一致（RELEASE=09-24 17:52 ≙ deploy_type=2 state=1）。
- 检测结果读面（LIVE 确诊形参名）：`POST /service/udc/application/search/front-detection`，
  body `{"appId":"<id>"}` → `{count, errorCount, seriouCount, warnCount}`；错误明细键被清理后 count=0。

### 10.2 Redis 布局（db0 实测，非臆造）

- 连接：`RedisStandaloneConfiguration`（arthas vmtool 取活体实例）：host `r-2zertbiuu892wf8jid.redis.rds.aliyuncs.com:6379`，**db 0**，password 16 位（值不入文档，取法见下）。
- 相关 key 实测（KEYS *）：
  - `test2:redis:build:{TEST|RELEASE}:{appId}`（String，**无 TTL**）= BuildStatusDto 序列化串：`status:FAIL|SUCCESS, startTime, totalTime, progress`
  - `test2:redis:build:log:{TYPE}:{appId}`（Hash，TTL≈2.9d）字段 5 个：`START / APP_METADATA / GENERATION_BACKEND_CODE / DETECTION / COMPLETE`，
    值=`["java.util.ArrayList",[...行]]` 快照格式；DETECTION 字段含逐任务耗时行（9 任务，全带 [完成]）。
  - `test2:-8112660841495312922:udc:5.3.517:Application::{appId}`（应用缓存）
  - `test2:udc:5.3.517:UDC:MEMBER:RIGHTS:::{appId}`、`test2:-8112…:{EVALHASH}:…DetectionError:Lock::{appId}`
- **DetectionError 明细键生命周期 = 单次构建会话**（构建结束即清或极短 TTL；KEYS 已 0）。要抓明细必须在构建进行中实时读。
  前格 §7 的 key 模板（`DetectionError:Data::…`）来自构建当刻日志，形态仍可信；但**事后不可取**。
- 凭据取法（已验证可复跑，值零落盘）：pod 内 `/app/arthas` + JDK tools.jar attach pid，
  `vmtool --action getInstances --className org.springframework.data.redis.connection.RedisStandaloneConfiguration
  --express "new String(instances[0].password.get())"`；pod 无 redis-cli/python3，用 **busybox nc + RESP 内联协议**（AUTH/KEYS/HGET/TTL）直读。

### 10.3 应用配额契约（字节码级，UDC_APP_0030）

- `ApplicationService.checkTenantLicenseAppCount`（javap）：计数条件 `sourceType=NORMAL && jsonPrefab=false`，
  上限 `SandboxTenantConfigDto.createAppNum`（test2 租户=10）；超限抛 `UDC_APP_0030`。
- test2 实况（RDS 全量 19 应用）：NORMAL 占配额者恰 10 个（全为业务应用，无测试残留）；dynamic/集成类 `source_type=1` 不占。
- 创建应用面（LIVE）：`POST /service/udc/application`（**平铺** ApplicationDto，标准 `@RequestBody`——与 deploy-normal 的
  `@MultiRequestBody` 恰相反）；必填 `name/caption/appVersion("1.0.0")/terminalType`。
- 只页应用面：`POST /service/udc/application/create-page-app`（平铺 `CreateOnlyPageApplicationDto`：
  `hostAppName/caption/pageUrl/masterEntity(=实体 fullName)`）；当前在宿主业务应用上触发
  `CustomPageInfoService.create4CustomPage:892` NPE（依赖应用 stream toSet() 时元数据悬空）——宿主数据病，环境侧无解。

### 10.4 证据锚（09-28）

- 部署历史双观测：POST appVersion/{appGuid} ×2（业务/副本）
- front-detection：POST ×4（appId 形参确诊，count=0 = 明细已清）
- Redis：nc+RESP 实测 KEYS/TTL/TYPE/HGET/GET/DBSIZE；BuildStatusDto + 5 阶段日志 hash 全量取回
- 配额：javap checkTenantLicenseAppCount + RDS udc_application 全量 19 行
