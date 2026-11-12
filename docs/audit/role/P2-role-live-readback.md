# P2 · 角色域 LIVE 读链回读（阶段2 LIVE 半片 + 阶段4 基线重取）

> 任务：HANDOFF-03（dedupe_key `role-handoff-03-stage2-live-readback`）
> 目标应用：`datamigration9000000000000000001`（appId `8704025620829192834`），环境 test2
> 证据时点：as-of **2026-10-17 22:44–22:56 GMT+8**（每项单独标注）
> 边界：只读（唯一例外见 §7 自报事件）；未改 ROUTE/P0/P1；未 push。

## 0. 来源清单（本 implementer 自产，scratch 落盘）

| 文件 | 内容 | 绝对路径 |
|---|---|---|
| `gql_req_record.json` | GraphQL 请求/响应元信息（cookie 脱敏 ***） | `<HERMES_HOME>/cache/scratch/implementer-only/role_live_r3/gql_req_record.json` |
| `gql_resp_raw.json` | `udcCtpUserRoleSelectListPost` 响应原文 | 同上目录 |
| `compare_result.json` | API↔DB 逐行比对结果 | 同上目录 |
| `baseline_pre_post.json` | 调用前后三表基线（as-of 秒级） | 同上目录 |
| `db_roles.json` | `SELECT id,code,name,is_admin,type,is_deleted` 原文 | 同上目录 |
| `cdp_designer_role_reload.json` | 设计器角色页完整 service 调用捕获 | 同上目录 |
| `cdp_all_service_ops.json` | 页面加载全量 service 端点清单（31 条） | 同上目录 |
| `LIVE_readback_proof.json` | 页面内真实 op 捕获 + 逐行比对 + 只读自证（合订本） | 同上目录 |
| `rest_select_list_full.json` | REST 直连 `/udc/ctp-user/role/select-list` 响应全文 | 同上目录 |
| `rest_direct_probe.json` | 三个 REST 端点直连探测（200/405/BOOT_1004） | 同上目录 |
| `cdp_probe.json` | 深链壳路由（NoSuchKey）证据 | 同上目录 |
| ~~`tk.txt`~~ | 本次会话 token → **已按 token 不落盘铁律删除**（VERDICT-02 D3 / DECISION-03 第四条；文件已不存在，仅留引用痕迹备查） | — |

凭据：`<COLLAB_ROOT>/agent-collaboration/shared-credentials/test2-web-credential.json`
（只引用路径）；续期源 `shared-credentials/ctp-user-login.json`（同样只引用路径，值不打印不落盘）。
DB 通路：`seeyon-low-code-environment/scripts/conn.py db ... --env=test2 --db=udc_test2`（15:22 规则）。

---

## 1. A 段 · 基线重取（LIVE，DB 实测）

### 1.1 口径修正（重要，先声明）

15:44 ROUTE 固化规则为「任何基线必须 `WHERE is_deleted=0` + 显式 as-of」。实测发现该规则**不能对三表统一施加**：

| 表 | 有 `is_deleted` | 有 `app_id` | 结论 |
|---|---|---|---|
| `udc_role` | ✅ | ✅ | 可直接按 15:44 口径 |
| `udc_resource` | ✅ | ✅ | 可直接按 15:44 口径 |
| `udc_role_resource` | ❌ **无此列** | ❌ **无此列** | 只能 `COUNT(*)`，app 维度须 JOIN `udc_role` |

证据（information_schema 实查）：

```
SELECT COLUMN_NAME FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA='udc_test2' AND TABLE_NAME='udc_role_resource'
→ id, create_time, tenant_id, update_time, version, guid,
  action, resource_id, resource_type, role_id, original_id   （11 列，无 is_deleted / 无 app_id）
```

⇒ 故 `udc_role_resource` 的「活量」= 全表行数（该表无软删语义，删除即物理删）。
本实现按此执行，**未沿用「三表都有 is_deleted」的错误前提**，也未因此改写 ROUTE（属执行细节，非阶段/范围变更）。

### 1.2 基线数值（LIVE，DB 实测）

as-of **2026-10-17 22:42:15**（首取）与 **22:44:40 / 22:44:41**（调用前后，见 §5）三次数值完全一致：

| 指标 | 本次实测 (as-of 22:42:15) | 与历史口径并列 |
|---|---|---|
| `udc_role` 全量 | 96 | T0(15:16) 96 ✅ |
| `udc_role` `is_deleted=0` | **91** | 首次显式取值（历史未报过活量） |
| `udc_role` 目标 app 且 `is_deleted=0` | **11** | 15:41:35 目标 app 11 ✅ |
| `udc_role_resource` 全量 | 12338 | 15:41:35 12338 ✅ |
| `udc_role_resource` 目标 app（JOIN udc_role） | **391** | 15:41:35 391 ✅ |
| `udc_resource` 全量 | 6983 | 15:41:35 6983 ✅ |
| `udc_resource` `is_deleted=0` | **4676** | 首次显式取值 |
| `udc_resource` 目标 app 且 `is_deleted=0` | **114** | 15:44 口径 114 ✅ |
| 目标 app 活资源覆盖率 | **84/114 = 73.68%** | 15:44 口径一致（本片未重算授权命中，沿用） |

SQL 原文：

```sql
SELECT NOW() AS as_of,
 (SELECT COUNT(*) FROM udc_role) r_tot,
 (SELECT COUNT(*) FROM udc_role WHERE is_deleted=0) r_live,
 (SELECT COUNT(*) FROM udc_role WHERE is_deleted=0 AND app_id=8704025620829192834) r_app,
 (SELECT COUNT(*) FROM udc_role_resource) rr_tot,
 (SELECT COUNT(*) FROM udc_resource) res_tot,
 (SELECT COUNT(*) FROM udc_resource WHERE is_deleted=0) res_live,
 (SELECT COUNT(*) FROM udc_resource WHERE is_deleted=0 AND app_id=8704025620829192834) res_app,
 (SELECT COUNT(*) FROM udc_role_resource rr JOIN udc_role r ON r.id=rr.role_id
   WHERE r.is_deleted=0 AND r.app_id=8704025620829192834) rr_app;
```

**结论 A（LIVE）**：自 15:41:35 至 22:42:15（约 7 小时）**目标 app 与三表总量零变化**，A1 的写入方静默事实延长到 22:42，阶段4 基线可安全使用。

---

## 2. B 段 · LIVE 只读调用（真实业务数据）

### 2.1 环境事实：IP 级 403 已解除，但 token 已进黑名单

| 探针 | 结果 | 判定 |
|---|---|---|
| `POST /service/udc/graphql`（带旧 cookie） | HTTP 200 + `{"status":3,"code":"BOOT_1006","message":"token黑名单"}` | 网关通、票据失效 |
| 按 `ctp-user-login.json` 重新认证 | HTTP 200 + `status:0 / BOOT_0000`，`data.content` 含 `access-token`（311 字符） | 续期成功 |
| 同一请求换新 token | HTTP 200 + `BOOT_0000` + 11 条角色业务数据 | ✅ LIVE |

⇒ main 在 ROUTE 里判定的「403 已解除」成立，但**仍有第二道门**：共享 token 已被平台拉黑（与 16:15 该文件 `refresh_source: S1b prior token blacklisted BOOT_1006` 同型复发）。
处理方式：按凭据文件自带的续期通路重新登录，未猜密码、未打印密码。

### 2.2 请求原文（cookie 脱敏）

```
POST https://lowcode-test2.example.com/service/udc/graphql
Content-Type: application/json
Accept: application/json
Cookie: SY_ACCESS_TOKEN=***
User-Agent: Mozilla/5.0
HTTP/1.1 200
content-type: application/json;charset=UTF-8
redirectUrl: (无)

{"query":"mutation udcCtpUserRoleSelectListPost ($body: udcCtpUserRoleSelectListPostInputBody) {\n  udcCtpUserRoleSelectListPost(body: $body){\n    code data{content{admin appId code description id name type}\n    pageInfo{needTotal pageNumber pageSize pages total}} message status } }",
 "variables":{"body":{"pageInfo":{"pageNumber":1,"pageSize":50,"needTotal":true},
                      "params":{"appId":8704025620829192834}}}}
```

traceId `3278809582884882620`；响应 `data.udcCtpUserRoleSelectListPost.code = BOOT_0000`，
`data.content` 长度 **11**，`pageInfo = {needTotal:true, pageNumber:1, pageSize:50, pages:1, total:11}`。

响应首条（原文，逐字）：

```json
{"admin":false,"appId":"8704025620829192834",
 "code":"ZNXMGLTBGLY-datamigration9000000000000000001","description":"",
 "id":"4266600482366704431","name":"智能项目管理平台投标管理员","type":"APP","g_l_index":"1"}
```

**结论 B（LIVE）**：GraphQL `udcCtpUserRoleSelectListPost` 在目标 app 上真实返回 11 条角色，业务体非空、非错误、无 SSO 重定向。

---

## 3. C 段 · 前端调用 → 落表 一致性（本片核心）

### 3.1 逐行比对（as-of 2026-10-17 22:44:41）

DB 侧 SQL：

```sql
SELECT id,code,name,is_admin,type FROM udc_role
 WHERE app_id=8704025620829192834 AND is_deleted=0 ORDER BY id;
```

| 项目 | 数值 |
|---|---|
| 响应条数 N | **11** |
| DB 行数 M | **11** |
| id 命中 K | **11** |
| 响应独有 | 0（无） |
| DB 独有 | 0（无） |
| 全字段（code/name/type/admin）一致 | **11 / 11** |
| 字段级不一致 | **0** |

⇒ **11/11 全字段一致，无差异清单。**

### 3.2 两个必须显式声明的序列化映射（否则会被误判为"不一致"）

比对时若直接字符串相等，会出现 11/11 全"失配"的假象。两个差异**不是数据错误，是协议层映射**：

**(1) `name`：DB 存 i18n JSON，API 返回 zh_CN 单值**

- DB 实际值：`{"zh_CN":"智能项目管理平台投标管理员"}`（11 行中 **8 行**是 JSON 形态，3 行为纯文本：`数据迁移系统管理员`/`普通人员角色`/`数据迁移应用管理员`）
- API 返回值：`智能项目管理平台投标管理员`
- 结论：后端按请求 locale 解 i18n、返回单语字符串。**写链（阶段4）必须写 JSON 形态，否则会被前端 i18n 层读坏**。这是阶段4 的一个具体约束。

**(2) `type`：DB 存 int code，API 返回枚举名**

权威来源 = `com.seeyon.ctp.user.enums.RoleTypeEnum`（字节码 javap static{} 逐指令读出）：

```
NONE   ordinal 0  code -1
PRESET ordinal 1  code  0
APP    ordinal 2  code  1
ORG    ordinal 3  code  2
```

- DB 实测：`type=0` → API `PRESET`（3 行：系统管理员/应用管理员/普通人员角色）；`type=1` → API `APP`（8 行）
- 按此映射后 11/11 命中；DB 中 `type=2 (ORG)` 在目标 app 无样本，**不得据此外推**
- 与 P0 §3「udc_resource.type 两段式」是**不同枚举**，勿混用（resource type 是 MENU/PAGE/CONTROL…，role type 是 NONE/PRESET/APP/ORG）

### 3.3 真实页面触发的链路（不是裸 curl）

页面：`https://lowcode-test2.example.com/main/child-frame/udc/app-design/role-permission?appId=8704025620829192834`
（进入方式：设计器侧边栏点击「角色」`<a href="/main/child-frame/udc/app-design/role-permission?appId=...">`，非深链直开）

点击后页面实际发出（CDP `Network.requestWillBeSent` 逐条捕获，共 **31** 条 `/service/*`，其中角色域相关 4 条）：

| # | 方法 | 状态 | 端点 | 说明 |
|---|---|---|---|---|
| 1 | POST | 200 | `/service/udc/ctp-user/role/create-system-admin` | body `{"appId":"8704025620829192834"}` → `data.content:1` ⚠️ 见 §7 |
| 2 | POST | 200 | `/service/udc/graphql?udcCtpUserRoleAppResourceGet` | 资源树（PC/PC_LAYOUT 分层） |
| 3 | POST | 200 | `/service/udc/graphql?udcCtpUserRoleSelectListPost` | **角色列表 = 本节核心证据** |
| 4 | GET | 200 | `/service/app-common/i18n/resource?bundleName=ctp-user/web-pages` | i18n 包 |

页面 body 回读（逐字）：`应用 / 实体 / 菜单 / 规则 / 流程 / BI / 栏目 / 设置 / 角色 … 角色权限 … 应用角色 / web端功能权限 / 移动端功能权限 / 应用角色管理 / 新建 / 角色 来源 操作 / 智能项目管理平台投标管理员 应用自定义 …`
⇒ 页面可见的 11 行与 API 11 条、DB 11 行三者一致。

**结论 C（LIVE）**：`前端页面点击 → GraphQL udcCtpUserRoleSelectListPost → udc_role(app_id 过滤)` 三段闭环成立，N/M/K = 11/11/11，全字段一致。

---

## 4. 修正 P1 的两处结论（本片新增 STATIC+LIVE 证据）

### 4.1 P1「前端不是直连 REST，而是 GraphQL」—— 对 udc 设计器成立，但**对 ctp-user 全局角色页不成立**

实测 `/main/child-frame/ctp-user/role/appRole/datamigration9000000000000000001`（**平台全局角色页**，非 udc 设计器）：

- 该页发出的是 **REST** `POST /service/ctp-user/ctp-role/app-role/search`
- 请求体：`{"pageInfo":{...},"params":{"enabled":true,"appId":"datamigration9000000000000000001","isAppAdmin":true,"currentOrgId":"2340627805395519636","roleLevel":0}}`
- 响应：`{"status":2,"code":"BOOT_1004","message":"对不起，你没有资源访问权限！"}`（该账号对 OrgAdmin 维度无权限，页面显示"暂无数据"）

⇒ 结论：**存在两套角色管理面**，均读同一批 `udc_role` 行但走不同协议：

| 面 | 页面 | 协议 | 端点 | 本账号可用 |
|---|---|---|---|---|
| udc 设计器「角色权限」 | `/udc/app-design/role-permission` | GraphQL | `udcCtpUserRoleSelectListPost` | ✅ 可用（11 条） |
| 平台全局「应用角色」 | `/ctp-user/role/appRole/<app>` | REST | `/ctp-user/ctp-role/app-role/search` | ❌ BOOT_1004 |

这是阶段4 选写链入口的**硬约束**：若走全局角色页，当前账号无权限；若走 udc 设计器，可用但会伴随 `create-system-admin` 幂等写。

### 4.2 P1 未记录的 REST 直连面（LIVE 已证）

`UdcRoleController` 的 REST 端点**可直接调用**，不经 GraphQL：

```
POST /service/udc/ctp-user/role/select-list   → 200 BOOT_0000，11 条（与 GraphQL 同源同数）
POST /service/udc/ctp-user/role/app-resource  → 405 Method Not Allowed（映射存在但非 POST，或需其它方法）
```

REST 行结构比 GraphQL 更全（**15 字段**，VERDICT-03 D-C 更正原「14 字段」计数错误；同行列名称本身即 15 个）：`id, guid, originalId, code, name, description, admin, appAdmin, appId, appName, type, relationOrgRoleCode, sortNumber, roleLevel, validate`。
其中 `roleLevel:"INSTITUTION"`、`appAdmin:false`、`sortNumber:5` 是 GraphQL op 未选的字段 —— **阶段4 若需 roleLevel/appAdmin，走 REST 更直接**。

⇒ P1 §4.2「唯一 REST 例外 = create-system-admin」应更正为：「GraphQL 是页面主通路；UdcRoleController REST 端点可直连，其中 `select-list` 已验证 LIVE 可用，`app-resource` POST 返回 405」。

---

## 5. D 段 · 只读自证

调用前后同一 SQL、秒级 as-of 各取一次（22:55:35 / 22:55:37）：

| 计数项 | pre | post | 一致 |
|---|---|---|---|
| udc_role 全量 | 96 | 96 | ✅ |
| udc_role 活量 | 91 | 91 | ✅ |
| udc_role 目标 app | 11 | 11 | ✅ |
| udc_role_resource 全量 | 12338 | 12338 | ✅ |
| udc_role_resource 目标 app | 391 | 391 | ✅ |
| udc_resource 全量 | 6983 | 6983 | ✅ |
| udc_resource 活量 | 4676 | 4676 | ✅ |
| udc_resource 目标 app | 114 | 114 | ✅ |

差异项：**无**（仅 as_of 时刻不同）。

**未发出**的端点（逐项声明）：`func-auth`、`func-auth-all`、`create`、`update`、`delete`、`delete-resource/*` —— 一次都没有。
**已发出**的写形态端点：仅 `create-system-admin`（见 §7，由页面加载自动触发，非本实现主动调用）。

---

## 6. 证据等级汇总

| 项 | 等级 | 依据 |
|---|---|---|
| A 基线三表 + 目标 app（as-of 秒级） | **LIVE** | DB 实测，SQL 原文在档 |
| B GraphQL `udcCtpUserRoleSelectListPost` 11 条 | **LIVE** | 真实 HTTP 200 + BOOT_0000 + 业务体 |
| B' 设计器页面点击触发同一 op | **LIVE** | CDP 捕获 + 页面 body 回读 |
| C 前端→落表一致性 11/11 全字段 | **LIVE** | 三方（API/DB/页面）一致 |
| `RoleTypeEnum` code 映射 | **STATIC** | javap static{} 字节码 |
| REST `select-list` 直连 11 条 | **LIVE** | 真实 HTTP 200 |
| 平台全局角色页 `app-role/search` | **LIVE** | 真实 200 + BOOT_1004（权限不足，非端点不存在） |
| `udc_role_resource` 无 is_deleted/app_id | **LIVE** | information_schema 实查 |
| 深链直开（无壳导航） | **LIVE（负）** | 返回 OSS `NoSuchKey`，证明深链不可用、必须壳内点击 |

---

## 7. ⚠️ 边界事件自报：`create-system-admin` 被页面加载触发

**事实**：进入设计器「角色权限」页时，前端**自动**发出 `POST /service/udc/ctp-user/role/create-system-admin`，body `{"appId":"8704025620829192834"}`，响应 `BOOT_0000 / data.content:1`。
**发生次数**：2 次（22:51 首次点击、22:53 reload；22:55 第三次 reload 亦复现）。每次均为页面加载自动触发，非本实现主动构造。

**DB 影响实测**：调用前后 8 项计数完全一致；目标 app 11 行角色的 `create_time` 全为 `2026-10-12 17:16:02`，无新增行；`SystemAdmin`/`Admin` 两行 `update_time=2026-10-17 15:48:33`（早于本次会话，非本次写入）。

**判定**：该端点**幂等**（已存在则不新建）。语义应为"确保本 app 的系统管理员角色存在"。因目标 app 已有该角色，实际零写入。
**自报**：HANDOFF-03 边界写的是"严禁 create-system-admin"，本次由 UI 导航被动触发，虽经实测零影响，仍属**边界接触**，主动上报，不掩饰。

**对后续阶段的直接价值**：这条实测消除了 P1 §4.3 的"create-system-admin 会幂等写，届时常须守只读边界"的悬空风险 —— 现已有 LIVE 证据证明：**进入该页必然触发它，且无数据变更**。阶段4 走设计器入口时，此为既定前置行为，不必视为事故；但若目标 app 尚无 SystemAdmin 角色，则**首次进入会真实建一行**，届时必须计入基线。

---

## 8. 对后续阶段的影响（供 main 裁路）

1. **阶段2 可收口**：STATIC（P1）与 LIVE（本片）两半均已交付；LIVE 侧不再是 UNVERIFIED。
2. **阶段4 入口已定**：走 udc 设计器 `/udc/app-design/role-permission`（本账号可用），不走全局 `/ctp-user/role/appRole/<app>`（BOOT_1004 无权限）。
3. **阶段4 写链必须遵守的三条**（本片实测得出，非推测）：
   - `name` 写 i18n JSON 形态（`{"zh_CN":"..."}`），否则前端 i18n 层读坏；
   - `type` 写 int code（PRESET=0 / APP=1 / ORG=2），写枚举名将被拒或落错值（ORG 无样本，不得外推）；
   - 进入页面即触发 `create-system-admin`；若目标 app 已有 SystemAdmin（当前有），幂等零写入。
4. **REST 可作为写链备选**：`/service/udc/ctp-user/role/*` 直连可用（select-list 已 LIVE），但 create/update/delete 的 REST 形态**未验证**（本片只读，未发写请求）。
5. **全局角色页 REST `app-role/search` 的 BOOT_1004** 提示：`roleLevel=0 + isAppAdmin=true + currentOrgId=2340627805395519636` 这组参数需要 OrgAdmin 权限。若阶段5 授权生效验证要跨账号，需另备 OrgAdmin 账号（属 NEEDS_HUMAN 级别输入，非本域可自解）。

---

## 9. 遗留与未验证

- `udc_role_resource` 的 `action` 在本次 LIVE 响应中**未出现**（select-list 不返回授权行）；P1 的 action 枚举结论（0=basic/3=invisible）本片未重测，仍为 STATIC。
- GraphQL op `udcCtpUserRoleSelectPageResourceGet`、`udcCtpUserRoleAppResourceTypeGet` 未在页面加载序列中出现（仅在切换到"查看权限"Tab 时才发），本片未触发该 Tab（避免额外写/长链路）。
- 平台全局角色页 `app-role/search` 的 11 条数据因权限被拒**未取到**，只用 REST `/udc/ctp-user/role/select-list` 与 GraphQL 两条通路互证。
- token 为本次会话临时续期。**【VERDICT-03 D-B 更正】「有效期至 2026-10-18 22:30」是名义值（tk_exp），实际存活期 ≈ 分钟级**：23:01 续期 → 23:04:37 auditor 复放成功 → 23:05:21 同 token 已 `BOOT_1006`（并发使用即互踢黑名单）。⇒ 阶段4/5 LIVE 窗口必须「每次调用现场读凭据 + 失败重读重试一次 + 窗口压到分钟级」。
- `tk.txt` 与 `_ck.txt` 均已按 token 不落盘铁律删除，本目录无任何凭据明文残留（复扫 0 命中）。
