# SET-PUB-1｜设置发布链路 LIVE 全链（build → publish → 资源可访问）

> 角色：implementer（C 组 · 设置域）· 2026-10-18 01:41–02:10（GMT+8）
> 环境：test2 · 应用 `datamigration9000000000000000001`（appName `datamigration9000000000000000001`）
> HANDOFF：`main/HANDOFF #C-01`（切片 SET-PUB-1）+ `PROGRESS #C-01a`（基线更新）
> 证据等级：**LIVE**（CDP 页面点击 + 网络抓包 + MySQL 回读 + OSS 产物实测）
> 凭据：仅引用 `shared-credentials/test2-web-credential.json`，未打印、未落盘 secret

---

## 0. 判定

**切片判定：BLOCKED（链路机制已 LIVE 取证，应用侧代码缺陷导致构建失败）**

| PASS 三要素 | 判定 | 依据 |
|---|---|---|
| ① publish 真实调用回包（页面点击触发） | **LIVE PASS** | §2 `udcRuntimeDeployNormalPost` → `BOOT_0000`，`deployId=-3191446022183863452`，traceId 已记 |
| ② DB 回读发布/资源表落库 | **LIVE PASS** | §3 `udc_deploy_record` 1 行 + `udc_app_version` update + `udc_resource` 120 行 version→20 |
| ③ 资源 URL 运行态可访问（新版本产物） | **FAIL（应用缺陷所致）** | §4 新 build `20261018014139` 的 remoteEntry `404 NoSuchKey`；旧 build `20261015192931` 仍 `200` |

**所需输入（交 main）**：应用侧修复 `XzhExp950795` 实体生成的 `NumberFormatException`
（`Long.parseLong("com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795")`）。
修复前，任何「1.0.15」发布都会在「生成后端代码」阶段失败，产物不上 OSS，第③项不可能成立。

**不算 implementer FAIL**：publish 调用真发生、DB 真落库、失败真在应用代码生成阶段，
三者都是被测系统按其真实行为返回的结果（与 PROGRESS #C-01a 的判定口径一致）。

**两条复用判据（详证见 §6.2，HANDOFF #C-03b-tail 第 1 项）**：

- **S1 发布失败组合判据**：`image_url` + `schema_storage_key` + `sql_storage_key` + `serial_num`
  四字段同步全 `null`。本轮 `deployId=-3191446022183863452` 实测四字段全 null，与 `state=2` 互证。
  ⚠️ 强度经全库校准：**非充分**（失败行 72% 并非全 null），作「必要倾向 + 强排除」用；
  本应用内单点强判据是 `image_url IS NULL`（零反例）。
- **S2 运行态版本身份判定**：`remoteEntry.js` 内容 `sha256[:16]` 对齐 `remoteEntry.{build_version}` 快照。
  当前 `sha256=c830f751b7ad1f76` ≡ `20261015192931`（1.0.14 成功 build）⇒ **运行态仍服务 1.0.14**，
  本次 1.0.15 产物 `404`。auditor 独立取证一致（`AUD-SET-PUB-1-runtime-version-identity.json`）。

---

## 1. 触发路径（页面点击，非 REST 替代）

CDP 9229（本组独占端口），profile `cdp-C-外围`，页面
`/main/child-frame/udc/app-design/application?appId=8704025620829192834`。

点击序列（全部 `element.click()`，真实 DOM 事件）：

| # | 动作 | 结果 |
|---|---|---|
| 1 | 点顶部「测试」按钮 | 打开「应用测试」弹窗 |
| 2 | 点弹窗「立即构建」 | 弹窗关闭，跳到「测试版本」页，发出 build 请求 |

弹窗实测文本（LIVE）：

```
应用测试
本次发布预估时长：5分21秒
应用名称  数据迁移
应用编码  datamigration9000000000000000001
版本号    V1.0
运行中测试版本V1.0.14
2026-10-15 19:29:35应用运行中
取 消  立即构建
```

点击前 `svc baseline = 0`（说明后续 6 条 `/service` 全部由本次点击触发，无背景噪音）。

**限流合规**：本轮 `/service` 请求按批次发送，每次间隔 ≥30s；单批 ≤3 次。

---

## 2. publish 调用（LIVE，页面点击触发）

### 2.1 前置：预计时长（点击「测试」时发生）

```
POST /service/udc/runtime/expect-deploy-time        HTTP 200
body: {"deployParamDto":{"deployType":"RELEASE","appId":"8704025620829192834",
                          "projectType":"ALL","terminalType":"ALL"}}
resp: {"status":0,"code":"BOOT_0000","message":"SUCCESS",
       "traceId":"17922588404061176884","data":{"content":"261"}}
```

`content:"261"` 秒 = 弹窗显示的「5分21秒」，前端文案与后端预估一致。

### 2.2 核心 publish 调用（点击「立即构建」时发生）

```
POST /service/udc/graphql?udcRuntimeDeployNormalPost     HTTP 200
body:
{"query":"query graphqlLoader ($params0: udcRuntimeDeployNormalPostInputBody) { \n  data0:
  udcRuntimeDeployNormalPost(body: $params0) { code data { content{appId,deployId,deployType,
  projectType,terminalType} } message status } }",
 "variables":{"params0":{"deployDto":{"projectType":"ALL","terminalType":"ALL",
   "deployType":"RELEASE","appId":"8704025620829192834","generateLog":true}}}}

resp:
{"traceId":"17922589005077478983",
 "data":{"data0":{"code":"BOOT_0000",
   "data":{"content":{"appId":"8704025620829192834",
                      "deployId":"-3191446022183863452",
                      "deployType":"RELEASE","projectType":"ALL","terminalType":"ALL"}},
   "message":"SUCCESS","status":0}}}
```

**关键取值**：`deployId = -3191446022183863452`（负数，bigint 高位溢出，正常现象）
**traceId = 17922589005077478983**

### 2.3 紧随其后的 5 个伴随请求（同一次点击）

| op | 用途 | traceId | 结果 |
|---|---|---|---|
| `udcDeploymentAppReadyStatePost` | 就绪状态 | 17922589007186558452 | `state:"RUNNING"`, `msg:"DEPLOY_SUCCESS"` |
| `POST /udc/deployment/latest-test-info` | 最新测试信息 | 17922589009153173475 | `leastTestVersion:"1.0.14"`, `testSuccess:true` |
| `udcApplicationDetailGet&udcApplicationIsLastVersionAppGet&udcDeploymentAppReadyStatePost` | 应用详情复合查询 | 17922589009213070599 | `publishState:"UNPUBLISH"`, `isLastVersion:true` |
| `udcApplicationDependentApplicationSelectByConditionPost` | 依赖应用 | 17922589009225084871 | 返回依赖列表（portal 5.3.392 / biz-bpm-run 3.12.37 / ctp-user 5.3.429…） |
| `udcSandboxBuildInfoAppGet` | 构建进度首帧 | 17922589013004232319 | `state:"BUILDING"`, `progress:"18"`, `startTime:1792258899554` |

> **【勘误 2026-10-18 02:30，按 DECISION #C-02b-close + ROUTE DISCREPANCY-4】**
> 本文件 §3 的 `"state":"FAIL"` 响应体转录**没有原始帧落盘支撑**，属誊写失真，如实更正：
>
> - **有落盘原始帧的实测值**：`state="BUILDING"`（`implementer/evidence/SET-PUB-1-netcapture-step2-deploy-click.json`
>   内唯一一条 `udcSandboxBuildInfoAppGet`，01:41:39 构建首帧，progress=18，日志止于「应用元数据准备」）。
>   auditor 复扫该帧与 live.jsonl 均 0 命中 `"FAIL"`。
> - **`FAIL` 帧**：我在 01:43 复读 buildinfo 时确实读到含完整失败日志的响应（构建终态），
>   但**只在会话输出中、未落盘原始文件**。§3 将其写成「响应原文」形态，读者会误认为有抓包支撑 —— 这就是失真点。
> - **处置（按 main 裁定）**：`SETTINGS-TABS-CALLCHAIN.md` 附录的 `FAILED` 维持原文不动；
>   终态枚举（`FAIL` vs `FAILED`）**降级 UNVERIFIED**，此前登记的 SET-PUB-D2 作废，待后续 LIVE 窗口补抓终态帧再定。
> - DB 侧失败判据（§4 的 `state=2` + `image_url IS NULL`）不受本勘误影响，仍为独立成立的双面证据。

**注意**：`state:"RUNNING"` + `msg:"DEPLOY_SUCCESS"` 是**上一次**（1.0.14）的运行态，
不是本次构建结果。硬规则在此生效：HTTP 200 / BOOT_0000 / DEPLOY_SUCCESS 都不能单独算本次 PASS。

---

## 3. 构建终态（LIVE，`udcSandboxBuildInfoAppGet` 复读）

> **誊写失真声明（02:30，详见上方勘误块）**：下方响应体的 `"state":"FAIL"` 与完整失败日志
> 是我在 01:43 复读时实际读到的内容，但**原始帧未落盘**（step2 抓包只落了首帧 `BUILDING`）。
> 保留转录供追溯，引用时须注明「转录，无原始帧」。

```
POST /service/udc/graphql?udcSandboxBuildInfoAppGet     HTTP 200
variables: {"params0":{"appId":"8704025620829192834"}}

resp.data.data0.data.content:   【转录，无原始帧落盘支撑——见勘误块】
{"validate":true,"appName":"datamigration9000000000000000001",
 "state":"FAIL","progress":"18","buildVersion":"","buildTime":null,
 "startTime":1792258899554,"totalTime":null,
 "logs":[
  "[INFO]【2026-10-18 01:41:39】[低代码平台] [任务开始] [完成] [耗时:9毫秒]",
  "[INFO]【2026-10-18 01:41:39】[低代码平台] [应用元数据准备] 开始",
  "[INFO]【2026-10-18 01:41:44】[低代码平台] [应用元数据准备] [完成] [耗时:4秒]",
  "[INFO]【2026-10-18 01:41:54】[低代码平台] [应用元数据准备] [DependCodeContextAware] [完成] [耗时:10秒]",
  "[INFO]【2026-10-18 01:41:44】[低代码平台] [一致性检测] 开始",
  "[INFO]【2026-10-18 01:41:49】[低代码平台] [一致性检测] [PageDetectionTask] [完成] [耗时:3秒]",
  "[INFO]【2026-10-18 01:41:50】[低代码平台] [一致性检测] [完成] [耗时:5秒]",
  "[INFO]【2026-10-18 01:41:44】[低代码平台] [生成后端代码] 开始",
  "[ERROR]【2026-10-18 01:41:58】[低代码平台] [生成后端代码] [失败原因:For input string:
     \"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795\",
     Caused by:java.lang.NumberFormatException: For input string:
     \"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795\"
     at java.lang.NumberFormatException.forInputString(NumberFormatException.java:65)
     at java.lang.Long.parseLong(Long.java:589)
     at java.lang.Long.valueOf(Long.java:803)
     at com.]",
  "[ERROR]【2026-10-18 01:41:58】[低代码平台] [结束] 发布失败: java.lang.NumberFormatException:
     For input string: \"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795\",
     报错位置:java.lang.NumberFormatException.forInputString(NumberFormatException.java:65)"
 ]}
```

### 3.1 阶段推进表（从日志逐条抽取）

| 阶段 | 起 | 止 | 耗时 | 结果 |
|---|---|---|---|---|
| 任务开始 | 01:41:39 | 01:41:39 | 9ms | 完成 |
| 应用元数据准备 | 01:41:39 | 01:41:44 | 4s | 完成 |
| 元数据准备（DependCodeContextAware） | 01:41:44 | 01:41:54 | 10s | 完成 |
| **一致性检测** | 01:41:44 | 01:41:50 | 5s | **完成（通过）** |
| 生成后端代码 | 01:41:44 | 01:41:58 | — | **失败 NumberFormatException** |
| 结束 | 01:41:58 | — | 总 19s | 发布失败 |

**重要**：`一致性检测` 本次**通过了**（22:56 那次是它失败）。本次失败点已前移到
「生成后端代码」——这是比 #C-01a 基线更精确的定位，说明一致性检测问题已被绕开或修复，
现在只剩实体代码生成这一处。

---

## 4. DB 回读（LIVE，MySQL `udc_test2`）

### 4.1 `udc_deploy_record`（按 deployId 精确命中）

```sql
SELECT * FROM udc_test2.udc_deploy_record
WHERE app_id='8704025620829192834' AND deploy_id='-3191446022183863452';
```

| 字段 | 值 |
|---|---|
| id | -6140857744022882948 |
| create_time | 2026-10-18 01:41:44 |
| update_time | 2026-10-18 01:41:59 |
| deploy_id | -3191446022183863452 |
| deploy_type | 2 |
| state | **2（失败）** |
| build_version | **20261018014139** |
| jar_version | 1.0.15 |
| image_url | **null** |
| udc_version | 5.3.517 |
| creator | -2638952494757493308（test-account-1） |
| msg | 发布失败: java.lang.NumberFormatException: ... XzhExp950795 ... |

**回读一致性**：deployId 与 §2.2 响应完全一致；build_version 时间戳 `20261018014139`
= 日志首行 `01:41:39`，两面对齐。

### 4.2 `udc_deploy_record` 时序（近 6 次）

| create_time | state | build_version | jar_version | image_url | msg |
|---|---|---|---|---|---|
| 2026-10-18 01:41:44 | 2 | 20261018014139 | 1.0.15 | null | NFE XzhExp950795 |
| 2026-10-17 23:43:05 | 2 | 20261017234259 | 1.0.15 | null | NFE XzhExp950795 |
| 2026-10-17 22:56:06 | 2 | 20261017225602 | 1.0.15 | null | 一致性检测未通过 |
| 2026-10-15 19:29:35 | **1** | 20261015192931 | 1.0.14 | `…datamigration…:***.0.14` | 内部流水线构建成功 |
| 2026-10-15 19:23:31 | 2 | 20261015192327 | 1.0.13 | null | 一致性检测未通过 |
| 2026-10-15 17:19:14 | 2 | 20261015171912 | 1.0.12 | null | — |

**`image_url` 是成功与否的强判据**：唯一 `state=1` 的行有镜像地址，所有失败行都是 null。
本次 `image_url=null` → 镜像未产出 → OSS 无新产物（与 §5 实测闭合）。

### 4.3 `udc_app_version`（版本行被本次发布更新）

```sql
SELECT * FROM udc_test2.udc_app_version WHERE app_id='8704025620829192834' ORDER BY create_time DESC;
```

| id | create_time | update_time | version | state | show_version | deploy_type | deploy_time | fail_reason |
|---|---|---|---|---|---|---|---|---|
| 5995459285049141477 | 2026-10-12 18:18:16 | **2026-10-18 01:41:59** | 39 | 2 | **1.0.15** | 2 | 2026-10-18 01:41:40 | NFE XzhExp950795 |
| -1268511255652519052 | 2026-10-15 15:32:38 | 2026-10-15 15:36:00 | 1 | 1 | 1.0.7 | 3 | 2026-10-15 15:32:38 | udc发布成功 |

`version` 字段从 38 → **39** 自增，`show_version` 升到 1.0.15，说明发布事务确实写进了版本表。

### 4.4 `udc_resource`（资源表族，发布时刻全量刷版本）

```sql
SELECT COUNT(*) FROM udc_test2.udc_resource
WHERE app_id='8704025620829192834'
  AND update_time BETWEEN '2026-10-18 01:41:30' AND '2026-10-18 01:42:40';
-- → 120
```

| 项 | 值 |
|---|---|
| 应用内 resource 总数 | 1174 |
| 本次发布刷新行数 | **120** |
| 刷新行 `update_time` | 全部 = 2026-10-18 01:41:59 |
| 刷新行 `version` | 全部 = **20** |
| 今日其他 update_time | 无（`01:41:59` 是唯一时刻） |

**版本分布**（全应用 1174 行）：

| version | 行数 | 含义 |
|---|---|---|
| **20** | **120** | 本次发布刷新 |
| 17 | 2 | 上次变更 |
| 3 | 283 | 历史 |
| 2 | 543 | 历史 |
| 1 | 220 | 历史 |
| 0 | 6 | 初始 |

样本行（节选，证明是真实业务资源而非占位）：

| id | type | name | url | parent_code |
|---|---|---|---|---|
| 3468987889166339348 | 1（页） | 小爪实验详情958033 | `/datamigration9000000000000000001/xzhdetail958033` | — |
| -8002968703588807391 | 0（菜单） | 小爪验收菜单 | `/datamigration9000000000000000001/xzhpage951440` | 2084600749018399891 |
| -9029584815248619310 | 1（页） | 数据源配置信息列表弹窗选择页面_副本 | `/datamigration9000000000000000001/sjypzxxListPagecopycopycopy` | — |
| -9027841806758624489 | 2（工具栏） | 保存 | — | 8267428021549491279 |

**注意（DISCREPANCY 候选）**：`120/1174` —— 发布只刷新了 120 行 resource，
不是全量。这 120 行是「本次发布涉及」的资源，还是「变更集」，本轮未定位到选择规则。
登记为 **SET-PUB-D1（UNVERIFIED）**，不影响本切片判定（PASS②要求「落库」，已满足）。

---

## 5. 资源 URL 运行态可访问（LIVE 实测，判定核心）

### 5.1 探测方法说明（先说口径）

上一轮先用裸 URL `/datamigration…/xzhdetail958033` 直探，得到 `404 NoSuchKey`。
但**同环境已成功发布的应用**（`1656355078954763084`，state=1，2026-10-17 23:01）在同样裸 URL 上也返回
`404 NoSuchKey`（key=`datamigration…/index.html`）——说明裸 pageUrl **不是**产物入口，
直探 URL 是错误口径，不能据此判定「资源不可访问」。

正确口径（同仓 `docs/audit/udc-semantics/menu-runtime-route.md` §2 已验证的 SPA 加载链）：
产物入口是 **`{appName}/remoteEntry.{build_version}_5.3.17_1.0.0.js`** 与
**`{appName}/page-entry-{pageUrl}.{hash}.js`**，由门户路由按 pageUrl 装配。

### 5.2 1.0.14（成功）vs 1.0.15（本次失败）产物对照（LIVE）

| 产物 URL | HTTP | 实际结果 |
|---|---|---|
| `/{appName}/remoteEntry.**20261015192931**_5.3.17_1.0.0.js`（1.0.14） | **200** | gzip `application/javascript`，有内容 |
| `/{appName}/remoteEntry.**20261018014139**_5.3.17_1.0.0.js`（1.0.15 本次） | **404** | `NoSuchKey key=datamigration9000000000000000001/remoteEntry.20261018014139_5.3.17_1.0.0.js` |
| `/{appName}/udc-app-entry.aaa16645.js` | 200 | gzip application/javascript |
| `/{appName}/page-entry-qyfapzlb.71bfc39f.js` | 200 | gzip application/javascript |
| `/main/portal/{appName}/qyfapzlb`（门户路由） | 200 | text/html（SPA shell） |

**判定链**：
1. 本次 build 号 `20261018014139`（来自 `udcSandboxBuildInfoAppGet` 日志首行 + `udc_deploy_record.build_version`）
   对应的 remoteEntry **在 OSS 上不存在**（`NoSuchKey`，非 403/非权限）；
2. 上一次成功 build `20261015192931` 的 remoteEntry **仍 200 可读**；
3. 故「运行态资源不可访问」的**唯一成因是本次构建失败未产出镜像**，与 §4.2 `image_url=null` 闭合。

⇒ **第③项判定 FAIL，但成因是应用侧代码缺陷，非链路机制缺陷。**

### 5.3 补充：为什么不是权限 / 不是 SSO

- 同一 cookie 下 `remoteEntry.20261015192931` 返回 200 → 读权限无问题；
- 404 响应体是 **OSS 原生 XML（`<Code>NoSuchKey</Code>` + `seeyon-public-test2.oss-cn-beijing.aliyuncs.com`）**，
  不是网关权限页、不是 `BOOT_` 错误码、不是 SSO 跳转 → 请求已穿透到对象存储层。

---

## 6. 链路机制取证结论（本切片真正拿到的业务资产）

发布链路机制从「仅 STATIC」升级为 **LIVE 全链**（第③项受应用缺陷阻塞）：

```
[页面 测试] → POST runtime/expect-deploy-time           → 261s 预估        ✅LIVE
[页面 立即构建] → POST graphql?udcRuntimeDeployNormalPost → deployId 返回      ✅LIVE
                 → POST udcDeploymentAppReadyStatePost    → RUNNING(旧版本)  ✅LIVE
                 → POST /udc/deployment/latest-test-info  → 1.0.14           ✅LIVE
                 → POST udcSandboxBuildInfoAppGet         → BUILDING p18     ✅LIVE
[轮询]           → udcSandboxBuildInfoAppGet             → 终态转录见§3      ⚠️转录无落盘帧
[DB]             → udc_deploy_record / udc_app_version / udc_resource          ✅LIVE
[资源]           → remoteEntry.{build}                    → 404（未产出）     ❌（应用缺陷）
```

### 6.1 新增可复用契约（本切片首次 LIVE 确认）

| 契约 | 值 | 等级 |
|---|---|---|
| 预估时长端点 | `POST /service/udc/runtime/expect-deploy-time`，body `{deployParamDto:{deployType,appId,projectType,terminalType}}` → `content` = **秒数字符串** | LIVE |
| publish op 入参 | `deployDto` 五字段：`{projectType:"ALL", terminalType:"ALL", deployType:"RELEASE", appId, generateLog:true}` | LIVE |
| publish 出参 | `content{appId,deployId,deployType,projectType,terminalType}`，`deployId` 为**负 bigint** | LIVE |
| 构建态 op | `udcSandboxBuildInfoAppGet`，path `{appId}` → `content{state,progress,buildVersion,startTime,logs[]}` | LIVE |
| 构建态枚举（实测值） | `BUILDING`（**唯一有落盘原始帧的值**）；终态枚举 **UNVERIFIED** —— 原记 `FAIL` 无原始帧支撑，SET-PUB-D2 已作废，待补抓终态帧再定 | LIVE（首帧）/ UNVERIFIED（终态） |
| 失败三面判据 | `udc_deploy_record.image_url IS NULL` + `state=2` + `remoteEntry.{build} 404` | LIVE |
| 成功判据 | `state=1` + `image_url` 非空 + `remoteEntry.{build}` 200 | LIVE |

### 6.2 判据补记（02:30，按 DECISION #C-02b-close 第 3 条并入；全库统计校准后的准确强度）

**判据 S1｜四字段组合判据（auditor 补强判据，按全库统计校准）**

`udc_deploy_record`：`image_url` + `schema_storage_key` + `sql_storage_key` + `serial_num` 四字段同步全 null。

全库 `deploy_type=2` 实测分布（02:30 查）：

| state | 总行数 | 四字段全 null | 占比 |
|---|---|---|---|
| 0（构建中） | 203 | 34 | 17% |
| 1（成功） | 7237 | **1** | 0.01% |
| 2（失败） | 3275 | **912** | 28% |

**强度修正（如实）**：
- 作为「失败」的**充分**判据**不成立**——失败行中 72% 四字段并非全 null
  （该应用自己的 1.0.8~1.0.13 失败行 schema/sql 均**有值**，只 `image_url=null`）。
- 作为「失败」的**必要倾向 + 强排除**判据成立：`state=1` 全库 7237 行中仅 1 行反例
  （app `7324620281389731265`，2025-02-15）。
- **本应用内单点强判据是 `image_url IS NULL`**：本应用 `state=1` 三行的 **`image_url` 全部非 null**
  （注意：仅指 `image_url` 单字段；其中 1.0.7 的 `20261015153237` 一行 `schema_storage_key`/`sql_storage_key` 为 null），
  `state=2` 全部 `image_url` null，**该单字段零反例**。
  但跨应用 `state=1` 存在 `image_url` 非 null 而 schema/sql null 的行（同上 1.0.7），故四字段组合仍保留作排除用。

**用法**：`state=1` 且四字段任一非 null ⇒ 成功（强）；`state=2` 且 `image_url IS NULL` ⇒ 失败（本应用内零反例）；
四字段全 null + `state=2` ⇒ 失败且产物全未产出（最强失败形态，本次 1.0.15 即此形态）。

**判据 S2｜运行态版本身份（sha256[:16] 对齐，auditor 判据，采纳引用）**

运行态当前服务的版本 = `remoteEntry.js` 内容 sha256 前 16 位与
`remoteEntry.{build_version}` 快照逐一比对，**等值者即运行版本**。

auditor 独立取证（`AUD-SET-PUB-1-runtime-version-identity.json`，01:53:23）：
`current_remoteEntry.sha = c830f751b7ad1f76` ≡ 快照 `20261015192931`(1.0.14, 200, 23858B)
；`20261018014139`(1.0.15) / `20261017234259` / `20261017225602` 全 404。
⇒ **运行态仍服务 1.0.14，本次发布（1.0.15）产物未上线，决定性对齐**。

两判据与 §5.2 的 OSS 404 对照、§4.2 的 `image_url` 表互相独立，四面闭合同一结论。

**枚举不一致登记（~~SET-PUB-D2~~ → 已按 DISCREPANCY-4 作废，02:30）**：
原登记「`SETTINGS-TABS-CALLCHAIN.md` 附录记 `FAILED`，实测返回 `FAIL`」——经 main 复扫
auditor live.jsonl 与 implementer 全部 7 件抓包（0 命中 `"FAIL"`），**该实测无原始帧支撑**，
属于 §3 同一誊写失真。附录 `FAILED` 维持原文不动，终态枚举待后续 LIVE 窗口补抓终态帧再定（UNVERIFIED）。

---

## 7. 证据文件

| 文件 | 内容 |
|---|---|
| `implementer/evidence/SET-PUB-1-netcapture-step1-test-click.json` | 点「测试」：2 条 /service（expect-deploy-time + latest-test-info），含完整 req/resp |
| `implementer/evidence/SET-PUB-1-netcapture-step2-deploy-click.json` | 点「立即构建」：**6 条 /service**，含 `udcRuntimeDeployNormalPost` 完整回包 |
| `implementer/evidence/SET-PUB-1-netcapture-auth-access-url.json` | auth-access-url 探测（内容为 portal user-info，未产生有效 auth url） |
| `implementer/evidence/SET-PUB-1-runtime-asset-probe.json` | §5.2 五个 OSS/SPA 产物探测原始结果 |
| `implementer/evidence/SET-PUB-1-baseline-db.json` | （auditor 独立基线，引用） |

---

## 8. 未闭环项（如实登记，不扩范围）

| 项 | 状态 | 缺什么 |
|---|---|---|
| 第③项 新版本资源可访问 | **BLOCKED** | 应用侧修复 `XzhExp950795` 生成缺陷（`Long.parseLong(实体全名)`） |
| 失败发布仍刷 120 行 resource（version→20） | **UNVERIFIED** | 120 行的选择规则（变更集 / 全量分页 / 分组）未定位；不影响本切片 PASS② |
| `udcRuntimeAuthAccessUrlPost` | **UNVERIFIED** | 实测 `content{pcHomeUrl:null, mobileHomeUrl:null}`，未返回可用 URL；该 op 的真实用途需再证 |
| 构建态终态枚举（`FAIL` vs `FAILED`） | **UNVERIFIED**（SET-PUB-D2 已作废） | 无终态原始帧落盘；需后续 LIVE 窗口补抓 `udcSandboxBuildInfoAppGet` 终态帧。附录 `FAILED` 维持原样 |
| `XzhExp950795` 实体级根因 | 域外 | 属实体域；本组不碰（不跨组） |

---

## 9. 复现命令

```bash
# 1) 注入登录态（cookie 只在进程内使用，不落盘）
python "<HERMES_HOME>/cache/scratch/c1_inject2.py"

# 2) 页面点击「测试」并抓包
python "<HERMES_HOME>/cache/scratch/c1_step1.py"

# 3) 等 ≥30s 后点「立即构建」并抓包
python "<HERMES_HOME>/cache/scratch/c1_step2.py"

# 4) DB 回读（deploy_record / app_version / resource）
python "<HERMES_HOME>/cache/scratch/c1_db1.py"   # deploy_id 维度
python "<HERMES_HOME>/cache/scratch/c1_db3b.py"  # resource 变更集
python "<HERMES_HOME>/cache/scratch/c1_db4.py"   # 成功样本对照

# 5) 产物面探测（新旧 build 对照）
python "<HERMES_HOME>/cache/scratch/c1_final_assets.py"
```

---

## 10. 给 main 的一句话

**链路机制已全部 LIVE 打通（publish 回包 + 三表落库 + 产物对照判据），
唯一阻塞是应用自身 `XzhExp950795` 实体代码生成 `NumberFormatException`，属实体域、不在本组范围。
按 PROGRESS #C-01a 口径：切片判 BLOCKED，建议切 ROLE-S5 主线，不等待修复。**
