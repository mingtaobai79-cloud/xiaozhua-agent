# 设置发布链 runbook（build → publish → 资源可访问）

> 角色：implementer（C 组 · 设置域）· 2026-10-18 12:5x（GMT+8）
> 目标应用：`datamigration9000000000000000001`（appId `8704025620829192834`），环境 test2
> 证据等级：**本文件全部为 STATIC**（反编译签名 + 已有文档交叉），**未执行任何请求**
> 凭据：仅引用 `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json`，不打印、不落盘
> HANDOFF：`#SETTING-PUB-RUNBOOK`（main 12:40:44）
>
> **【覆盖边界】本 runbook 覆盖 = 3 个 Controller（Deploy / Deployment / Sandbox）、23 个端点。**
> 23 = **5 条执行步骤端点（步骤1–6，其中步骤6 上线仅登记不含）+ 18 条步骤7 登记备查端点**。
> 这个 23 **不是 udc-web 全量端点对账**（`UdcManagerController` 等未纳入）。
> 该计数**可用 §10 的三个 javap 文件独立复算**，不依赖任何外部脚本。复算命令（实跑得 12+6+5=23）：
> ```
> cd docs/audit/artifacts/udc-web-5.3.517-contracts
> cat DeployController.javap.txt DeploymentController.javap.txt SandboxController.javap.txt \
>   | grep -cE 'annotation\.(Post|Get)Mapping\('     # → 23
> ```
> **两个必踩的坑（都实测过）：**
> 1. **必须匹配全限定名 `annotation.(Post|Get)Mapping(`**。类级 `annotation.RequestMapping(` 是 **3**（每类一个），不能混入。
> 2. **不要用 `^\s+(Post|Get)Mapping\(` 这种「行首即短名」的写法 —— 它会得 0**，而且这个 0 极具误导性。
>    真实原因是：javap 的注解行是 `        org.springframework.web.bind.annotation.PostMapping(`，
>    **行首是缩进 + 全限定名**，短名并不在行首。对照：`^[[:space:]]+.*(Post|Get)Mapping\(` 得 23。
>    （顺带澄清一个易搞混的点：`@PostMapping(` 在这三个文件里出现 **0** 次，因为 javap 不保留 `@`；
>    而裸短名要**两条命令各跑一次**才得 23，**不是一条命令能得 18+5**：
>    ```
>    cat DeployController.javap.txt DeploymentController.javap.txt SandboxController.javap.txt | grep -cF 'PostMapping('   # → 18
>    cat DeployController.javap.txt DeploymentController.javap.txt SandboxController.javap.txt | grep -cF 'GetMapping('    # → 5
>    ```
>    **单跑 `PostMapping(` 只得 18**（它不命中 `GetMapping`），两式相加才 23。
>    ⇒ 短名能对上是**偶然**（这三个文件名与内容里没有同义串），**不可依赖**，换一批文件就会虚高。
>    所以我用全限定名一条命令：`grep -cE 'annotation\.(Post|Get)Mapping\('` → **23**。）
>
> **两套独立分解同得 23（互证无遗漏）**：按 Controller 是 12+6+5；按文档用途是 5 条执行步骤 + 18 条登记备查。
> 两条互不相交的路径落到同一个数 ⇒ 这 3 个 Controller 的注解方法**全数列出，无重复无遗漏**。
> （边界来源：auditor 意见，2026-10-18。）

---

## 0. 本文件的证据等级纪律（先读这条）

**本文件不含任何 LIVE 结论。** 每条端点都只写「STATIC 来源 + 待验证项」。

已经存在的 LIVE 材料（`docs/audit/settings/SET-PUB-1-publish-chain-live.md`，2026-10-18 01:41）
本文件**引用其观测事实**用于「基线/判据/STOP」段，但**不把它的结论当作本次执行的免验证项** ——
执行时必须自己重新取证，理由见 §7：该切片第③项当时 FAIL（应用侧缺陷），本次执行前须先确认缺陷状态。

标签约定：
- `STATIC` — 反编译签名行 / 已有文档段落，可回溯
- `待验证` — 本次 runbook 不覆盖，必须执行时现场取证
- `BLOCKED` — 已知外部阻塞

---

## 1. 端点序列（按执行顺序）

类级基路径（两条，均来自 `javap` 类级 `RequestMapping`）：
- `DeployController` → `udc/runtime`
- `DeploymentController` → `udc/deployment`

> **STATIC 来源（下同）**：
> `docs/audit/artifacts/udc-web-5.3.517-contracts/DeployController.javap.txt`（类级 `RequestMapping value=["udc/runtime"]`，文件末行附近）
> `docs/audit/artifacts/udc-web-5.3.517-contracts/DeploymentController.javap.txt`（类级 `RequestMapping value=["udc/deployment"]`）

> ⚠️ **完整 URL = 网关前缀 `/service/` + 类级 value + 方法级 value，此拼接规则是 STATIC 单源（UNVERIFIED 拼接机制）** ——
> 拼接结果与 LIVE 观测 URL 一致（`/service/udc/runtime/expect-deploy-time`），但拼接规则本身未从框架代码取证。
> **只读 §1 的执行者请勿把「URL 对」当成「拼接规则已证」**，详见 §8 的 R5。

### 步骤 0｜页面入口（必做，不可跳过）

| 项 | 值 |
|---|---|
| 页面 | `/main/child-frame/udc/app-design/application?appId=8704025620829192834` |
| 入口控件 | 顶部「测试」按钮 |
| 性质 | **页面点击**（硬约束 7：构建必须页面点击，不能纯 REST 替代） |
| STATIC 依据 | 前端 store 声明 `udcRuntimeDeployNormalPost` 等 op（`docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md` 附录「构建/部署执行链 op 组」） |

### 步骤 1｜预估时长（点「测试」时前端自动发出）

| 项 | 值 |
|---|---|
| 方法/路径 | `POST /service/udc/runtime/expect-deploy-time` |
| 关键参数 | `DeployParamDto`，`@MultiRequestBody`；**body 顶层键 = `deployParamDto`**（**不是裸 DTO，也不是 `deployDto`**）<br>【引用已有 LIVE 抓包，非本次结论】原文：`{"deployParamDto":{"deployType":"RELEASE","appId":"8704025620829192834","projectType":"ALL","terminalType":"ALL"}}` |
| 返回 | `SingleResponse<Long>`，`content` = **秒数**（LIVE 记录里是字符串 `"261"`，见 §7） |
| 性质 | 页面点击附带（不需要人手动调 REST） |
| STATIC 来源 | `DeployController.javap.txt` L744 `SingleResponse<java.lang.Long> expectDeployTime(DeployParamDto)`；L769 `PostMapping value=["expect-deploy-time"]`；L782 `@MultiRequestBody` |
| 角色要求 | `@HasRole("udcAppDesigner","OpsAdmin","udcSystemAdmin")`（同方法注解） |

### 步骤 2｜核心 publish（点「立即构建」时发出）

| 项 | 值 |
|---|---|
| 方法/路径 | `POST /service/udc/graphql?udcRuntimeDeployNormalPost`（GraphQL 包装层） |
| 底层 REST | `POST /service/udc/runtime/deploy-normal` |
| 关键参数 | `deployDto` 五字段：`{projectType, terminalType, deployType, appId, generateLog:true}`；`deployType="RELEASE"` 走测试构建。**注意位置：实际发的是 GraphQL 包装，五字段在 `variables.params0.deployDto`，不在 body 顶层**（形状详见下方 ⚠️ 块） |
| 返回 | `SingleResponse<DeployResultDto>`，含 `deployId`（**负 bigint 正常**）、`buildVersion` |
| 性质 | **页面点击**（点「立即构建」） |
| STATIC 来源 | `DeployController.javap.txt` L398 `deployNormal(DeployNormalDto)`；L427 `PostMapping value=["deploy-normal"]`；参数嵌套形态 `params:{deployDto:e}` 见 `SETTINGS-TABS-CALLCHAIN.md` L283 |

> ⚠️ **两处口径差异，执行时必须现场判定，不得预设**：
> 1. 页面实际发的是 GraphQL 包装（`?udcRuntimeDeployNormalPost`），底层 REST 是 `deploy-normal`。**两者不是替代关系**，是同一能力的两个入口；本 runbook 要求走页面点击，因此观测到的是 GraphQL 形态。
> 2. **两个端点的 body 形状不同，且都不在顶层带 `deployDto`**：
>    - `expect-deploy-time`（**裸 REST，无 GraphQL 包装**）：顶层键 = `deployParamDto`
>      ```
>      {"deployParamDto":{...四字段...}}
>      ```
>    - `udcRuntimeDeployNormalPost`（**GraphQL 包装**）：顶层是 `{query, variables}`，业务参数在 `variables.params0.deployDto`
>      ```
>      {"query":"query graphqlLoader (...) { data0: udcRuntimeDeployNormalPost(body: $params0) {...} }",
>       "variables":{"params0":{"deployDto":{"projectType":"ALL","terminalType":"ALL",
>                                            "deployType":"RELEASE","appId":"...","generateLog":true}}}}
>      ```
>    ⇒ **抄错的后果**：两个端点的顶层键互换了会 400 / 参数为空；只记住「`deployDto`」一个词也会错——
>    `expect-deploy-time` 用的是 `deployParamDto`（多一个 `Param`），且它是**扁平一层**，
>    而 `deploy-normal` 是 **`variables.params0.deployDto` 两层嵌套**。
>
>    **【这两条形状的来源】**：均为 2026-10-18 01:40–01:41 真实页面点击抓包（`implementer/evidence/SET-PUB-1-netcapture-step1-test-click.json` /
>    `…step2-deploy-click.json`），非注解推断。**注意 `@MultiRequestBody` 不能推出键名**——
>    两个方法都标了该注解，但顶层键一个是 `deployParamDto`、一个是 GraphQL 的 `variables`，
>    所以键名只能以抓包为准。

### 步骤 3｜就绪状态（同一次点击的伴随请求）

| 项 | 值 |
|---|---|
| 方法/路径 | `POST /service/udc/deployment/app-ready-state`（GraphQL op `udcDeploymentAppReadyStatePost`） |
| 关键参数 | `{appId}` |
| 返回 | `AppReadyStateDto`：`{state, msg, appVersion, enableLoginEntry, enableClearEntry, validate…}` |
| 性质 | 页面点击附带 |
| STATIC 来源 | `DeploymentController.javap.txt` `Post "/app-ready-state"` → `SingleResponse<AppReadyStateDto> get...` |

> ⚠️ **`state` + `msg:"DEPLOY_SUCCESS"` 是「上一次」的运行态，不是本次构建结果。**
> 【引用已有 LIVE 记录，非本次结论】SET-PUB-1 §2.3 观测：点击后仍返回旧版本的 RUNNING/DEPLOY_SUCCESS。

### 步骤 4｜最新测试信息

| 项 | 值 |
|---|---|
| 方法/路径 | `POST /service/udc/deployment/latest-test-info` |
| 关键参数 | `{appId}` |
| 返回 | `AppLeastTestInfoDto`：`{leastTestVersion, leastTester, testSuccess, buildTime}` |
| 性质 | 页面点击附带 |
| STATIC 来源 | `DeploymentController.javap.txt` `Post "/latest-test-info"` → `SingleResponse<AppLeastTestInfoDto>` |

### 步骤 5｜构建进度轮询（**唯一必须主动轮询的一步**）

| 项 | 值 |
|---|---|
| 方法/路径 | `GET /service/udc/sandbox/build-info/{appId}`（GraphQL op `udcSandboxBuildInfoAppGet`） |
| 关键参数 | path `{appId}` |
| 返回 | `AppBuildInfoDto`：`{state, progress, buildVersion, startTime, totalTime, logs[]}` |
| 性质 | **允许 REST**（只读轮询，非构建动作；不违反硬约束 7） |
| STATIC 来源 | `SandboxController.javap.txt` 类级 `RequestMapping "udc/sandbox"`；`Get "/build-info/{appId}"` → `SingleResponse<AppBuildInfoDto> getBuildInfo...` |
| 轮询纪律 | **每轮 ≤3 次、间隔 ≥30s**（与 /service 限流同口径） |

同族只读端点（本次不用，登记备查）：`GET /udc/sandbox/delta-build-info/{appId}`、`GET /udc/sandbox/release-build-info/{appId}`、`POST /udc/runtime/search-deploy-status/{deployId}`、`POST /udc/runtime/search-by-name/{appName}`、`POST /udc/runtime/search-deploy`、`POST /udc/runtime/deploy-statistics`。

### 步骤 6｜上线发布（本次 runbook **不含**，仅登记边界）

| 项 | 值 |
|---|---|
| 方法/路径 | `POST /service/udc/deployment/app-online-new`（GraphQL op `udcRuntimeDeployOnlinePost`，`deployType="ON_ONLINE"`） |
| STATIC 来源 | `DeploymentController.javap.txt` `Post "/app-online-new"`；`SETTINGS-TABS-CALLCHAIN.md` L288 |
| **本 runbook 不覆盖理由** | 本次目标是「build→publish→资源可访问」，`deploy-normal`(RELEASE) 即为测试构建发布。上线发布是**对外可见的不可逆动作**，须单独授权，不混在同一轮。 |

### 步骤 7｜同域只读端点（本次不用，逐条登记备查）

以下端点均为 `javap` 中**存在**（STATIC 解析，非运行实测），全部只读。**本 runbook 不调用它们**，登记的目的是：执行时若页面顺带发出，能识别、不误判为异常；以及后续补 R3（120 行选择规则）时用得上。

| 完整路径 | 方法 | STATIC 来源（javap 方法级 value） | `@HasRole` |
|---|---|---|---|
| `GET /service/udc/sandbox/delta-build-info/{appId}` | GET | `SandboxController.javap.txt` `Get "/delta-build-info/{appId}"` → `SingleResponse<AppBuildInfoDto>` | 无 |
| `GET /service/udc/runtime/frontend/metadata/{appId}` | GET | `DeployController.javap.txt` `Get "frontend/metadata/{appId}"` → `SingleResponse<FrontSandboxDto>` | 无 |
| `GET /service/udc/sandbox/release-build-info/{appId}` | GET | `SandboxController.javap.txt` `Get "/release-build-info/{appId}"` → `SingleResponse<AppBuildInfoDto>` | `OrgAdmin, udcAppDesigner, OpsAdmin, udcSystemAdmin` |
| `GET /service/udc/sandbox/select/{appId}` | GET | `SandboxController.javap.txt` `Get "/select/{appId}"` → `SingleResponse<SandboxInfoDto>` | 无 |
| `POST /service/udc/sandbox/select-roles` | POST | `SandboxController.javap.txt` `Post "/select-roles"` → `ListResponse<SandboxAppRoleDto>` | 无 |
| `POST /service/udc/runtime/search-deploy-status/{deployId}` | POST | `DeployController.javap.txt` `Post "search-deploy-status/{deployId}"` → `ListResponse<DeployRecordDto>` | `udcAppDesigner, OpsAdmin, udcSystemAdmin` |
| `POST /service/udc/runtime/search-by-name/{appName}` | POST | `DeployController.javap.txt` `Post "search-by-name/{appName}"` → `ListResponse<DeployRecordDto>` | `udcAppDesigner, udcSystemAdmin` |
| `POST /service/udc/runtime/search-deploy` | POST | `DeployController.javap.txt` `Post "search-deploy"` → `PageResponse<DeployRecordDto>` | `udcAppDesigner, udcSystemAdmin` |
| `POST /service/udc/runtime/deploy-statistics` | POST | `DeployController.javap.txt` `Post "deploy-statistics"` → `SingleResponse<Map>` | `udcAppDesigner, OpsAdmin, udcSystemAdmin` |
| `POST /service/udc/runtime/auth-access-url` | POST | `DeployController.javap.txt` `Post "/auth-access-url"` → `SingleResponse<AppAccessUrlDto>` | 无 |

> **写操作端点（本 runbook 明令禁用，仅登记以标明危险边界）**：
> `POST /service/udc/runtime/deploy/stop/{deployId}`（停构建）、`POST /service/udc/runtime/deploy-form`、
> `POST /service/udc/runtime/cross-deploy-form`（跨应用部署）、`POST /service/udc/runtime/deploy/ferry`（应用迁移）、
> `POST /service/udc/deployment/restart`、`POST /service/udc/deployment/app-online`、
> `POST /service/udc/deployment/app-online-new`、`POST /service/udc/deployment/app-delta-deploy`。
> 其中 `cross-deploy-form` / `deploy/ferry` 会**写到本任务授权之外的应用**，属硬约束 6 禁区。

---

## 2. traceId 取证点（每步都要取）

**两个来源，必须都取**（单靠响应体 traceId 无法与 DB 关联）：

### 2.1 响应体 `traceId`（每次都返回）

```
{"traceId":"17922589005077478983","data":{"data0":{...}}}
```

- 位置：响应 JSON **顶层** `traceId`（不是 `data` 里）
- 取值时机：每次 `/service` 调用之后，**立刻记录**，勿事后补

### 2.2 `udc_operation_log.trace_id`（DB 侧，用于关单）

```sql
SELECT create_time, module, sub_module, action_type, domain_caption, trace_id, log_path
FROM udc_test2.udc_operation_log
WHERE app_id = '8704025620829192834'
  AND create_time BETWEEN '<执行前 -1min>' AND '<执行后 +10min>'
ORDER BY create_time;
```

- 表：`udc_test2.udc_operation_log`，键 `app_id`（**数字字符串**）
- `trace_id` 非空率：【引用已有 LIVE 查询，非本次结论】2026-10-17 起 43/43 行均有值（`has_trace=43`）
- `action_type`：`1=CREATE / 2=DELETE / 3=UPDATE`（栏目/角色域已验；**发布链是否写入该表 = 待验证**，见 §6 风险 R2）

> ⚠️ **已知空洞（必须写在执行记录里，不许跳过）**：
> 2026-10-18 01:41 那次真实发布，`udc_operation_log` 在该时刻 **±90s 内 0 行**
> （该次观测的 SQL 与结果见 §7 复核记录）。⇒ **发布链可能根本不写 `udc_operation_log`**。
>
> **这件事为什么不能用注解来判**（2026-10-18 13:20 修正，原表述依据方向是错的）：
> javap 里 `Deploy` / `Deployment` / `Sandbox` 三个 Controller 的 `OperationLog`/`AuditLog` 注解 = 0，
> 只有 `RestApi` / `RestApiOperation` / `HasRole` / `MultiRequestBody` / `ParameterInfo`。
> **但「注解 = 0」不能推出「不写 oplog」** —— 我核对了两组反证：
> - 全库 54 个 Controller，`OperationLog` 字样只命中 1 个（`OperationLogController` 自身，
>   且它只有 `search`/`deleteAll`/`initData`/`searchOperationLogDetailsById`/`elementIsExist`，
>   **全是读或清空，没有写入方法**）；而同库 `RestApiOperation` 出现在 53/54、`HasRole` 49/54
>   ⇒ 注解体系真实存在且覆盖广，只是**它不负责写 oplog**。
> - 反证更硬：**栏目域确实写 oplog**（`ROUTE-S2-create-capture.md` L151-154 有 action_type=1/2/3、
>   module、sub_module、log_element、trace_id 全套 LIVE），**而 `PortletController`/`PortletGroupController`
>   的 `OperationLog` 注解同样是 0**。
>
> ⇒ 结论：**写 oplog 的机制在 Controller 层之外**（框架/AOP 拦截层，未取证），
> 用「Controller 有没有标 OperationLog」来推「这张表会不会被写」是无效推理。
> 所以本链判定只能靠**实测有没有行**，不能靠注解，也不能靠「本该有」的假设。
>
> 因此处置口径（三句话，缺一会滑向豁免）：
> 1. traceId 的主证据是 **2.1 响应体**；
> 2. 2.2 若为 0 行，**不得判 FAIL** —— 该表可能不承载发布链；
> 3. **但也不得据此判 PASS** —— 本链（`udc_operation_log`）**不作判据，只作登记**，
>    关单一律改走 `udc_deploy_record.deploy_id + create_time` 时间对齐。

### 2.3 第三处（DB 主键级，最硬的关单依据）

```sql
SELECT create_time, deploy_id, deploy_type, state, build_version, app_version,
       image_url, schema_storage_key, sql_storage_key, serial_num, msg
FROM udc_test2.udc_deploy_record
WHERE app_id = '8704025620829192834'
ORDER BY create_time DESC LIMIT 5;
```

`deploy_id` 与步骤 2 响应体 `content.deployId` **逐字相等** = 响应与落库同一条记录（最硬关联）。

---

## 3. 资源 URL 可访问性验证（判定核心，口径必须先对齐）

### 3.1 错误口径（先说清，避免重犯）

**裸 pageUrl 直探不是产物入口。**【引用已有 LIVE 探测，非本次结论】观测：`/datamigration…/xzhdetail958033` → `404 NoSuchKey`，
但**同环境已成功发布的应用**在同一裸 URL 上也 404 ⇒ 该 URL 本就不是产物入口，不能据此判「不可访问」。

### 3.2 正确口径

产物入口两条（`docs/audit/udc-semantics/menu-runtime-route.md` §2 SPA 加载链）：

```
{appName}/remoteEntry.{build_version}_5.3.17_1.0.0.js     ← 应用级 remoteEntry
{appName}/page-entry-{pageUrl}.{hash}.js                  ← 页面级 chunk
```

`build_version` 取自 `udc_deploy_record.build_version`（形如 `20261018014139`）。

### 3.3 匿名 vs 带 cookie（两者都要跑，结论不同含义）

| 方式 | 判读 |
|---|---|
| **匿名**（不带 cookie） | 能 200 ⇒ OSS 公开读；返 403 ⇒ 需要鉴权，**不代表资源不存在**（不可判 FAIL） |
| **带 cookie** | 200 + `Content-Type: application/javascript` + gzip 魔数 `1f 8b` ⇒ **资源真实存在且可读** |
| 两种都 404 且 body 含 `<Code>NoSuchKey</Code>` + `<Key>…</Key>` | **确定性判「产物未产出」**（不是权限/不是 SSO） |

**判定必须看 OSS 原生 XML 的 `<Code>`**，不能只看状态码：

```
<Error><Code>NoSuchKey</Code><Message>The specified key does not exist.</Message>
<Key>datamigration…/remoteEntry.20261018014139_5.3.17_1.0.0.js</Key>
```

### 3.4 版本身份对齐（S2 判据，可选但强烈建议）

`/{appName}/remoteEntry.js`（无 build 号）的响应内容 `sha256[:16]`，
与各 `remoteEntry.{build_version}` 快照逐一比对 —— **等值者即当前运行版本**。
1.0.14 那次【引用已有 LIVE 取证，非本次结论】：`c830f751b7ad1f76` ≡ `20261015192931`。

---

## 4. 基线（执行前必记，缺一项即不得开始）

全部只读。**执行前一次性采完并落盘 JSON**，执行后逐项对照。

```sql
-- ① 发布记录基线（行数 + 最新 deploy_id + 最新 state）
SELECT COUNT(*) n, MAX(create_time) last_time FROM udc_test2.udc_deploy_record
WHERE app_id='8704025620829192834';                       -- 【引用已有 LIVE 查询，非本次结论】基线 4 行以上，最新 01:41:44 state=2

-- ② 当前运行版本基线（S2 判据锚点）
SELECT app_version, state, fail_reason, show_version, deploy_time
FROM udc_test2.udc_app_version WHERE app_id='8704025620829192834' ORDER BY update_time DESC;

-- ③ 资源版本族基线（发布后 version 会整体刷成一个新值）
SELECT version, COUNT(*) c FROM udc_test2.udc_resource
WHERE app_id='8704025620829192834' GROUP BY version ORDER BY version DESC;
-- 基线：version=20 → 120 行；17→2；3→283；2→543；1→220；0→6（合计 1174）

-- ④ 资源总行数
SELECT COUNT(*) FROM udc_test2.udc_resource WHERE app_id='8704025620829192834';   -- 1174

-- ⑤ OSS 侧：当前 remoteEntry 的 sha256[:16]（步骤见 §3.4）
```

另需落盘的**非 DB 基线**：
- 当前 `remoteEntry.js` 的 `sha256[:16]` 与字节数
- 执行前 `udc_operation_log` 该应用的 `MAX(create_time)`（用于判断执行后有无新增行）

### 4.1 关键字段口径（抄错即全错）

> 下表口径来源：本角色 2026-10-18 12:41 只读 DB 复检（`implementer/evidence/S4-BASELINE-RECHECK-1241.json`）+ D25 定稿。
> 表中「数字/字符串」是对**该列实际存储形态**的读取结果，不是推断。本次执行前建议用一条 `SELECT` 复验。

| 表 | 键列 | 值形态 |
|---|---|---|
| `udc_deploy_record` | `app_id` | **数字** `8704025620829192834` |
| `udc_app_version` | `app_id` | **数字** |
| `udc_resource` | `app_id` | **数字** |
| `udc_operation_log` | `app_id` | **数字** |
| `portal_test2.portal_portlet_category` | `app_code` | **字符串** `datamigration9000000000000000001` |
| `portal_test2.portal_portlet_definition` | `app_id` 列 | **值 = 字符串 code**（D25 定稿，用数字查恒 0） |

---

## 5. 回滚 / 回到执行前状态

**发布是不可逆的**（OSS 产物 + 镜像 tag 会留存）。因此回滚策略是「不制造需要回滚的变更」：

| 风险 | 处置 |
|---|---|
| 本次构建成功但不应上线 | **不上线发布即可**。`deploy-normal`(RELEASE) 只产出测试构建，`app-online-new` 才对外。**本 runbook 不含上线步骤** |
| `udc_resource.version` 被刷成新值 | **不需要回滚**：该列是「当前发布版本号」，是预期行为。基线的用途是**确认刷了多少行**（1.0.15 那次刷了 120/1174 行，选择规则 UNVERIFIED） |
| 构建失败但 DB 留了 `state=2` 行 | **保留，不回删**。失败记录本身是证据；删记录会破坏证据链且属未授权写 |
| 误发上线 | **STOP 前置**：本 runbook 明令不调用 `app-online-new` / `app-online` / `app-delta-deploy` |

**唯一需要「恢复」的情形**：执行中发现自己发到了非目标应用 ⇒ 立即 STOP，
记录实际 appId 与 deployId，报 main，**不做任何补救性写操作**（写操作只允许 zzprobe 或本应用）。

---

## 6. STOP 条件（命中任一即停，登记不重试）

| # | 条件 | 判定依据 | 动作 |
|---|---|---|---|
| S1 | `BOOT_1006` / token 黑名单 | 响应体 `code:"BOOT_1006"` | **立即停**。这是共享账号被踢，重试会加剧互踢。登记后转 STATIC/DB 工作 |
| S2 | 403 / 401 | HTTP 状态码 | 停，记录 URL 与响应体；**不要换账号重试** |
| S3 | 限流到顶 | 本轮 `/service` 已 3 次，或距上次 <30s | 停，等窗口满足后再继续；**不用页面刷新绕过** |
| S4 | 步骤 5 轮询返回终态且 `state` 非成功 | `state` 字符串 + `logs[]` 含 `[ERROR]` | 停，取 `udc_deploy_record` 该 `deploy_id` 行，把失败原因原文落盘 |
| S5 | 构建超时 | 超过步骤 1 返回的预估秒数 × 2 | 停，记录 `progress` 停滞值，不重复点击构建 |
| S6 | 页面出现 SSO 跳转 / 登录框 | URL 变化或 DOM 出现登录表单 | 停，**不猜密码、不重登**（会踢掉其他两组） |

**STOP 后必做**：把「已执行到第几步 / 已产生哪些 `deploy_id` / 基线是否被改动（逐项对照 §4）」
写进执行记录。**已产生的 deploy 记录不回删。**

---

## 7. 已有执行记录的观测事实（引用，非本次结论）

来源：`docs/audit/settings/SET-PUB-1-publish-chain-live.md`（2026-10-18 01:41–02:10）。
**引用的目的是：本次执行前先知道「上次是怎么失败的」，不是替代本次取证。**

| 观测 | 值 |
|---|---|
| 上次 publish 回包 | `deployId=-3191446022183863452`，`traceId=17922589005077478983` |
| 上次构建终态 | **失败**，`udc_deploy_record.state=2`，`image_url/schema/sql/serial_num` 四字段全 null |
| 失败原文（DB 权威） | `udc_app_version.fail_reason` = `java.lang.NumberFormatException: For input string: "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795"`，位置 `NumberFormatException.forInputString` |
| 失败阶段（构建日志） | 「生成后端代码」阶段，前序「应用元数据准备」「一致性检测」均完成 |
| 资源侧结果 | 新 build `20261018014139` 的 remoteEntry → `404 NoSuchKey`（未产出）；旧 `20261015192931` → 200 |
| 运行态版本 | 仍服务 1.0.14 |

> 本次执行前**必须先查**：该 `XzhExp950795` 实体是否已修复。
> 查法（只读）：`SELECT MAX(create_time), state, LEFT(fail_reason,200) FROM udc_test2.udc_deploy_record WHERE app_id='8704025620829192834' ORDER BY create_time DESC LIMIT 1;`
> 以及看 `udc_app_version` 最新行的 `state`（1=成功）。**若最新仍 state=2，本次构建必然同样失败，应报 main 不要空跑配额。**

---

## 8. 本次 runbook 的已知未闭环项（不掩盖）

| 项 | 等级 | 说明 |
|---|---|---|
| R1 构建终态枚举值 | UNVERIFIED | `FAIL` vs `FAILED` 无原始帧支撑（SET-PUB-D2 已作废）；本次执行**必须落盘终态原始帧**才能定 |
| R2 发布链是否写 `udc_operation_log` | UNVERIFIED | 01:41 那次 ±90s 内该表 0 行；需本次执行后复查 |
| R3 `udc_resource.version` 刷新的 120 行选择规则 | UNVERIFIED | 1174 行只刷 120，规则未定位 |
| R4 `udcRuntimeAuthAccessUrlPost` 真实用途 | UNVERIFIED | 【引用已有 LIVE 观测】返回 `{pcHomeUrl:null, mobileHomeUrl:null}`，未产出可用 URL |
| R5 类级基路径拼接 | STATIC（单源） | `udc/runtime` + `expect-deploy-time` 是按 `javap` 类级+方法级注解**拼接**得出；LIVE 观测的 URL 与拼接结果一致（`/service/udc/runtime/expect-deploy-time`），但拼接规则本身未从框架代码取证 |

---

## 9. 执行清单（打印出来逐项打勾用）

```
[ ] 0  查 XzhExp950795 是否已修复（§7）—— 未修复则 STOP 报 main
[ ] 1  采基线 §4 ①~⑤ + remoteEntry sha256 + oplog MAX(create_time)，落盘 JSON
[ ] 2  开干净 tab（勿复用已知超时的 tab），导航到应用设计页
[ ] 3  点「测试」→ 记 expect-deploy-time 的 traceId + content 秒数
[ ] 4  点「立即构建」→ 记 udcRuntimeDeployNormalPost 的 traceId + deployId
[ ] 5  轮询 build-info（≤3 次/轮，≥30s），落盘终态原始帧（R1）
[ ] 6  DB 回读 deploy_record（按 deployId 精确命中）+ app_version + resource
[ ] 7  资源面：remoteEntry.{build_version} 匿名 + 带 cookie 各一次，记 <Code>
[ ] 8  版本身份：remoteEntry.js sha256[:16] 对齐（S2）
[ ] 9  对照基线，逐项写「变 / 不变」，不改判 PASS 直到三项齐
[ ] 10 若 STOP：登记停在哪步 + 已产生 deploy_id + 基线是否被改
```

**PASS 三要素（缺一即 UNVERIFIED）**：
① publish 真实调用回包（页面点击触发，含 traceId）
② DB 回读落库（`deploy_record` 精确命中 + `app_version` + `resource`）
③ 新版本资源**运行态可访问**（`remoteEntry.{build_version}` 200 + gzip + 版本身份对齐）

---

## 10. 证据来源索引

| 用途 | 文件 |
|---|---|
| `DeployController` 12 端点签名 | `docs/audit/artifacts/udc-web-5.3.517-contracts/DeployController.javap.txt` |
| `DeploymentController` 6 端点签名 | `docs/audit/artifacts/udc-web-5.3.517-contracts/DeploymentController.javap.txt` |
| `SandboxController` build-info | `docs/audit/artifacts/udc-web-5.3.517-contracts/SandboxController.javap.txt` |
| 构建/部署 op 组 + 参数形态 | `docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md` §附录（L277–292） |
| SPA 产物加载链 | `docs/audit/udc-semantics/menu-runtime-route.md` §2 |
| 上次全链观测（引用） | `docs/audit/settings/SET-PUB-1-publish-chain-live.md` |
| 前端 op 表 | `docs/audit/udc-semantics/FRONTEND-CHUNK-INVENTORY.md` |
| 凭据（只引用路径） | `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json` |

### 10.1 过程工具（**不在仓库内，非本 runbook 的复算依赖**）

本 runbook 的 23 端点计数**不依赖**任何脚本（见卷首复算命令）。但编制期确实用过两个一次性脚本，
留指纹在此，供需要时辨认版本 —— 它们**不在 git 里，半年后可能已不存在**：

| 用途 | 位置（仓库外） | 指纹 |
|---|---|---|
| 端点双向对账（forward/reverse） | `<HERMES_HOME>\cache\scratch\verify_runbook_gate.py`（副本 `implementer/evidence/`） | 7,914 B / sha256 前 16 位 `3a86cc9aba42aab6` |
| 注入实验（5 case 判别力） | `<HERMES_HOME>\cache\scratch\gate_inject_test.py` | — |

⚠️ **该闸门有两个版本，行为不同**，认版本只看输出里的 `reverse_enforced` 字段：
- **默认强制反向版**（`reverse_enforced=true`，即上表指纹这版）：反向漏列即 FAIL；
- 早期版本（无该字段或 `false`）：**反向漏列默认放过，只有加 `--strict` 才拦** —— 用早期版跑出「全过」不代表没漏列。

⇒ 这也解释了为什么正文只写「23 端点可用 javap 复算」而不写「闸门验证通过」：
**一句「23/23 全过」若不说清是哪个版本、开没开开关，等于没说。**
