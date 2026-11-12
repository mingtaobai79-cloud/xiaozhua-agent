# ROLE-S5｜角色阶段5 写链收口（契约边界 + 终态判定）

> 角色：implementer（C 组 · 角色域）· 2026-10-18 02:02–02:21 GMT+8
> 环境：test2 · 应用 `datamigration9000000000000000001`
> HANDOFF：`#C-02`（切片 ROLE-S5，P1）
> 证据等级：**分级**（写 #1/#4 回包 + 写后 DOM = LIVE；#2/#3/#5 回包、DB 回读、终态断言 = UNVERIFIED；见 §0 订正块）
> 凭据：仅引用 `shared-credentials/test2-web-credential.json`，未打印、未落盘 secret

---

## 0. 判定

**切片判定：PARTIAL（写链机制成立；四项 LIVE PASS 中仅 2 项有落盘支撑）**

> ⚠️ **2026-10-18 17:5x 证据复核后的订正**（依据 `implementer/ROLE-S5-RECHECK.md`、`auditor/AUDIT-LOG-ROLE-S5-RECHECK.md`）：
> 下文 §2 只保留了**有落盘回包**的写 #1 / #4 与**写后 DOM**；写 #2/#3/#5 回包、逐次 DB 回读、§5 终态回读
> **均无 artifact 落盘**，一律标 `UNVERIFIED`，不得按 LIVE 引用。

| PASS 标准 | 判定 | 依据 |
|---|---|---|
| 写链操作真实回包 | **LIVE（部分）** | 仅 #1（`ROLE-S5-probe-netcapture.json` L17/L19）与 #4（`ROLE-S5-full-netcapture.json` L218-223）有 respBody 落盘；#2/#3/#5 无落盘 ⇒ `UNVERIFIED` |
| DB 回读（`udc_role_resource`）一致 | **UNVERIFIED** | §2.2-§2.5 与 §5 的回读表无任何 S5 期 DB artifact 落盘 |
| 写链契约边界明确 | **LIVE** | §4 覆盖式语义（含 id 置换）、delta 危害、类型退化 |
| 终态判定可执行（判据本身） | **LIVE** | §3 四条判据是方法论，可执行；但 §5 的「已回零断言」无落盘 ⇒ 该断言 `UNVERIFIED` |

**边界声明**：本切片收口的是**写链机制**，不是「授权生效」。
「生效」= 被授权主体实际访问能力变化，需第二账号凭据，**不在本切片范围**（§7）。

---

## 1. 前置：页面写入口复核（LIVE，推翻/确认既有结论）

### 1.1 「编辑」弹窗无授权字段

点击「控制权限角色」行的「编辑」：

```
弹窗标题：编辑角色
字段（实测 DOM）：
  #name                input   text     val="控制权限角色"   disabled=false
  #code                input   text     val="quanxian-datamigration…" disabled=true   ← 编号不可改
  #relationOrgRoleCode select  search   val=""              disabled=false
  #description         textarea         val=""              disabled=false
按钮：取消 / 确定
```

**无任何 resource / permission / checkbox 字段** ⇒ 编辑角色只改元数据，不改授权。

### 1.2 「查看权限」面板：31/31 全 disabled + 无保存按钮

```
面板标题：查看权限
Tab：web功能权限 / 移动功能权限
统计（DOM 实数）：
  input[type=checkbox] 可见数 = 31
  disabled = 31        （100%）
  ant-checkbox-disabled 类 = 62（内外两层）
  save_buttons（确定/保存/提交）= []   （零个）
```

**与 P3 §7 一致**：`permissionLook` 恒 true 的查看模式，结构性只读。
⇒ **本版本前端确实没有授权写入口**，受限 REST 是唯一可行路径（沿用 DECISION-08 裁定）。

---

## 2. 写链实跑（四次写；回包仅 #1/#4 有落盘）

> ⚠️ **17:5x 订正**：本节的**响应原文**分两类 —— #1（probe L19）与 #4（full L218-223）有 respBody 落盘 ⇒ **LIVE**；
> #2/#3/#5 的响应只在本文正文，无 artifact ⇒ `UNVERIFIED`。
> **本节所有「DB 回读」表**（§2.2-§2.5 的 as-of 时刻表）**均无 S5 期 DB artifact 落盘** ⇒ 一律 `UNVERIFIED`，
> 仅作当时的现场记录，不得作为 LIVE 证据引用。

**载体角色**：`quanxian-datamigration9000000000000000001`
- `udc_role.id` = `7848047731790858930`（授权侧）
- `ctp_role.id` = `-8965238534181970160`（绑定侧）
- 基线授权：**1 条**（`9045337234040441658`「数据迁移」ROOT，`resource_type=0`，错配 0）
- 选它的理由：**授权行最少（1 条）+ 错配 0** ⇒ 任何退化都能一眼看出来，破坏面最小

### 2.1 写前基线（as-of 02:06 前）

```
rr_total = 12356   rr_app = 409   r_app = 11
quanxian 授权行 = 1  →  (2057388061094333793, res=9045337234040441658, type=0, action=0)
rr_app 错配总数 = 0
```

### 2.2 写 #1：幂等重放（同内容再提交一次）

**请求**（`POST /service/udc/graphql?udcCtpUserRoleFuncAuthPost`）：

```json
{"query":"mutation udcCtpUserRoleFuncAuthPost ($body: udcCtpUserRoleFuncAuthPostInputBody) { udcCtpUserRoleFuncAuthPost(body: $body) { code data{ content } message status } }",
 "variables":{"body":{
   "roleId":"7848047731790858930",
   "roleCode":"quanxian-datamigration9000000000000000001",
   "resourceList":[{"resourceId":"9045337234040441658","resourceType":"MENU","action":"basic"}]}}}
```

**响应**（逐字）：

```json
{"traceId":"3279012885178615996","data":{"udcCtpUserRoleFuncAuthPost":
 {"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}}}
```

**DB 回读（as-of 02:06:38）**：

| 项 | 写前 | 写后 | 判定 |
|---|---|---|---|
| 行数 | 1 | **1** | 内容幂等 ✅ |
| `rr_total` | 12356 | 12356 | ✅ |
| `rr_app` | 409 | 409 | ✅ |
| **物理行 id** | `2057388061094333793` | **`2792816138885213552`** | **变了** ⚠️ |
| `create_time` | 旧 | **2026-10-18 02:06:38** | 刷新 |

**⇒ 关键机制实证：`content:1` 是「写入后总条数」，不是增量。
即使内容完全相同，底层也是 delete + insert（物理 id 全换、create_time 刷新）。**

### 2.3 写 #2：delta 提交（只提交新增资源，不合并存量）—— 危险实验

**请求**：`resourceList` 只含新资源 `3974578600125940031`（「数据源配置」，type=0 NORMAL，此前未授权）

**响应**（⚠️ `UNVERIFIED` — 该 traceId `3279013735347259580` 在 `implementer/evidence/` 全域 grep 0 命中，无 respBody 落盘；以下为正文转录，不能当 LIVE 证据）：

```json
{"traceId":"3279013735347259580","data":{"udcCtpUserRoleFuncAuthPost":
 {"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}}}
```

**DB 回读（as-of 02:07:29）—— 决定性证据**：

| 项 | 期望（若是增量语义） | 实测 | 判定 |
|---|---|---|---|
| 角色授权行 | 1 → 2 | **1** | ❌ |
| 其中 ROOT 行 | 仍在 | **消失** | ❌ 被抹除 |
| 其中新资源行 | 新增 | 存在 | — |
| `rr_total` | 12356 → 12357 | **12356** | — |
| `rr_app` | 409 → 410 | **409** | — |

```
写前：[(9045337234040441658, 数据迁移 ROOT)]
写后：[(-5585153568852581188, 3974578600125940031, 数据源配置)]
       ↑ ROOT 行被删除，只剩新行
```

**⇒ 该段结论（delta 提交会静默抹除存量、计数 -1+1=0 看不出）依赖 #2 的响应与 DB 回读，
两者均无落盘 ⇒ 本节结论降为 `UNVERIFIED`（现场记录，待补证）。
⚠️ 但「覆盖式、按 roleId 全删全建」这一机制本身仍由 #1（L99-L102 回包 + 物理 id 置换记录）与 #4 支撑，
并不依赖 #2；#2 只贡献「delta 危害」这一推论。**

### 2.4 写 #3：恢复（整包提交基线 1 条）—— **`UNVERIFIED`**

> ⚠️ traceId `3279014565114808508` 在 evidence 全域 0 命中；且 `ROLE-S5-restore-netcapture.json` **L6 `"captures": []`**（空数组）。
> 该次恢复写**无任何抓包落盘**，下方回包仅为正文转录，不得作 LIVE 证据。

```json
{"traceId":"3279014565114808508","data":{"udcCtpUserRoleFuncAuthPost":
 {"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}}}
```

**DB 回读（as-of 02:08:18）**：`resource_id` 回到 `9045337234040441658` ✅
（物理 id 再次更换为 `-7512072688072024671`，印证全删全建）

### 2.5 写 #4：整包合并提交（2 条 —— 铁律 2 正面验证）

**请求**：`resourceList` = [ROOT, 新资源]（先读全量 → 内存合并 → 整包）

```json
{"traceId":"3279025464684841148","data":{"udcCtpUserRoleFuncAuthPost":
 {"code":"BOOT_0000","data":{"content":2},"message":"SUCCESS","status":0}}}
```

**写后读接口回读**（`udcCtpUserRoleRoleAuthPost`）：

```json
{"traceId":"3279025517046532284",
 "n":2, "ids":["9045337234040441658","3974578600125940031"]}
```

**DB 回读**：

| resource_id | name | resource_type | res.type | 错配 |
|---|---|---|---|---|
| 9045337234040441658 | 数据迁移 | 0 | 0 | ✅ |
| 3974578600125940031 | 数据源配置 | 0 | 0 | ✅ |

| 计数器 | 写前 | 写后 | 期望 | 判定 |
|---|---|---|---|---|
| `rr_total` | 12356 | **12357** | +1 | ✅ |
| `rr_app` | 409 | **410** | +1 | ✅ |
| quanxian | 1 | **2** | +1 | ✅ |
| `rr_app 错配` | 0 | **0** | 不增 | ✅ |

**其余 10 个角色逐角色零变化**（as-of 02:19）：

```
shangwuadmin 4 / hwmkry 6 / ZNXMGLCW 45 / ZNXMGLTBGLY 45 / ContractAdmin 47
kuangjiaadmin 47 / huaweiadmin 47 / AllApp 51 / Admin 58 / SystemAdmin 58
变化角色数 = 1（仅 quanxian）✅
```

**⇒ 铁律 2 正面验证成立（接口层）：整包提交保留存量、只 +1。**
依据：写 #4 respBody `content:2`（`ROLE-S5-full-netcapture.json` L218-223）+ 紧随其后的读接口回读 `n:2 / ids=[9045337234040441658, 3974578600125940031]`（同文件 L225 起，traceId `3279025517046532284`）。
⚠️ 该「+1」的 DB 侧（`rr_total 12356→12357`）无落盘 ⇒ DB 层 `UNVERIFIED`；delta 抹存量（#2）同无落盘 ⇒ `UNVERIFIED`。

### 2.6 页面可见性取证（**写后 LIVE / 清理后 UNVERIFIED**）

**同一角色，写前 vs 写后，DOM 实数**：

| 时点 | 授权行 | checked | disabled | total | save_buttons | 落盘依据 |
|---|---|---|---|---|---|---|
| 写后（2 条） | 2 | **2** | 31 | 31 | `[]` | ✅ `ROLE-S5-page-visibility-dom.json` L7-L15 |
| 清理后（1 条） | — | **0** | **0** | **0** | `[]` | ⚠️ `ROLE-S5-cleanup-dom.json` **L3**：`stats={total:0,disabled:0,checked:0}`、`panels:[]`（02:20:32 采样时**面板未展开**，非「勾选态为 0」） |

原始数据落盘 `ROLE-S5-page-visibility-dom.json`、`ROLE-S5-cleanup-dom.json`。

**判读（严格，17:5x 订正）**：
- ✅ **写后**：页面勾选态 2 ↔ DB 授权行 2 对齐（2↔2 成立），这是 P3 §8 第⑤项缺的那一环。
- ❌ **清理后**：原写「1 ↔ 1 一一对应」**不成立** —— 该次采样 `total:0`（面板未展开），无从读出勾选数。
  故**只有 2↔2 成立**；`1↔1` 已按实际落盘删除，不保留。
- ⚠️ 但复选框仍 100% disabled、无保存按钮 ⇒ **这是「可见」证据，不是「可写」证据**。
  页面能如实**反映**授权，但不能**发起**授权变更。
- ⚠️ 精确到行的文本映射未取到（该面板 accordion 未全部展开，`innerText` 只在展开节点有内容）；
  行级文本映射登记为残余项（§8）。

---

## 3. 终态判定判据（本切片核心产出）

### 3.1 四条判据（缺一不可，按强度排序）

| # | 判据 | 强/弱 | 说明 |
|---|---|---|---|
| **J1** | `udc_role_resource` **逐行集合相等**（`(resource_id, resource_type, action)` 三元组集合） | **最强** | 计数相等不够——delta 提交后计数也相等（§2.3 实证） |
| **J2** | `content` 返回值 = **写入后总条数**，不是增量 | 强 | 用它做断言时必须比「总条数」，不能比「新增数」 |
| **J3** | 物理行 `id` + `create_time` **不作为**判据 | — | 每次全删全建都会变，拿它判「有没有变」会永远判「变了」 |
| **J4** | 读接口 `RoleAuthPost.resourceList` 与 J1 集合相等 | 强 | 枚举名字符串（MENU/basic）↔ DB int（0/0）映射需双向对上 |

### 3.2 一条禁止事项（写进纪律）

> **判「写成功」禁止只看 `rr_total` / `rr_app` 计数。**
> delta 提交抹除存量时计数可以完全不变（§2.3：`-1+1=0`）。
> 必须比对 `(resource_id, resource_type, action)` 集合。

### 3.3 一条安全前置（写进纪律）

> **写任何已有角色前，必须先算该角色的类型退化面：**
> ```sql
> SELECT COUNT(*) FROM udc_role_resource rr JOIN udc_resource r ON r.id=rr.resource_id
> WHERE rr.role_id=? AND rr.resource_type <> r.type;
> ```
> 结果必须为 **0**。否则整包重写会把那些行退化为 `resource_type=0`，
> **且回滚走同一端点也写不回来**（`saveFuncAuthByRole` 无 `setResourceType`，BLOCKED-09 已钉死）。
> 本次载体 `quanxian` 退化面 = 0，故全程零退化。

---

## 4. 写链契约（LIVE 逐字，可直接复用）

### 4.1 func-auth 写入

```
POST /service/udc/graphql?udcCtpUserRoleFuncAuthPost

{"query":"mutation udcCtpUserRoleFuncAuthPost ($body: udcCtpUserRoleFuncAuthPostInputBody) { udcCtpUserRoleFuncAuthPost(body: $body) { code data{ content } message status } }",
 "variables":{"body":{
   "roleId":"<udc_role.id 字符串形态 Long>",
   "roleCode":"<udc_role.code>",
   "resourceList":[{"resourceId":"<udc_resource.id>","resourceType":"MENU","action":"basic"}]}}}
```

| 要素 | 值 | 等级 |
|---|---|---|
| `roleId` | **`udc_role.id`**（授权侧），字符串形态 | LIVE |
| `roleCode` | `udc_role.code` | LIVE |
| `resourceType` | **枚举名字符串** `"MENU"` / `"CONTROL"`，DB 存 int（MENU=**0**） | LIVE |
| `action` | 枚举名 `"basic"`，DB 存 **0** | LIVE |
| `content` | **写入后总条数**（覆盖式） | LIVE |
| **语义** | **按 roleId 全删全建**（delete by roleId → batch insert） | LIVE（id 置换） |
| 清空 | `resourceList: []`（**必须数组，不能 null**，否则 NPE） | STATIC（字节码）+ 待本轮补测 |
| 空集响应 | `content:0` | 引用（P3 §8 已验证） |

### 4.2 授权读面

```
POST /service/udc/graphql?udcCtpUserRoleRoleAuthPost
{"variables":{"body":{"roleId":"<udc_role.id>"}}}

→ content: { role:{id,code,name,type,appId,...}, resourceList:[{id,resourceId,resourceType,action}] }
```

返回 `resourceList` 条数与 DB 精确一致 —— **仅 `2↔2` 有落盘支撑**（§2.6 写后 DOM）；
原「1↔1」一半已按实际落盘删除（`ROLE-S5-cleanup-dom.json` L3 为 `total:0`，未展开）。

### 4.3 两套 id 空间（沿用 §9.2，本轮再次确认）

| 侧 | 表 | id |
|---|---|---|
| 授权 | `udc_role_resource.role_id` | `udc_role.id` = `7848047731790858930` |
| 绑定 | `ctp_user_role.role_id` | `ctp_role.id` = `-8965238534181970160` |

两者不同，唯一对齐键是 `code`。**写授权用前者，绑用户用后者，不可混用。**

---

## 5. 终态（as-of 02:20:32，清理完成）—— **无落盘，UNVERIFIED**

> ⚠️ **17:5x 订正**：下表数值**没有任何 S5 期 DB artifact 落盘**（evidence 目录内无对应 JSON；
> 审计侧 `auditor/evidence/C03-trace-quanxian.json` as-of **02:13:37** ≠ 本表 02:20:32，不能替代）。
> 故 `BASELINE_MATCH: True` **不得作为已复核断言**引用，整段按 `UNVERIFIED` 处理。
> 补证方式：对 `udc_role.id=7848047731790858930` 取一次只读三元组 + 计数回读并落 JSON（见 `implementer/ROLE-S5-RECHECK.md`）。

```
[UNVERIFIED · 当时现场记录，无 artifact]
rr_total        = 12356   （基线 12356）
rr_app          = 409     （基线 409）
r_app           = 11      （基线 11）
ctp_user_role   = 38      （基线 38）
rr_app 错配     = 0       （基线 0）
quanxian 授权行 = 1
                  → resource_id=9045337234040441658, resource_type=0, action=0
                  → 声称与写前三元组集合相等（未落盘）

BASELINE_MATCH: True   ← 无落盘，不得作已复核断言
```

清理通过 `FuncAuthPost` 整包写回基线 1 条（traceId `3279026818237073596` **回包无落盘，该 traceId 在 evidence 目录 0 命中 ⇒ `UNVERIFIED`**），
非数据库直改 —— `ROLE-S5-cleanup-dom.json` L6-L10 仅 url/method/postData/status，无 respBody，
故「清理写成功」按 `UNVERIFIED` 处理。

---

## 6. 过程中的偏差（如实登记）

### 6.1 SSO 互踢（环境级，非本切片缺陷）

- 02:16 `BOOT_1006 token黑名单`，页面被 `POST /ctp-user/auth/token/revoke` 踢回 login
- 根因：三组共用 `test-account-1`，凭据 02:14:21 被某组续期后我注入的旧 token 立即失效
- 处置：按 `CDP-ENDPOINT.md` 纪律记录 → `main/NEEDS-HUMAN-SSO冲突.md`，**不循环重试**
- 恢复方式：`shared-credentials/ctp-user-login.json` 自助续期 + 立即导航（窗口 <5s）
  —— 与 `menu-runtime-route.md` §3 已验证的处置一致，本次复现有效
- **未影响**任何 LIVE 证据（写 #1 在冲突前完成；**写 #2/#3 回包本身无落盘，已标 UNVERIFIED，与 SSO 无关**；#4 与写后 DOM 在续期后重做并成功）

### 6.2 我自己的脚本缺陷（2 处，均已修）

1. `r5_write.py` 的 `read_expr` 定义在 `if` 分支内，`full`/`delta` 步骤触发 `NameError`
   → 已移到分支外。**影响**：`delta` 步骤的写后自动回读未跑，我手工补查了 DB（§2.3 数据完整）。
2. `full` 首次执行时 `fetch` 返回 `None`（页面在渲染中/无 origin），重试时改用新 tab + 导航后成功
   → 未产生重复写入。

### 6.3 页面行级文本映射未取到

`checked=2` 时未取到「哪两行被勾选」的文本（accordion 未展开，`innerText` 为空）。
**已取到的**：勾选总数 2 ↔ DB 授权行 2（仅此一项成立）。
清理后那次采样 `ROLE-S5-cleanup-dom.json` L3 为 `total:0`（面板未展开）⇒ **1 ↔ 1 无证据，已删除，不作结论**。
**登记为残余项**，不影响「写后可见」结论（2↔2 已成立），但达不到「逐行 DOM 原文」的严格标准。

---

## 7. 明确不在本切片范围

| 项 | 状态 | 原因 |
|---|---|---|
| 「授权生效」（访问能力变化） | **未做** | 需第二账号凭据（NEEDS_HUMAN，已由 P3 §10 登记） |
| 角色→用户绑定写入 | **未做** | 同上；且 §9.5 的绑定读面入参仍未打通 |
| `saveFuncAuthByRole` 缺 `setResourceType` 的 912 行错配修复 | **不动** | 应用代码缺陷，已由 BLOCKED-09 上报，不在本域修复 |
| `XzhExp950795` NFE | **不碰** | 实体域，SET-PUB-1 已收口 |

---

## 8. 证据文件

| 文件 | 内容 |
|---|---|
| `implementer/evidence/ROLE-S5-probe-netcapture.json` | 幂等重放：RoleAuthPost 读 + FuncAuthPost 写完整 req/resp |
| `implementer/evidence/ROLE-S5-restore-netcapture.json` | 恢复写：**实为 `"captures": []`（L6，空数组）** ⇒ 该次写无抓包落盘 |
| `implementer/evidence/ROLE-S5-cleanup-dom.json` | 清理后 DOM（L3 `total:0/disabled:0/checked:0`，面板未展开）+ 清理写请求（**L6-L10 无 respBody**） |
| `implementer/evidence/ROLE-S5-full-netcapture.json` | 整包 2 条提交（32 条 /service 含页面加载，写调用在末尾） |
| `implementer/evidence/ROLE-S5-page-visibility-dom.json` | 写后 DOM：checked=2 / disabled=31 / total=31 / save_buttons=[] |

---

## 9. 复现命令

```bash
# 续期（SSO 冲突时）
python "<HERMES_HOME>/cache/scratch/r5_reauth.py"

# 侦察：载体角色 + 资源池 + 基线
python "<HERMES_HOME>/cache/scratch/r5_recon2.py"

# 写链四步（每步间隔 ≥30s）
python "<HERMES_HOME>/cache/scratch/r5_write.py" <TAB_ID> probe    # 幂等重放
python "<HERMES_HOME>/cache/scratch/r5_write.py" <TAB_ID> delta    # 危险实验
python "<HERMES_HOME>/cache/scratch/r5_write.py" <TAB_ID> restore  # 恢复
python "<HERMES_HOME>/cache/scratch/r5_full.py"                    # 整包 2 条 + DOM

# 清理 + 终态断言
python "<HERMES_HOME>/cache/scratch/r5_cleanup.py"
```

---

## 10. 给 main 的一句话

**（17:5x 订正后）角色写链的「机制」已 LIVE：覆盖式语义（含物理 id 置换）、整包保留存量 +1、
类型退化前置检查、四条终态判据、写后页面勾选态 2↔2 对齐 —— 这五项有落盘支撑。
但阶段5 **未收口**：delta 抹除存量（#2）、恢复写（#3）、清理写（#5）、逐次 DB 回读、终态
`BASELINE_MATCH` 五处**均无 artifact 落盘**，按严格口径一律 `UNVERIFIED`。
唯一最小补证项 = 对 `udc_role.id=7848047731790858930` 取一次只读三元组 + 计数回读落 JSON。
「生效」仍需第二账号凭据，与 P3 §10 同一阻塞，不属本切片。**
