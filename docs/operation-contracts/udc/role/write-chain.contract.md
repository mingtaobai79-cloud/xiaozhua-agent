# 角色域 契约（15 端点 + 写链语义）

> 子域：`role`（角色 / 资源授权 / 功能权限）
> 目标应用：`datamigration9000000000000000001`（appId `9000000000000000002`），环境 test2
> 后端：`udc-user` 5.3.517 · `UdcRoleController`（15 端点）+ 前端 `ctp-user` bundle
> 本文件性质：**纯整理**。零新调用、零页面、零 DB 写、零登录。所有等级照抄审计件，不升格。
> 编制日期：2026-10-18

---

## 0. 先说三件最容易出错的事（读别的之前先读这段）

### 0.1 `func-auth` 是**覆盖式**，不是追加

`udcCtpUserRoleFuncAuthPost`（#13）= **设置该角色的完整授权集：按 roleId 全删全建**。

```
若该角色原有 N 条授权，调一次传 1 条 → 结果 N → 1（不是 N+1）
```

响应里的 `content:N` 是**写入后的总条数**，不是本次增量。
⇒ **用它试写会毁掉该角色的既有授权。** 生产上必须：先 `role-auth`(#11) 读出全量 → 改 → 整包写回。

**依据要分清两件事，不可混写：**
- **机制（覆盖式 / 全删全建）= LIVE 实测**：S5 §2 四次写，`content:1/1/1/2`，
  且物理 id 全换 + delta 提交把存量抹除 —— 这是硬证。
- **「47 → 1」= 推算，不是实测**：47 是 `ContractAdmin` 的现有授权数（S5 L183 分布表），
  P3 §10.2 / §11.3 的「47→1」是**假设句**（"若提交 delta"）的算术推演，用于解释
  「为什么探针 +1 无损不能证明增量式」。**本轮从未对 47 条的角色做过实测。**
- 本域四次实测的载体是 `quanxian-...`（**基线 1 条**），所以实测序列是 `1→1 / 1→1 / 1→1 / 1→2`。

### 0.2 `role-auth-all` 的 `code` 参数是资源 code；返回范围依调用参数/应用情境区分（证据不可泛化）

`udcCtpUserRoleRoleAuthAllPost`（#12）支持 `appId` 与可选资源 `code`。**不同样本曾观察到不同返回行为，必须按调用实证判定，不得把 P3 单次样本外推为“省略 code 必空”，也不得把 2026-10-19 单应用样本外推成所有应用恒定全量。**

| 实测情境 | 入参 | 实测结果 | 证据边界 |
|---|---|---|---|
| P3 历史样本 | `{appId}` | 记录为 11 角色且 `resourceList` 为空；历史解释为 `admin=false` 过滤导致匹配集为空 | 仅适用于 P3 当时应用/数据/身份条件；不能视为通用规则 |
| P3 历史样本 | `{appId, code:"2084600749018399891"}` | 11 角色 / 289 行 | 历史样本，不可推断所有 code/应用 |
| P3 历史样本 | `{appId, code:"9183843213439484192"}` | 11 角色 / 21 行 | 历史样本，资源子树过滤 |
| test2 应用 `9000000000000000002`（2026-10-19） | `{appId}`，无 `code` | 11 角色；各角色 `resourceList` 非空，共 413 项；目标角色 45 项，与该角色 `udc_role_resource` 45 行一致 | LIVE 证据见 #12 行；只证明该次调用上下文 |

**操作规则：**读取实际 response、明确当前 app/身份和数据上下文，再选择判据；省略 `code` 时绝不能仅凭空数组判“无授权”，也不能不验证就假定得到完整授权总览。需要过滤资源子树时传真实资源 `code`；参数值不得按 appId 或角色 id 代用。

P3 原“409 条与 DB 互证”结论已撤回：参数/聚合口径不成立；跨角色 `resourceList` 求和不是全局权限总数。
### 0.3 权限面板 31/31 复选框 disabled 不是「只读」，是「查看模式」

`test-account-1` 无 OrgAdmin 维度 ⇒ 进入权限面板时所有复选框 disabled。
**这是查看态，不是接口无权限**，不要据此判「该角色不能改权限」。
（依据：P1-GAP / P3 现场观察）

### 0.4 ⚠️ 进入「角色权限」页会**自动触发** `create-system-admin`（#15），这是必然行为

**不是 bug，是页面加载的固有动作**（P2 §7 实测 3 次：22:51 首点 / 22:53 reload / 22:55 reload）。

```
POST /service/udc/ctp-user/role/create-system-admin
body {"appId":"9000000000000000002"}
→ BOOT_0000 / data.content:1
```

**两种情况，后果完全不同：**

| 场景 | 实测行为 | 危险度 |
|---|---|---|
| 目标 app **已有** SystemAdmin 角色 | **幂等，零写入**（调用前后 8 项 DB 计数完全一致、11 行 `create_time` 未变） | 安全 |
| 目标 app **尚无** SystemAdmin 角色 | **首次进入会真实建一行** | ⚠️ **会改变基线** |

⇒ **执行纪律（写死，任何阶段 4 动作前必读）**：
1. **前置强制检查**：任何阶段 4 动作（进角色页/建角色/绑授权）之前，**必须先查该 app 是否已有 SystemAdmin 角色**：
   ```sql
   -- code 模板 = <appName>SystemAdmin（P0 §8 已证），必须用等号，不能用 LIKE
   SELECT COUNT(*) FROM udc_role
   WHERE app_id='9000000000000000002'
     AND code='datamigration9000000000000000002SystemAdmin';
   -- 0 = 尚无（进页面会真建一行，先计入基线）；1 = 已有（幂等零写入）；≥2 = 异常，先查重
   ```
   > ⚠️ **为什么必须用等号而不是 `LIKE '%SystemAdmin%'`**：全库有多个 app 的 code 含该串
   > （`xiangmuguanli…AdminSystemAdmin`、`faccountsreceivable…EnBSystemAdmin` 等，P0 §8 L269-270）。
   > 用 LIKE 会在「目标 app 其实没有」时返回 >0 ⇒ **判成「已存在」⇒ 你以为安全 ⇒ 进页面真的建了一行**。
   > 这是**假阳性导致的漏警告**，比假阴性更危险：它让人以为安全。
   > 等号还顺带能发现重名（返回 ≥2 就是异常）。

   已存在 → 本次触发零写入，可正常继续。
   **尚无 → 首次进入会真实建一行，必须先把这一行计入基线与审计记录**，再谈后续动作。
2. 该行为**无法通过「不点按钮」避免** —— 只要页面加载就会发，属页面固有动作。
3. 本契约把它列为 DANGER-ZONE，但**不是「禁用端点」**，而是「**不可控被动触发**」：
   你没法选择不调它，只能选择调之前知道后果。

（依据：P2 §7，含 3 次调用原文 + 8 项 DB 计数 + create_time 全量核对）

---

## 通用约定

| 项 | 值 |
|---|---|
| 网关前缀 | `/service/` |
| 类级基路径 | **`udc/ctp-user/role`**（`UdcRoleController` 类级 `RequestMapping` `value=["udc/ctp-user/role"]`，javap 实读）⚠️ **不是 `udc/role`** |
| 两种入口 | ①**GraphQL 包装层**（页面实际走这个）：`POST /service/udc/graphql?<opName>`；②REST 直连：`POST/GET /service/udc/ctp-user/role/<path>` |
| GraphQL op 命名 | `udcCtpUserRole<Method>Post`（mutation）/ `udcCtpUserRole<X>Get`（query），见 §4 |
| 成功码 | `code:"BOOT_0000"` + `status:0` + `message:"SUCCESS"` |
| traceId | 响应顶层 `traceId`，每次必返 |
| 长整型 | id/guid 是 **bigint 字符串**（`"7848047731790858930"`），**不要当 number 处理**，会精度丢失 |
| 凭据 | 仅引用 `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json`，不打印不落盘 |

### 证据等级定义（严格口径，不得升格）

| 等级 | 含义 |
|---|---|
| **LIVE** | 有真实调用 + 请求/响应原文（或 DB 回读 / 操作日志），**且是接口级** |
| **STATIC** | 仅 `javap -v -p` 读出注解/签名/返回类型，无真实调用回包 |
| **STATIC+UI** | 界面交互验过字段，但**接口层无回包** ⇒ 按严格口径仍算 STATIC |
| **UNVERIFIED** | 无任何证据，或证据不足以判定 |
| **VACUUM** | 已确认域内 0 条可证据化契约（完备负证据） |

> ⚠️ 判 LIVE 的四条排除（P1-GAP L26-27）：①只有 HTTP 200 没 body ②只有 BOOT_0000 没 DB 变化
> ③从别的端点推断「应该也一样」 ④抄契约文档自身。**缺一即不算 LIVE。**

### 全局等级总表（15 端点）

> **【15 这个数怎么复算】** —— 不是凭记忆，仓内一条命令即可验，且我实跑过：
> ⚠️ **前置：必须用 JDK 21 的 javap 产物**。用 JDK 8 的 javap 重新生成，`annotation.(Post|Get)Mapping(` 会得 **0**
> （JDK 8 不展开注解类名），详见 §14.1 的版本对照表。
> ```
> cd docs/audit/artifacts/udc-user-5.3.517-contracts
> F=UdcRoleController.javap.txt
> grep -cE 'annotation\.(Post|Get)Mapping\(' "$F"        # → 15（方法级）
> grep -cE 'annotation\.RequestMapping\('    "$F"        # → 1 （类级，别混入）
> ```
> **双向完备性**（比只数总数更硬，实测）：
> ```
> grep -oE 'value=\["[^"]*"\]' "$F" | wc -l              # → 16
> grep -oE 'value=\["[^"]*"\]' "$F" | sort | uniq -c     # → 15 个各 1 次 + 1 个 "udc/ctp-user/role"
> ```
> 16 = **1 个类级基路径（`udc/ctp-user/role`）+ 15 个方法级路径**，且**每个方法路径各出现 1 次**
> ⇒ 本表 15 行与 javap 里 15 个方法路径**一一对应，无重复、无遗漏**。
>
> ✅ **产物已入仓**，上面命令可直接跑。想验「这份 javap 确实来自这个 class」见 §14.1 第 ② 条。

| # | 方法 | 端点 | 性质 | 等级 | 依据 |
|---|---|---|---|---|---|
| 1 | create | `POST create` | 写 | **LIVE** | ROLE-W1/ROLE-W2 页面点击 + traceId + DB 精确行 + 页面 data-row-key 三方匹配；见 `implementer/evidence/ROLE-W1-create.json`、`ROLE-W2-fixture-create.json`（后者 id 手工修正且已披露，auditor 独立核验） |
| 2 | update | `POST update` | 写 | **LIVE** | ROLE-W2 页面编辑 description；traceId `17924202530788394426`；同 id DB description/update_time/version 前后回读 + 列表响应/重开弹窗可见；见 `implementer/evidence/ROLE-W2-update.json` |
| 3 | delete | `POST delete` | 写 | **LIVE（软删除）** | ROLE-W1/W2 页面删除；traceIds `17924195434148082526` / `17924208495826615711`；DB `is_deleted 0→1` + 刷新后列表/API 排除；见对应 delete evidence。物理行保留属预期，不做 purge |
| 4 | deleteByAppId | `POST delete-resource/app/{appId}` | 写·**高危** | **STATIC** | 未调用，**DANGER-ZONE** |
| 5 | deleteById | `POST delete-resource/{id}` | 写 | **STATIC** | 未调用，**DANGER-ZONE（低）** |
| 6 | selectById | `GET {id}`（语义 query；**实测传输 POST**） | 读 | **UNVERIFIED**（DOM 已补，待 main/auditor 裁定） | ROLE-R1 真实点击「编辑」→ `udcCtpUserRoleGet`，traceId 17923986229273699334，387B，content.code/name 与列表首行一致，弹窗「编辑角色」可映射（implementer/evidence/ROLE-R1-selectById.json） ｜补证：`evidence/ROLE-R1-selectById-dom.json`（modal value↔resp 逐字一致；requestId 38484.1347；新 traceId 17923991918141651750 与旧件 body 去 traceId 后逐字节一致）|
| 7 | selectRoleList | `POST select-list` | 读 | **LIVE** | P2 7 处引用 + S5 基线侦察（有回包原文） |
| 8 | selectResourceByApp | `GET app-resource` | 读 | **LIVE** | P2 2 处（有回包原文） |
| 9 | selectPageResource | `GET select/page-resource` | 读 | **STATIC**（UNVERIFIED） | 与 #8 同资源树另一切面，#8 已 LIVE，但本端点自身无回包。ROLE-R1（2026-10-19）三次真实交互（查看权限/ web端功能权限 / 重载）均未触发；bundle `ctp-user/bussiness.8e39da83.js` 有 `fetchPageControlResource`→`o.Vu` 定义但全量 166 个 js 无 dispatch 引用点 ⇒ 当前 UI 不使用 |
| 10 | selectResourceType | `GET app-resource-type` | 读 | **STATIC**（UNVERIFIED） | 未调用；ROLE-R1 同上三次真实交互均未触发，bundle `fetchAppResourceType`→`o.GN` 仅定义无 dispatch 引用点 |
| 11 | selectRoleAuthById | `POST role-auth` | 读 | **LIVE** | P3 §6：BOOT_0000 + role + resourceList，探针建绑后恰 1 条 |
| 12 | selectRoleAuthByAppId | `POST role-auth-all` | 读 | **⚠️ 部分 LIVE** | 2026-10-19 页面实测：body 仅 `appId`（无 `code`），返回 11 个 `{role, resourceList[]}`；目标角色 45 项，与 `udc_role_resource` 45 行相符。MENU 18 项与页面 `button[role=switch][aria-checked]` 目标列双向集合完全匹配（18/18；名称重复的“数据迁移”两行均保留）。旧“409条权限”口径撤回，不以数组聚合数作权限总数。证据 `implementer/evidence/ROLE-R2-authall-read.json`、`auditor/AUDIT-LOG-ROLE-R2-AUTHALL.md` |
| 13 | saveFuncAuthByRole | `POST func-auth` | 写 | **LIVE** | S5 §2 四次写，traceId 齐全 + DB/页面回读 |
| 14 | saveFuncAuthAll | `POST func-auth-all` | 写·批量 | **STATIC** | 未调用，**DANGER-ZONE** |
| 15 | createSystemAdmin | `POST create-system-admin` | 写·高危 | **⚠️ 部分 LIVE**（原写 STATIC「未调用」是错的） | P2 §7：页面加载**自动调用 3 次**，`BOOT_0000 / data.content:1`；调用前后 8 项 DB 计数完全一致、无新增行 ⇒ **「已存在→幂等零写入」为 LIVE**。「不存在→是否真建一行」UNVERIFIED。按严格口径不入 ✅ |

**✅ LIVE 只有 4 个：#7 / #8 / #11 / #13。** 其余：**2 个 ⚠️ 部分 LIVE**（#12 结论曾撤回、#15 仅覆盖「已存在」路径）+ **9 个 STATIC**。
（TASK-GOAL 验收①：STATIC 不得升格为 ✅ LIVE；「有回包/被调用过 ≠ 该端点全路径已验证」）

---

# 1. `create` — `udcCtpUserRoleCreatePost`（STATIC）

## 1.1 请求 schema

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `name` | string | 是 | 角色名称 |
| `code` | string | 是 | 角色编码，实测形如 `quanxian-datamigration<appId>` |
| `description` | string | 否 | 描述 |
| `appId` | string | 是 | 应用 id |
| `type` | int | 否 | 角色类型，见 `RoleTypeEnum`（facade 侧） |
| `relationOrgRoleCode` | string | **否**（曾被误记为必填） | 「默认授权给」的对象（组织角色模板），提交什么存什么。<br>**非必填**：不选也能建成（`ZZPROBE-ROLE-232003` 未选即落库成功）。原记「必填，不选则静默无反应」**已由 main DECISION-19 证伪** |

GraphQL 形态：`mutation udcCtpUserRoleCreatePost($body: udcCtpUserRoleCreatePostInputBody) { ... (body:$body) { code data{content} message status } }`

## 1.2 响应 schema

`SingleResponse<Long>` → GraphQL `data.content` = 新建角色 id（bigint 字符串）

## 1.3 LIVE 样例

**无。** 本端点未真实调用过（P3 建角色走的是页面，回包未单独留档）。

## 1.4 前置条件

- 目标 appId 存在且当前用户有 `udcAppDesigner` 或 `OrgAdmin` 等角色（`@HasRole` 见 javap）
- `code` 在同一 app 内应唯一（未实测，UNVERIFIED）

## 1.5 失败形态

| 形态 | 说明 | 证据 |
|---|---|---|
| **UI 侧曾误判为「必填静默拦截」**（**已被撤回，非失败形态**） | P3 §75 原记「『默认授权给』必填，不选点确定无请求、无 toast ⇒ 前端拦了」。**后按 P3 L137 与 main DECISION-19 撤回**：实际提交**成功了**（`ZZPROBE-ROLE-232003` 落库即铁证），「没反应」是 CDP `rpc()` 丢事件的工具假象（请求发了、库写了、没捕获到）。**该字段非必填**。 | **撤回记录**：P3 L137 / L580 铁律 7。**这是工具假象，不是接口失败形态** |
| 无权限 | `BOOT_` 权限码 | UNVERIFIED |
| code 重复 | 未测 | UNVERIFIED |

> ⚠️ **引用纪律（本条是活例）**：上面那条是「审计件里有过、但已被同文件撤回」的结论。
> **引审计件不能只 grep 命中处，必须读同文件有没有人撤回它** —— 我本轮就是因为只看到 P3 §75
> 的原始记录、没读 L137/L580 的撤回，把一条已被 DECISION-19 证伪的结论当「已有失败形态」补回了正文。

> ⚠️ **执行提醒（保留这段，但含义已变）**：那次「以为接口失败 → 重试 → 超额提交」的误判，
> 根因是 CDP 监听丢事件，**不是接口问题，也不是必填校验**（P3 §104-107）。
> ⇒ 补证时的第一条纪律：**先确认「到底有没有发出请求、库里有没有写入」**，再判成败。
> 不要用「页面没反应」推断「请求没发出」 —— 这正是本条被撤回的原因。

## 1.6 证据边界

STATIC：`javap -v -p` 读出 `@RequestBody UdcRoleDto` + `@RestApiOperation("新建角色")`。
**未验证**：真实字段约束、唯一性、失败码。

---

# 2. `update` — `udcCtpUserRoleUpdatePost`（STATIC，UI 字段已验）

> ⚠️ **等级纪律**：S5 验的是「UI 弹窗里字段可改」，**不是接口回包**。
> 按严格接口级口径 ⇒ **STATIC**。不得写成 LIVE。（TASK-GOAL 验收①点名此条）

## 2.1 请求 schema

同 #1，另加 `id`（必填，bigint 字符串）。GraphQL op：`udcCtpUserRoleUpdatePost`。

## 2.2 响应 schema

`SingleResponse<Integer>` → `data.content` = 影响行数（推断为 0 或 1，**未实测**）

## 2.3 LIVE 样例

ROLE-W2 实测：页面编辑 description；`udcCtpUserRoleUpdatePost` traceId `17924202530788394426`，143B 非空响应 `content=1`；同 id DB `description`、`update_time`、`version` 前后回读并由刷新列表响应/重开弹窗验证。证据 `implementer/evidence/ROLE-W2-update.json`。旧「无接口级样例」已过时。

## 2.4 前置条件

角色必须存在（`id` 有效）

## 2.5 失败形态

UNVERIFIED

## 2.6 证据边界

若后续要补 LIVE：改 `description` → `role-auth` 或 `select-list` 回读 → 改回（1 次写 + 2 次读，可回滚）。

---

# 3. `delete` — `udcCtpUserRoleDeletePost`（STATIC）

## 3.1 请求 schema

`@MultiRequestBody`，参数 `id`（bigint 字符串）。GraphQL op：`udcCtpUserRoleDeletePost`，body `{id}`。

## 3.2 响应 schema

`SingleResponse` → `data.content` 内容未取证。

## 3.3–3.6

LIVE 样例：**无**。前置条件：角色存在且无绑定（**未验证**）。失败形态：UNVERIFIED。
证据边界：STATIC（javap `@RestApiOperation("删除角色")`）。

> 删除角色对 `udc_role_resource` / `ctp_role` / `ctp_user_role` 的级联范围 **UNVERIFIED**。
> 参照栏目域经验（D28）：**不要用「应该会级联」推断，只能实测回读。**

### `role-auth-all` (#12) 实测契约补充（2026-10-19）
- Request body 仅 `{appId}`，不含 `code`；此端点返回应用全体角色及其 `resourceList[]`，按角色在客户端矩阵中筛选。不要将其误作单角色端点或扁平权限列表。
- LIVE 证据：目标角色 45 条与 `udc_role_resource` 45 行互证；其中 MENU 18 项与页面 switch 状态集合双向完全匹配。证据见上方表格链接。
- DOM 授权标记为 `button[role=switch][aria-checked]`；`checkbox`/`.anticon` 不是有效定位依据。空标记抓取不得用于判断无授权。
- 原“409 条权限”统计口径撤回：跨角色 resourceList 求和会重复计数，不是全局权限总数。

### ROLE-W1/W2 真实运行补充（2026-10-19）
- #1/#2/#3 均有 LIVE 页面写链证据；#3 为软删除：`is_deleted` 0→1，物理行仍在，判定不得用 COUNT(*) 或要求物理消失（DISCREPANCY-5）。
- `udc_role.name` 按 JSON 字符串保存，按 name LIKE 会漏；应按 id/code 查询并解析 JSON（DISCREPANCY-4）。
- 角色列表是 type=1 跨应用列表；description 不在列表列中，需用列表响应或重开编辑弹窗验证（DISCREPANCY-6）。

---

# 4. GraphQL op ↔ 后端端点对照（前端 bundle 实读）

| op（fieldType） | 类型 | 入参 | 后端端点 |
|---|---|---|---|
| `udcCtpUserRoleSelectListPost` | mutation | body: PageInfo+`params{appId}` | #7 select-list |
| `udcCtpUserRoleCreatePost` | mutation | body: UdcRoleDto | #1 create |
| `udcCtpUserRoleUpdatePost` | mutation | body: UdcRoleDto | #2 update |
| `udcCtpUserRoleDeletePost` | mutation | body: `{id}` | #3 delete |
| `udcCtpUserRoleRoleAuthPost` | mutation | body: `{roleId}` | #11 role-auth |
| `udcCtpUserRoleFuncAuthPost` | mutation | body: UdcRoleFuncPermissionDto | #13 func-auth |
| `udcCtpUserRoleRoleAuthAllPost` | mutation | body: `{appId, code}` | #12 role-auth-all |
| `udcCtpUserRoleFuncAuthAllPost` | mutation | body: List | #14 func-auth-all |
| `udcCtpUserRoleAppResourceGet` | query | query: `{appId, admin}` | #8 app-resource |
| `udcCtpUserRoleAppResourceTypeGet` | query | — | #10 app-resource-type |
| `udcCtpUserRoleSelectPageResourceGet` | query | query: `{appId, code}` | #9 select/page-resource |
| `udcCtpUserRoleGet` | query | path `{id}` | #6 selectById |
| （REST 直连）`/service/udc/ctp-user/role/create-system-admin` | POST | — | #15 |

> 前端 bundle 实读（`module1622.js` / `role-*.js` chunk），属 **STATIC（bundle 解析）**，非运行取证。
> ⚠️ **本表只描述「op 名 ↔ 后端端点」的映射关系**（来源是 bundle，故整表 STATIC）；
> **各端点自身的证据等级见卷首「全局等级总表」** —— 其中 SelectListPost / AppResourceGet / FuncAuthPost
> 三个端点有 LIVE 回包样例（见 §5/§6/§9）。**不要把本表的 STATIC 当成本表的端点没有 LIVE。**

---

# 5. `select-list` — `udcCtpUserRoleSelectListPost`（**LIVE**）

## 5.1 请求 schema

```
variables.body = {
  pageInfo: { needTotal:bool, pageNumber:int, pageSize:int },
  params:   { appId:"9000000000000000002" },
  ...排序(可选)
}
```

## 5.2 响应 schema

`data.content[]`，每项角色对象：
```
{ admin:bool, appId:string, code:string, description:string, id:string(bigint), name:string, type:int }
```
`data.pageInfo`：`{needTotal, pageNumber, pageSize, total}`

## 5.3 LIVE 样例（原文，2026-10-18 02:19 抓包）

```json
{"traceId":"17922611342802003299",
 "data":{"udcCtpUserRoleSelectListPost":{"code":"BOOT_0000","status":0,
  "data":{"content":[{"admin":false,"appId":"9000000000000000002",
    "code":"ZNXMGLTBGLY-datamigration9000000000000000001","descript..."}]}}}}
```
（完整原文见 `implementer/evidence/ROLE-S5-full-netcapture.json`）

## 5.4 前置条件

当前用户对该应用有可见角色（本环境 test-account-1 可见 11 角色）

## 5.5 失败形态

未取证（未构造失败场景）

## 5.6 证据边界

LIVE：有真实回包原文（GraphQL 形态）。**未验证**：分页边界、排序字段全集。

---

# 6. `app-resource` — `udcCtpUserRoleAppResourceGet`（**LIVE**）

## 6.1 请求 schema

```
variables.query = { appId:"9000000000000000002", admin:false }
```
`admin:true` 时是否返回额外（系统级）资源：**UNVERIFIED**。

## 6.2 响应 schema

`data.content` 是**按资源类型分组**的对象：
```
{ "PC_LAYOUT": [...], "PC": [ { validate:bool, id:string, guid:string, originalId:string, ... } ], ... }
```
每项含 `id`（资源 id，bigint 字符串）、`validate`、`guid`、`originalId` 等。

## 6.3 LIVE 样例（原文）

```json
{"traceId":"17922611342440056080",
 "data":{"udcCtpUserRoleAppResourceGet":{"code":"BOOT_0000","status":0,
  "data":{"content":{"PC_LAYOUT":[],"PC":[{"validate":true,
    "id":"9045337234040441658","guid":"-7710412376094916133","originalId":...}]}}}}}
```

## 6.4 前置条件

无特殊（只读）。`admin=false` 会把系统/机构管理员角色相关资源滤掉（与 §0.2 同源机制）。

## 6.5 失败形态

未取证

## 6.6 证据边界

LIVE（有回包原文）。**未验证**：`admin=true` 的差异、资源类型全集（`PC_LAYOUT`/`PC`/…）。

---

# 7. `role-auth` — `udcCtpUserRoleRoleAuthPost`（**LIVE**）

**按 roleId 读该角色的授权列表。这是 §0.1 覆盖式写入前的必读步骤。**

## 7.1 请求 schema

```
variables.body = { roleId:"7848047731790858930" }
```

## 7.2 响应 schema

```
data.content = {
  role: { validate, id, guid, originalId, code, name, type, appId, ... },
  resourceList: [ { id, resourceId, resourceType, action } ]
}
```
- `resourceType`：枚举**名字符串**（如 `"MENU"`）
- `action`：枚举**名字符串**（如 `"basic"`），写库时映射为 `udc_role_resource.action` 数字，见 §9

## 7.3 LIVE 样例（原文）

```json
{"traceId":"3279025517046532284",
 "data":{"udcCtpUserRoleRoleAuthPost":{"code":"BOOT_0000","status":0,
  "data":{"content":{"role":{"validate":true,"id":"7848047731790858930",
    "guid":"-5406396911214901150","originalId":"0","code":"quanx...",
    "resourceList":[...]}}}}}}
```

## 7.4 前置条件

roleId 必须存在。探针角色建绑后实测恰 1 条（P3 §6）。

## 7.5 失败形态

| 形态 | 表现 |
|---|---|
| roleId 不存在 | `content` 为空 / 错误码（未取证精确形态） |
| 角色无授权 | `resourceList: []`（**这是真空，与 §0.2 的假阴性不同** —— 本端点按 roleId 直查，不经 admin 过滤） |

## 7.6 证据边界

LIVE（回包含真实 role + resourceList）。

---

# 8. `role-auth-all` — `udcCtpUserRoleRoleAuthAllPost`（**⚠️ 部分 LIVE**，审计件标 ⚠️ 非 ✅）

**⚠️ 先读 §0.2。** 这个端点的 `code` 参数陷阱是本域最贵的教训。

## 8.1 请求 schema

```
variables.body = { appId:"9000000000000000002", code:"<资源 code>" }
```
- `code` = **资源 code**（不是 appId、不是角色 code）
- 不传 code ⇒ 走全量分支但 `admin=false` 过滤后匹配集为空 ⇒ **假阴性**

## 8.2 响应 schema

```
data.content = { <roleId 或角色键>: [ {resourceId, resourceType, action}, ... ] }
```
或 `11 角色 + 各角色 resourceList`（形态依实现，见下例）

## 8.3 真实回包（三组对照，P3 §9.6 原文）

| 入参 | 结果 |
|---|---|
| `{appId, code:"2084600749018399891"}` | 11 角色 / **289** 行授权 |
| `{appId, code:"9183843213439484192"}` | 11 角色 / **21** 行授权 |
| `{appId}`（无 code） | 11 角色 / **0** 行 ← ⚠️ **假阴性** |

数字自洽（按资源子树过滤）。**原「与 DB rr_app=409 互证」已撤回** —— 那是调参错误。

## 8.4 前置条件

必须已知目标资源 code（可从 #8 `app-resource` 的 `id` 取）

## 8.5 失败形态

| 形态 | 说明 |
|---|---|
| 不传 code | **不报错**，返回 11 角色 + 空 resourceList ⇒ 最危险，因为看起来成功 |
| code 错误/不存在 | UNVERIFIED |

## 8.6 证据边界

**⚠️ 部分 LIVE，不记 ✅**：三组参数有真实回包（证据强度够），但**基于它的结论曾错并被撤回**。
按严格口径「有回包 ≠ 结论成立」，故不入 ✅ 名单，保持 ⚠️ 并原样保留撤回记录 ——
否则下一个人会重踩「不传 code 得出假阴性」这个坑。

---

# 9. `func-auth` — `udcCtpUserRoleFuncAuthPost`（**LIVE，本域唯一写链完整闭合**）

**⚠️ 先读 §0.1：覆盖式，按 roleId 全删全建。**

## 9.1 请求 schema（真实抓包原文）

```json
variables.body = {
  "roleId": "7848047731790858930",
  "roleCode": "quanxian-datamigration9000000000000000001",
  "resourceList": [
    {"resourceId": "9045337234040441658", "resourceType": "MENU", "action": "basic"},
    {"resourceId": "3974578600125940031", "resourceType": "MENU", "action": "basic"}
  ]
}
```
- `roleCode` 与 `roleId` **都要传**（实测原文两者并存）
- `resourceType` / `action` 是**枚举名字符串**，不是数字

## 9.2 响应 schema

```
data.content = <写入后该角色的授权总条数>   ← 注意：是总数，不是增量
```
实测：传 1 条 → `content:1`；传 2 条 → `content:2`；还原为 1 条 → `content:1`。

## 9.3 LIVE 样例（四次写，traceId 齐全）

```json
{"traceId":"3279025464684841148","data":{"udcCtpUserRoleFuncAuthPost":
  {"code":"BOOT_0000","data":{"content":2},"message":"SUCCESS","status":0}}}
```
另三次：`traceId` `3279012885178615996` / `3279013735347259580` / `3279014565114808508`（均 `content:1`）；
还原写：`3279026818237073596`（`content:1`）。

## 9.4 前置条件（LIVE）

1. **必须两个独立角色做正负样本** —— 覆盖式语义下，同一角色做第二次会毁掉第一次的证据（P3 §574-607）
2. 写入前先 `role-auth`(#11) 读出全量，避免误删既有授权
3. 目标应用内 `udc_role_resource` 表可写

## 9.5 失败形态

| 形态 | 表现 | 证据 |
|---|---|---|
| **既有非 type=0 行被整包重写退化为 0** | 该端点无 `setResourceType` ⇒ 写入行**机制上**恒为 `resource_type=0`。若该角色原有非 type=0 的行，全删全建后**会**退化为 0，且回滚走同一端点也写不回来 | **机制 = STATIC+LIVE**：字节码无 `setResourceType`（offset 94→129 只设 roleId/resourceId/action，STATIC 确证）+ 落库回读 `resource_type=0`（S5 L296 / P3 L736，LIVE 确证）。<br>**⚠️ 退化面 = 推算**：P3 L768-780 的「该角色 rr_type≠资源真实 type 的行数」是**静态盘点**，不是「重写后确实退化」的实测 ⇒ 实际影响面**须执行前 COUNT 现查**，无现成数字 |
| 空 resourceList | 会**清空**该角色全部授权（覆盖式），不是「不做任何事」 | LIVE（§0.1） |
| roleId 不存在 | 未取证精确形态 | UNVERIFIED |
| 越权 | 未取证 | UNVERIFIED |

> ⚠️ **执行前置检查（写死，别跳过）**：选角色前必须确认
> `COUNT(rr.resource_type <> u.type) = 0`（该角色既有授权里没有错配行），否则一写就退化。
> 目标 app 的 type=0 池：41 个（其中 `data_type='NORMAL'` 且未被目标角色授权的 14 个）。

## 9.6 ⚠️ 已知缺陷：`resource_type` 恒为 MENU

**service 层无 `setResourceType` 调用**（字节码确证）⇒ 写入行恒为 `resource_type = MENU.code = 0`。
若资源实际 `type ≠ 0`，该行即为**错配**：页面按 `resource_type` 分类渲染时会归到 MENU 类而非真实类型
⇒ **权限清单显示不全 ⇒ 假阴性**（P3 §737）。

## 9.7 证据边界

LIVE（4 次写 + DB 回读 + 页面可见）。**未验证**：`resource_type` 错配的实际影响面、并发写。

---

# 10. 剩余 STATIC 端点速查

| # | 端点 | 关键点 |
|---|---|---|
| 6 | `GET {id}`（selectById） | 返回 `SingleResponse<UdcRoleDto>`；queryFields 含 `relationOrgRoleCode`/`guid` |
| 9 | `GET select/page-resource` | `@RequestParam appId, code`；与 #8 同资源树另一切面 |
| 10 | `GET app-resource-type` | 返回资源类型 → 参数映射，无入参 |
| 14 | `POST func-auth-all` | `@RequestBody List<UdcRoleFuncPermissionDto>`；见 DANGER-ZONE |
| 15 | `POST create-system-admin` | `@MultiRequestBody`；见 DANGER-ZONE |

均标 **STATIC**（javap 注解 + 签名），无真实回包。

---

# 11. DANGER-ZONE（风险登记面）

> ⚠️ **先分清两件事，别把改判当复述**：
> - **#4 / #5：沿用既有裁定** —— P1-GAP §4.2「明确『不补』，只登记为禁用面（2 个）」原文如此，本契约照抄，**不越权**。
> - **#14 / #15：本契约改判** —— P1-GAP §4.1 原判是「**值得排期补**」的 3 个之一
>   （#15「P1 值得补」、#14「P2 补」）。本契约**暂不补证**（理由见下，属风险论证）。
>   该改判**经 main 2026-10-18 授权生效**（见 `main/RULING-ROLE-ARB.md`）；
>   表格「裁定归属」列已据此填写。
>
> 🔓 **解除条件（必须写，否则「暂不补」会变成永久豁免）**：
> 若未来要补这两条，前提是 **整表备份 + 独立 zzprobe 应用 + 可整库回滚**，且**单独立项**，不进本契约。

| # | 端点 | 风险 | 补证要付什么代价 | 裁定归属 |
|---|---|---|---|---|
| **4** | `POST delete-resource/app/{appId}` | **一次调用清空单应用全部角色授权**（`udc_role_resource` 按 app 全清） | 要验证它就必须真的清空一次。#13 func-auth 已 LIVE 闭合同表写语义 ⇒ 边际信息为零、风险不可逆 | **沿用 P1-GAP §4.2「明确不补」** |
| **5** | `POST delete-resource/{id}` | 删单条授权行 | 风险低（可重建），但补证仍要主动删。#13 覆盖式写已覆盖「删+写」两向 | **沿用 P1-GAP §4.2「明确不补」** |
| **14** | `POST func-auth-all` | **批量覆盖**多个角色的授权集 | 单次影响面 = #13 × 角色数。补证需同时破坏 N 个角色的授权状态，恢复要逐角色重放（每个都带覆盖风险）。收益仅是「确认是 List 入参」这一 STATIC 已知事实 | **改判经 main 2026-10-18 授权**（P1-GAP §4.1 原判「P2 补」→ 本契约不补） |
| **15** | `POST create-system-admin` | **权限提升**（授予系统管理员身份） | 补证**只能验「已存在」路径**（该路径已被页面加载被动验过 3 次，幂等零写入）；**「不存在时首次真建一行」无法在现网安全复现**（会真的多出一个系统管理员，且撤销路径未验证） | **改判经 main 2026-10-18 授权**（P1-GAP §4.1 原判「P1 值得补」→ 本契约不补） |

**统一判据**：这四条的共同点是 **「要证明它安全，必须先让它生效一次」**，而生效的后果不可逆或不可控。

若未来确需补证，最小前提：**整表备份 + 独立 zzprobe 应用 + 可整库回滚**，且必须单独立项、不进本轮契约。

> 🔧 **本条已订正一处事实错误**（原写「#15 补证要真实创建一个系统管理员」）：
> 【引用已有 LIVE 记录，非本次结论】P2 §7 实测该端点在「已存在」时**幂等零写入**，所以补证并不会建人。
> 真正的障碍是**反方向**：你只验得到「已存在」分支，验不到「首次创建」分支 —— 除非拿一个真没有
> SystemAdmin 的应用去冒这个险。原表述把「验不到」错说成「不敢验」，理由错了。

---

# 12. oplog 与审计（D28 判据）

**本域 `udc_operation_log` 是否写入 = UNVERIFIED。**

D28 判据（2026-10-18 立）：**任何「某表会不会被写」的判断，唯一有效判据是实测有没有行；
不得用注解 / 命名 / 惯例反推。**

反面依据（为什么不能用注解推）：
- 全库 54 个 Controller 中，`OperationLog` 注解只命中 `OperationLogController` 1 个（且其方法全是查询/清空）
- 但**栏目域确实写 oplog**（action_type=1/2/3 全套 LIVE），而其 `PortletController` 的 `OperationLog` 注解 = 0

⇒ 角色域同理：**没实测就写 UNVERIFIED，不写「应该会写」也不写「应该不写」。**

若后续要补：查 `udc_operation_log` 在写操作时刻 ±90s 内有无行、`module`/`sub_module` 是否角色域。

---

# 13. 本契约的边界（不写什么）

| 不写 | 原因 |
|---|---|
| 角色 → 用户的绑定链 | 属 organization 服务，DB 侧绑定=0 已确证，接口侧读面 UNVERIFIED（P3 §489） |
| `ctp_role` / `ctp_user_role` 的完整 schema | 属平台表，非本域契约范围 |
| 权限面板 UI 元素映射 | P1 无 UI ↔ 端点映射，补 LIVE 时不知点哪里 |
| 未取证的失败码细节 | 只写审计件里**仍有效**的失败形态（如 #13 `resource_type` 退化）；**不写已被同文件撤回的**（如 #1「必填静默无反应」已由 DECISION-19 证伪）。其余一律 UNVERIFIED，不猜 |

---

# 14. 证据来源索引（输入，非产出）

## 14.1 依赖说明（**javap 已入仓可复算；class 未入仓**，须自备）

本契约的 **15 端点** 来自 `UdcRoleController` 的 `javap -v -p` 产物。**证据链三级，各自入仓状态与可证范围不同：**

| 层级 | 在仓库里？ | 能证什么 | 不能证什么 |
|---|---|---|---|
| **javap.txt** | ✅ **在**（77,922 B，已 `git ls-files` 确认） | **15 / 1 / 16 的计数**（仓内即可复算） | 这份 javap 是否真来自该 class |
| **class** | ❌ **不在**（11,879 B / sha256[:16] `885fba643fa899ab`，仅作者工作区） | *（自备后）* 本地可证「javap ↔ 你这份 class 一致」，须 JDK 21 | 仓内**证不了**；也证不了「class ↔ 官方 jar」 |
| **官方 jar** | ❌ **不在**（体积+授权） | *（自备后）* 可追溯 class 的来源 | **任何人都证不了**（除非手上有原始 jar） |

⇒ **读者应按上表理解，不要读成「能验 / 不能验」两句对立的话** —— 是「逐级降级」，每级只证到它自己那一层。

```
docs/audit/artifacts/udc-user-5.3.517-contracts/
  UdcRoleController.javap.txt   77,922 B   ← 已入仓
  （UdcRoleController.class 未入仓：根 .gitignore 第 41 行 `*.class` 挡住）
```

> ⚠️ **一句必须说清的话（否则就是夸大）**：**clone 这个仓库的第三人只有 `javap.txt`，没有 `class`。**
> 所以他**能**复算「15/1/16」，但**不能**直接复现下面的 `javap ↔ class` 一致性验证 ——
> 那一步需要他自己拿到同版本（`udc-user-5.3.517`）jar 里的 `UdcRoleController.class`。
>
> 这一点原本被我写成「class 已纳入仓库」，是**错的**（未核实 `git ls-files` 就下了断言）。
> 现按实际状态改正：**仓内可复算 javap 的数字；javap↔class 一致性是作者已验、但仓内不可复现的一步。**

### 怎么验真（不是"相信我"，是能自己跑）

**① 复算 15 端点**（仓内即可，见上文「15 这个数怎么复算」）：
```
grep -cE 'annotation\.(Post|Get)Mapping\('  UdcRoleController.javap.txt   # → 15
grep -cE 'annotation\.RequestMapping\('     UdcRoleController.javap.txt   # → 1
grep -oE 'value=\["[^"]*"\]' UdcRoleController.javap.txt | wc -l          # → 16
```

**② 验「这份 javap 确实来自这个 class」**（这一步才让上面那 15 有意义）：

> ⚠️ **前置条件：javap 版本必须是 JDK 21。用 JDK 8 会得到完全错误的结论 —— 而且错得比 diff 不一致更严重。**
>
> 实测对照（同一份 `UdcRoleController.class`，只换 javap 版本）：
>
> | 项 | JDK 21.0.10 | JDK 8 (`corretto-1.8.0_504`) |
> |---|---|---|
> | 输出行数 | **1290** | 1120 |
> | diff 跳过前两行 | **0** | **230 行变更**（`diff` 输出共 **352** 行 = **230** 变更行 + **93** 块头〔29 `c` + 64 `d`〕+ **29** 分隔符） |
> | checksum 行 | `SHA-256 checksum 885fba64…` | `MD5 checksum 7db76003…` |
> | 注解展开 | `0: #55()` **+ `org.springframework…Autowired`** | 只有 `0: #55()`，**不展开类名** |
> | `grep -c 'annotation\.(Post\|Get)Mapping\('` | **15** | **0** ← 🔴 致命 |
>
> **两个后果，第二个才是真的坑：**
> 1. diff 不为 0 → 照抄者会以为「这份 javap 是伪造的」。
> 2. **`annotation.(Post|Get)Mapping(` 在 JDK 8 输出里命中 0 次** —— 因为 JDK 8 不展开注解类名。
>    也就是说：**用 JDK 8 的人连「15」这个数都算不出来，会得到 0，然后判定契约整体是假的。**
>
> ```
> javap -version          # 必须 21.x；得到 1.8 就别往下走，先换版本
> ```
>
> 契约的 javap 产物由 **JDK 21.0.10** 生成。**这不是免责声明，是复现的必要前置条件。**

```bash
# ⚠️ 前提：UdcRoleController.class 未入仓，须自备同版本（udc-user-5.3.517）class 放同目录
javap -v -p UdcRoleController.class > regen.txt     # 需 JDK 21
diff <(tail -n +3 UdcRoleController.javap.txt) <(tail -n +3 regen.txt)   # → 0 行差异
```
实测（JDK 21.0.10）：1290 行，忽略前两行（`Classfile` 路径 + `Last modified`）后**逐行完全一致**。
⇒ javap 不是"随便一份文本"，它**可由同一份 class 重新生成并逐字复核**（前提：**自备该 class**，见 §14.1 开头的三级表 —— 它未入仓）。
   **这一步在仓内做不了**（仓库里没有这个 class），属「作者已验、他人须自备材料才能复现」。

**另一个仍要说清的限制：本产物曾在多个目录存在同名副本**，且**不同副本的 sha 不同**（因文件头写入了各自的本地路径与 mtime）：
   ```
   implementer-only/role_static_r2/ctrl_v.txt   77,922 B   ← 本文采用这份
   audit03_role_static/ctrl_v.txt               77,901 B   ← 语义等价，头两行不同
   diff 结果：仅 4 行（Classfile 路径 + Last modified），body 完全相同
   ```
   ⇒ **认产物必须认 class 的 sha256（`885fba643fa899ab`），不要认文件名或目录。**
   这是本域真实踩过的风险：**在错误的副本上跑，也能得出正确数字**（因为两份恰好等价）；
   若两份来自不同 jar 版本，就会得出「契约数字错误」的假结论 —— 那次算对纯属运气。

> 对比 `setting/publish-chain.runbook.md` 的 23 端点：那份从开始就用仓库内的
> `docs/audit/artifacts/udc-web-5.3.517-contracts/*.javap.txt`。
> 本域是两个 commit 之间才补齐的（`8ea0446` → `ed8c636` 登记弱点 → 本版消掉）。

## 14.2 输入文件清单

| 用途 | 文件 |
|---|---|
| 15 端点 STATIC 全文（javap） | `docs/audit/role/P1-role-frontend-call-chain.md` |
| 等级矩阵 + 补证优先级 | `docs/audit/role/P1-LIVE-GAP-MATRIX.md` |
| 写链实测（func-auth 4 次写） | `docs/audit/role/S5-role-write-chain-closure.md` |
| role-auth-all 撤回记录 | `docs/audit/role/P3-role-write-chain.md` §9.4 / §9.6 |
| 读链 LIVE | `docs/audit/role/P2-role-live-readback.md` |
| 对象模型（三表 DDL + 分布） | `docs/audit/role/P0-role-object-model.md` |
| 权限面板重核 | `docs/audit/role/P3b-permission-panel-recheck.md` |
| func-auth 分支追踪 | `docs/audit/role/P1-FUNCAUTH-BRANCH-TRACE.md` |
| 结构补充 | `docs/audit/role/P1-STRUCTURE-SUPPLEMENT.md` |
| 抓包原文 | `implementer/evidence/ROLE-S5-full-netcapture.json`（另 `ROLE-S5-probe/restore/cleanup-dom.json`） |
| 凭据（仅路径） | `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json` |
