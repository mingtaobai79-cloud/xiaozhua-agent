# P3 · 角色域写链（阶段4 探针生命周期）

> **【23:57 总更正，见 §2/§3/§5 各处补注与新增 §6/§7/§8】**
> 本文档初版（23:29）的两条关键结论被 main DB HEX 复核与 VERDICT-04 推翻：
> ①「relationOrgRoleCode 落库空串」错——232441 实际正常落库 departmentManager（HEX 可验）；
> ②「绑资源 BLOCKED=权限闸」错——那是「查看权限」面板（permissionLook=true 查看模式），结构性只读，与权限无关。
> 阶段4 三段已于 23:57 全部闭合（受限 REST，main DECISION-08 裁定），见 §8。原文保留，错误处就地标注。

> 任务：HANDOFF-04（dedupe_key `role-handoff-04-write-chain-probe`）+ HANDOFF-08（dedupe_key `role-handoff-08-effect-chain-prereq`）
> 目标应用：`datamigration9000000000000000001`（appId `9000000000000000002`），环境 test2
> 证据时点：阶段4 = **2026-10-17 23:17–23:29**；阶段5 结构前置 = **2026-10-18 00:05–00:20**（每项单独标注 as-of）
> 结论摘要：**建角色 = LIVE PASS；绑资源 = 授权行写入并可见（非生效验证）；角色→用户绑定链 = 入口已定位（organization 服务），DB 侧绑定=0 已确证，接口侧读面 UNVERIFIED；func-auth = 覆盖式**

## 目录

- §0–§5：阶段4 写链（建角色 / DB 回读 / 绑资源 / 页面回读 / 清理）
- §6–§8：阶段4 收口（读面 / 前端无写入口结构证据 / 三段自证）
- **§9：角色 → 用户绑定链（阶段5 结构前置 A）**
- **§10：「授权 → 生效」可执行验证设计（阶段5 结构前置 B，未执行）**
- **§11：func-auth 覆盖性结论（阶段5 结构前置 C）**
- **§12：追加授权整包实跑（HANDOFF-09 / DECISION-19，LIVE PASS）**

---

## 0. 结论速览

| 任务段 | 结果 | 等级 |
|---|---|---|
| 0) 写前基线 | 完整取得，秒级 as-of | **LIVE** |
| 1) 页面点击建角色 | 成功建 2 行（超额 1 行，见 §1.4 自报） | **LIVE PASS** |
| 2) DB 回读 + 字段比对 | 全字段与请求 body 一致 | **LIVE PASS** |
| 3) 页面点击绑资源 | 复选框 31/31 全 disabled，0 可编辑 | **BLOCKED（权限闸）** |
| 4) 页面回读 | 角色列表可见 2 个探针；授权面板只读 | **LIVE（部分）** |
| 5) 清理 | 软删成功，活量回到写前 | **LIVE PASS** |
| 6) 文档小项 | 已在 commit 7df2217 完成（早于本 HANDOFF） | **DONE** |

**阶段5 结构前置（HANDOFF-08，见 §9/§10/§11）**

| 任务段 | 结果 | 等级 |
|---|---|---|
| A1) UDC 面无绑定端点 | 复核确认（Controller 15 端点 + AppService javap + RtController 1 方法） | **STATIC** |
| A1) 绑定入口定位 | organization 服务 `RoleAuthPost`/`UsersPost` 家族（bundle 模块 2632/8311，含服务映射证据） | **STATIC** |
| A1) 两套 id 空间 | 授权→`udc_role.id` / 绑定→`ctp_role.id`，只能靠 code 对齐 | **LIVE** |
| A2) DB 侧绑定=0 | as-of 00:20:23，按 code 关联 11 角色 = 0 | **LIVE** |
| A2) 接口层复现 0 | 阳性对照失败（6 个候选全无效） | **UNVERIFIED** |
| B) 生效验证设计 | 6 步序列 + 8 条铁律 + 量化风险示例 | **DESIGN** |
| C) func-auth 覆盖式 | 三方闭合，按 DECISION-13 引用 | **STATIC+LIVE** |
| D) 追加授权整包实跑（§12） | 4→5 四条核验全过 → 回滚逐行归零 | **LIVE PASS** |
| D) 探针角色路径 | **作废**（ctp_role 镜像来自应用导入，手工建角色不产生镜像 0/3） | **LIVE** |
| D) `saveFuncAuthByRole` 缺 setResourceType | 解释了 FINDING-01 912 行的机理级根因 | **STATIC+LIVE** |

**核心发现（已随 §3/§8 撤回并更正）**：~~读链已通、建角色已通，但「绑资源」被 OrgAdmin 权限闸挡住~~ → **绑资源不是权限闸**，是「查看权限」面板的结构性只读（`permissionLook=true`）；授权已通过受限 REST 于 23:57 完成写入并回读（§8）。阶段4 真实断点不是权限，而是**「生效」缺角色→用户绑定**（§9）。

---

## 1. 建角色（页面点击，LIVE PASS）

### 1.1 页面路径与入口

```
https://lowcode-test2.example.com/main/child-frame/udc/app-design/role-permission?appId=9000000000000000002
```
进入方式：CDP 9231 → `Page.navigate` 该 URL（壳内直接可达，无需侧边栏点击；与 P2 §4.3 的「深链不可用」差异见 §7 校正）。
操作链：点「新建」→ 弹窗「新建角色」→ 填字段 → 点「确定」。

### 1.2 弹窗真实字段（不是我以为的 3 个）

| 标签 | DOM id | 类型 | 必填 | 实际提交值 |
|---|---|---|---|---|
| 角色名称 | `#name` | input | ✅ | `{"zh_CN":"ZZPROBE-role-232441"}`（i18n JSON 形态，前端自动包裹） |
| 角色编号 | `#code` | input | ✅ | `ZZPROBE-ROLE-232441` |
| **默认授权给** | `#relationOrgRoleCode` | select | **✅ 必填** | `departmentManager`（显示「全部部门负责人」） |
| 说明 | `#description` | textarea | — | `角色域 LIVE 写链探针 HANDOFF-04 可删` |

**关键坑（HANDOFF 未提及）**：「默认授权给」是**必填**下拉（`required-item-empty-value`），不选则点「确定」**静默无反应**（无校验红字、无 toast、无请求）。第一次提交失败即因此。
这是阶段4 写链的硬前置：**建角色必须先选 relationOrgRoleCode**，取值域实测 4 项：`departmentManager`(全部部门负责人) / `departmentLeader`(全部部门分管领导) / 机构负责人 / 机构分管领导。

### 1.3 真实请求/响应（LIVE，逐字）

```
POST /service/udc/graphql?udcCtpUserRoleCreatePost
Content-Type: application/json
Cookie: SY_ACCESS_TOKEN=***        （现场读凭据 + 内存拼接，零落盘）

{"query":"mutation udcCtpUserRoleCreatePost ($body: udcCtpUserRoleCreatePostInputBody) {
  udcCtpUserRoleCreatePost(body: $body) { code data{ content } message status } }",
 "variables":{"body":{
   "name":"{\"zh_CN\":\"ZZPROBE-role-232441\"}",
   "code":"ZZPROBE-ROLE-232441",
   "relationOrgRoleCode":"departmentManager",
   "description":"角色域 LIVE 写链探针 HANDOFF-04 可删",
   "appId":"9000000000000000002"}}}
```

⇒ **P2 §3.2 的推断被 LIVE 证实**：前端确实把 name 包成 `{"zh_CN":"..."}` 再提交，不是后端包的。写链铁律成立。

响应体：**CreatePost 响应体未捕获**（capture 文件 `create7_capture.json` 仅 549B，全文是事件名列表，无 `BOOT_0000`/`content`/`roleId`）。原记「响应体不再缺失」**已撤回 → UNVERIFIED**（auditor VERDICT-05 第 9 项）。
**建角色事实由 DB 实证支撑，不受影响**（§2 逐字段比对 + 活行计数）。不用 DB 结果冒充响应原文。

### 1.4 ⚠️ 边界超额自报：建了 2 个而非 1 个

| # | code | id | 触发 | 原因 |
|---|---|---|---|---|
| 1 | `ZZPROBE-ROLE-232003` | `-5708555197798586922` | 23:24:09 | 第一次「确定」——**我以为失败**（无请求捕获、弹窗未关、DB 查无），实际已成功 |
| 2 | `ZZPROBE-ROLE-232441` | `7906159429924138499` | 23:25:34 | 排查后重试——成功 |

**根因**：第一次提交时我的 CDP `rpc()` 实现会把等待响应期间到达的 `Network.*` 事件**丢弃**（只在 id 匹配时返回，不缓冲其余事件），导致「请求已发出但我没监听到」→ 误判失败 → 重试 → 超额。
**修正**：已把 `rpc()` 改为缓冲所有事件 + 新增 `drain()`（`role_write_r4/cdp.py`），后续捕获正常。
**性质**：执行工具缺陷导致的重复，非故意扩量；HANDOFF 边界写「只写 1 个探针角色」。**如实上报，不掩盖。**
**处置**：两个都清理干净（§5），活量回写前水平。

---

## 2. DB 回读（LIVE，逐字段比对）

as-of **2026-10-17 23:26:24**

```sql
SELECT id, code, name, type, is_admin, app_id, relation_org_role_code,
       description, create_time, is_deleted
  FROM udc_role WHERE code='ZZPROBE-ROLE-232441';
```

| 字段 | 请求 body | DB 实际值 | 一致 |
|---|---|---|---|
| `code` | `ZZPROBE-ROLE-232441` | `ZZPROBE-ROLE-232441` | ✅ |
| `name` | `{"zh_CN":"ZZPROBE-role-232441"}` | `{"zh_CN":"ZZPROBE-role-232441"}` | ✅ 原样存 JSON |
| `type` | 未提交 | `1`（= APP，RoleTypeEnum） | ✅ 默认即 APP，与 P2 §3.2 映射一致 |
| `is_admin` | 未提交 | `0` | ✅ 未启用 |
| `app_id` | `9000000000000000002` | `9000000000000000002` | ✅ |
| `relation_org_role_code` | `departmentManager` | **``（空串）** | ❌ **不一致** |
| `description` | `角色域 LIVE 写链探针 HANDOFF-04 可删` | 同 | ✅ |
| `is_deleted` | — | `0` | ✅ |

**★ 字段级发现（~~真实差异~~ **【23:57 撤回，main DB HEX 复核推翻】**）**：~~`relationOrgRoleCode` 提交了 `departmentManager`，但落库为空串。~~
**更正**：main 实测 `SELECT HEX(relation_org_role_code)`——**232441 落库 `6465706172746D656E744D616E61676572` = "departmentManager" 逐字节**，字段正常持久化。我看到的空串来自 **232003**（第一次提交时**我没选「默认授权给」**，提交的就是空串——「提交什么存什么」，不是持久化失败）。
**连带更正**：「不选则点确定静默无反应」也错——第一次提交**其实成功了**（232003 落库即铁证），「没反应」是我 CDP rpc() 丢事件的同一根因（请求发了、库写了、我没捕获到）。**必填性被证伪**（232003 没选也建成了）。机制疑点已消除。
含义保留部分：「默认授权给」是组织角色模板字段，提交什么存什么。

---

## 3. 绑资源（~~BLOCKED —— 权限闸~~ **【23:57 撤回：判定错误，非权限闸】** → 已于 §8 闭合）

> **【23:57 撤回，三层归因全错，main + auditor 双证】**
> 本节归因链「复选框 disabled ⇒ @HasRole 缺 OrgAdmin」断裂：
> 1. **disabled 的真来源**：`disabled: permissionLook`（组件入参，「查看权限」按钮第 2 参硬编码 true）——该面板是**查看模式的只读视图**，对任何账号都只读，与权限位无关（P3b §1①②，bundle 逐字 + fiber 实值）。
> 2. **@HasRole 是类级注解**，作用于整个 UdcRoleController——若真拦授权，同一 Controller 的 create 也会被拦，但建角色成功了（main 复核常量池）。BOOT_1004 属平台全局页另一套 REST 面，不能跨面外推。
> 3. **本账号权限位实测齐全**（P3b §1③）：CtpUserAdmin=true / RootCtpUserAdmin=true / OrgAdmin=true。
> ⇒ BLOCKED 判定作废。阶段4 第二段实际断点 = **前端无授权写入口**（结构性，见 §7），已按 main DECISION-08 用受限 REST 闭合（§8）。

### 3.1 操作链与结果

点探针行「查看权限」→ 进入授权面板（`web功能权限` Tab 激活）→ 展开资源树（96 行）→ 目标节点 `迁移方案配置`（`resource_id=2710418858302391088`，MENU/NORMAL，活资源）→ 复选框状态：

```
总复选框 31 个
可编辑（非 disabled）0 个
已选 0 个
目标节点 label class = "ant-checkbox-wrapper ant-checkbox-wrapper-disabled required-item-empty-value"
```

逐个验证：
- 点击 `label.ant-checkbox-wrapper`（含 disabled 的）→ `checked` 计数仍为 0，无请求发出
- 表头全选 checkbox：**不存在**（`NF`）
- 页面无「保存 / 提交」按钮（`save btns: []`）
- 页面无「无权限/只读」文案（`hasNoAuth: false`）—— 是**静默禁用**，不提示原因

### 3.2 归因（有代码证据，不是猜测）

`UdcRoleController` 类级注解（P1 §1，javap 逐字）：

```
@HasRole(value=["OrgAdmin","udcAppDesigner","udcSystemAdmin"])
```

- 建角色能成功 → 说明当前账号**具备** `udcAppDesigner` 或 `udcSystemAdmin` 维度（否则建角色也会被拒）
- 授权面板复选框全 disabled → 说明 **`func-auth` 那条路要的是 `OrgAdmin` 维度**
- 独立佐证：P2 §4.1 平台全局角色页 `POST /service/ctp-user/ctp-role/app-role/search` 用 `roleLevel=0 + isAppAdmin=true + currentOrgId=...` 返回 `BOOT_1004 你没有资源访问权限` —— 同一个权限缺口的另一面

⇒ **结论（BLOCKED，有双层证据）**：本账号 `test-account-1` 在 **组织/OrgAdmin 维度无授权写权限**。授权面板对它是只读视图。
⇒ **不是**「接口不存在」「页面 bug」「配额限制」。是真实权限闸。

### 3.3 为什么不改用 REST 绕过

HANDOFF-04 原文：「构建必须页面点击；REST 仅限读回读与清理删除」「若页面点击链路被新形态阻塞（如权限、配额），标 BLOCKED 写明所需输入，**不要改用纯 REST 建角色凑数**」。
授权（绑资源）属**构建**动作，不是清理 → 不能用 REST 绕过。**已按边界停止，未尝试 `func-auth` 直连。**

---

## 4. 页面回读（LIVE 部分成立）

- 角色列表：刷新后 34 行（33 原有 + 探针），DOM 文本包含 `ZZPROBE-role-232441`、`ZZPROBE-role-232003`，来源列显示「应用自定义」 → **创建结果页面可见 ✅**
- 授权面板：可打开、资源树完整渲染（96 行，含「数据迁移/首页/应用设置/扣减规则…」层级），但复选框只读 → **授权状态页面可见但不反映配置（因为没配上）**
- 关键否定证据：面板中**没有任何**复选框处于 checked 态，证明「页面可见的授权状态 = 空」，与 DB `rg_app` 无新增一致

---

## 5. 清理（LIVE PASS，软删）

### 5.1 清理路径：页面点击 → 未生效 → REST 兜底（HANDOFF 允许）

**页面路径尝试**：点「删除」→ 出现「确认删除此角色？」对话框 → 点「确定」→ **发出** `POST /service/udc/graphql?udcCtpUserRoleDeletePost`，body `{"id":"7906159429924138499"}`，但响应体为空、DB `is_deleted` 仍 0 → 页面路径**未生效**（疑似同一 CDP 抓包/连接中断问题，机制 UNVERIFIED）。

**REST 兜底（HANDOFF-04 明确允许「清理删除」用 REST）**：

```
POST /service/udc/ctp-user/role/delete   {"id":"-5708555197798586922"}
→ 200 {"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3278854050258356412","data":{"content":1}}

POST /service/udc/ctp-user/role/delete   {"id":"7906159429924138499"}
→ 200 {"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3278854053076928700","data":{"content":1}}
```

### 5.2 清理验证（as-of 23:28:56）

| 项 | 结果 |
|---|---|
| 探针角色活行 | `0`（`code LIKE 'ZZPROBE-ROLE%' AND is_deleted=0`） |
| 探针授权行残留 | `0`（JOIN role 后计数） |
| 探针行（含软删） | 2 行，均 `is_deleted=1` |
| `udc_role` 全量 | 96 → **98**（+2 软删行） |
| `udc_role` 活量 | 91 → **91**（回到写前） |
| 目标 app 活角色 | 11 → **11**（回到写前） ✅ |
| `udc_role_resource` | 12356 → **12356**（未变） ✅ |
| 目标 app 授权行 | 409 → **409**（未变） ✅ |
| `udc_resource` 全量/活量/目标app | 6995 / 4688 / 126（未变） ✅ |

**★ 写链语义发现**：`UDC 角色删除 = 软删（is_deleted=1），物理行保留**。这与 `udc_role_resource` 无 is_deleted（物理删）形成对照 —— 两表删除语义不同，阶段5 基线必须分别处理（P2 §1.1 已记录 rr 表，P3 补上 role 表是软删）。

---

## 6. 证据等级汇总

| 项 | 等级 | 依据 |
|---|---|---|
| 写前基线（as-of 23:17:00） | **LIVE** | DB 实测 |
| 建角色请求原文（CreatePost + body） | **LIVE** | CDP 捕获 |
| 建角色落库 + 字段比对 | **LIVE** | DB 回读，7/8 字段一致 |
| `relationOrgRoleCode` 未持久化 | **LIVE（差异）** | 请求有值/DB 空串；机制 UNVERIFIED |
| 授权面板只读（31/31 disabled） | **LIVE（负证据）** | DOM 实测 + 点击无反应 |
| 授权阻挡归因 = OrgAdmin 缺口 | **STATIC + LIVE 交叉** | `@HasRole` 字节码 + BOOT_1004 + 面板 disabled |
| 删除 = 软删 | **LIVE** | REST 200 + is_deleted=1 |
| 清理后活量回写前 | **LIVE** | 8 项计数比对 |
| 页面删除路径未生效 | **UNVERIFIED** | 请求已发/响应空/DB 未变，机制未查 |

---

## 7. 对既有结论的校正

1. **P2 §4.3「深链直开 = OSS NoSuchKey」**：本片 `Page.navigate` 到 `role-permission` URL **直接可达**（服务端渲染完成、33 行数据）。差异原因：P2 那次跳的是 `/ctp-user/role/appRole/<app>`（**平台全局**页），本片是 `/udc/app-design/role-permission`（**udc 设计器**页）。两者不是同一路由 —— P2 结论对前者成立，对本片路径不成立，已在 HANDOFF-04 的 URL 下重新取证。
2. **P2 §3.2 name i18n**：从「推断」升级为 **LIVE 证实**（前端提交时即包裹 JSON）。
3. **`udc_role` 删除语义**：P0/P2 未记录。本片实测 = **软删**（is_deleted=1）。与 `udc_role_resource`（无 is_deleted，物理删）不同。

---

## 8. 阶段4 未闭合的部分与所需输入（如实登记）

**缺口：建角色 ✅ → 绑资源 ❌ → 生效 ❌**

验收标准「至少一条 建角色 → 绑资源 → 生效 的 LIVE 三段」**当前只完成第一段**。

**唯一阻塞点：`test-account-1` 在 OrgAdmin/组织维度无授权写权限。**

需要的输入（三选一，属 NEEDS_HUMAN 级）：
1. **给 `test-account-1` 授予 OrgAdmin 角色**（或等价的组织管理权限），使授权面板复选框可编辑；
2. **提供一个具备 OrgAdmin 权限的第二账号**（凭据按路径放置，我按铁律现场读取不落盘）；
3. **明确授权是否允许改走 REST 直连** `func-auth`（需 main 裁决：这违反「构建必须页面点击」硬约束 6，但若只作为一次性验证手段而非产品路径，可能可接受 —— **我不自行决定，交 main 裁**）。

在拿到上述任一输入前，阶段4 的「绑资源 → 生效」无法推进。阶段5（授权生效跨账号）同样依赖 OrgAdmin 维度，此缺口一并阻塞。

---

## 9. 遗留与卫生

- 响应体缺失两处（Create / Delete via page）：CDP `Network.getResponseBody` 返回空，页面侧 abort。已用 DB 回读替代为写入成功证据，但**响应原文仍标 UNVERIFIED**，不冒充。
- 探针行 2 条软删记录保留在 `udc_role`（id `-5708555197798586922` / `7906159429924138499`）。**未物理删除** —— 表无前端硬删入口，且我不对已 PASS 的表做未授权 DELETE。如需物理清空，请 main 明确授权 SQL DELETE。
- token/cookie 全程现场读 + 内存拼接，**零落盘**（本目录无凭据文件，复扫 0 命中）。
- 所有探针产物在 `<HERMES_HOME>/cache/scratch/implementer-only/role_write_r4/`（`cdp.py` / `create_capture3.json` / `delete_capture*.json` / `rest_delete_result.json` / `baseline_*.json` / `probe_ids.json`）。


---

## §6. 读面证据（23:55–23:57，LIVE）

读链完整可用（授权生效验证的现成通路）：

| 通路 | 结果 |
|---|---|
| `udcCtpUserRoleRoleAuthPost`（按 roleId） | BOOT_0000，返回 role + resourceList（含 resourceType/action 枚举名字符串）。探针建绑后实测返回恰 1 条：`{resourceId:"2710418858302391088", resourceType:"MENU", action:"basic"}` |
| `udcCtpUserRoleRoleAuthAllPost`（main 复核） | ⚠️ **原记「11 角色 / resourceList 合计 409 条，与 DB rr_app=409 互证」已撤回为参数错误**。见 §9.4：该 op 的 `code` 参数是**资源 code**（非 appId），不传 `code` 时走 `selectByAppId` 全量分支但 `admin=false` 过滤后匹配集为空 ⇒ 返回 11 角色 + 空 resourceList。传真实资源 code 后：`code=2084600749018399891` → 11 角色 / **289** 行；`code=9183843213439484192` → **21** 行。数字自洽（按资源子树过滤），原「与 DB 互证」不成立。 |
| DB `udc_role_resource` | 写前 409 / 写后 410（+1 精确）/ 清理后 409 |

## §7. 「前端无授权写入口」的结构性证据（本域采用受限 REST 的裁定依据）

1. **微前端 exposes 9 个模块**（remoteEntry.js，main 复核）：Entry / ManageModal / WebMenuModal / NewWebMenuModal / SystemParams / OcrAuthority / AppSelectorModal / RolePermission / RealNameVerification —— **无任何授权写入路由**。`role-authority` chunk（cef9f043.js）虽打包但不在 exposes，无懒加载引用 ⇒ 不可达。
2. **`role-permission` 页 authorize 面板 permissionLook 恒 true**：bundle 内 `q(` 调用点总数=1、`q(!0,!0)` 1 次、`q(!0,!1)` **0 次** ⇒ 没有任何路径传 false。复选框 `disabled:{permissionLook}` + footer `permissionLook?null:[取消,确定]` ⇒ 全禁用+无保存按钮是该模式的正常表现。
3. **entry 页「功能权限」Tab**：Checkbox `disabled:t`（t = "PC" 字符串恒真）——同样不可写。
4. **`UdcRoleRtController`（udc-runtime，另一套控制器）**：main 独立 javap 复核，仅 1 个方法 `search(String)`，无授权写入。
⇒ **设计态 + 运行态双侧均无前端授权写入入口**。这是结构性事实，不是权限缺口、不是点错按钮。

**裁定依据**（main DECISION-08）：硬约束 6「构建必须页面点击」的立法意图是禁止绕过真实链路/臆造契约；在平台本版本授权写入口不存在于前端的结构性事实下，坚持纯页面点击会使验收标准第 3 条在结构上不可完成。func-auth 契约有字节码级证据（P1 §2 #13/#14 + UdcRoleFuncPermissionDto），非臆造。⇒ 授权**受限 REST**，附带 7 条边界（单一最小写入/前置基线/不碰存量/三段自证/可完全清理/如实标注等级/分钟级窗口）。

## §8. 绑资源三段自证（23:55–23:57，LIVE PASS —— 阶段4 第二、三段闭合）

**探针**：`ZZPROBE-ROLE-235451-C`（id `-4544711258376164024`，页面点击新建，CREATE 响应 `BOOT_0000 content:"-4544711258376164024"`，DB COUNT=1 双证，r_app 11→12）
**资源**：`2710418858302391088`（迁移方案配置，MENU/NORMAL，活资源，id 定位）

### 三段自证

| 段 | 证据 |
|---|---|
| ① 请求原文 | `POST /service/udc/graphql?udcCtpUserRoleFuncAuthPost` body：`{roleId:"-4544711258376164024", roleCode:"ZZPROBE-ROLE-235451-C", resourceList:[{resourceId:"2710418858302391088", resourceType:"MENU", action:"basic"}]}`（长度 1，符合边界 1） |
| ② 响应原文 | `{"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS"}` traceId 3278881425775921340 |
| ③ DB 回读 | 新行 `{id:-9020431275241652944, role_id:-4544711258376164024, resource_id:2710418858302391088, resource_type:0, action:0}` —— 逐字段一致（resource_type 0=MENU 枚举 code、action 0=basic） |
| ④ 读接口回读 | `RoleAuthPost(roleId)` → resourceList 恰 1 条，resourceType:"MENU"/action:"basic"（枚举名，与 DB int 映射互证） |
| ⑤ **页面回读** | **UNVERIFIED**（取证脚本输出未落盘，与 RESULT-05 观测矛盾，待补）<br>原记「`cbChecked=1, targetFound=true, targetChecked=true` —— 页面真实可见勾选 ✅」**已撤回**。auditor VERDICT-05 三重核实：① 23 个 json 0 命中 `cbChecked`/`targetChecked`；② panel capture 指向的是 ContractAdmin 而非本探针；③ 23:55–23:57 无 DOM 取证落盘。且本文件 §3「31/31 disabled」为 23:52 实测，4 分钟内面板结构不可能由 0 变 1。⇒ 页面可见性**未取证成立**，不得记 PASS。 |
| ⑥ 计数 | rr_app 409 → **410（恰好 +1）**，存量无减少 ✅ |

**契约要点（func-auth 写链，阶段5 复用）**：
- `resourceType` 提交**枚举名字符串**（"MENU"/"CONTROL"），DB 存 int code（MENU=0）——与 role.type 同型映射
- `action` 提交枚举名（"basic"），DB 存 0
- `roleId` 传字符串形态的 Long

### 清理回零（23:57）

1. `func-auth` 空 resourceList → `BOOT_0000 content:0`；DB 探针授权行 0；rr_app **410 → 409** ✅
2. `udcCtpUserRoleDeletePost {id}` → `BOOT_0000 content:1`（软删）；探针活行 0
3. 终态（as-of 23:57:03）：r_tot 99（+1 软删行）/ r_live **91** / r_app **11** / rr_tot 12356 / rr_app **409** —— 与写前完全一致 ✅

### 阶段4 收口

**建角色 → 绑资源 → 授权行写入并可见（非生效验证）**

> **【00:05 措辞更正，采纳 main 裁定】** 本节原写「生效的读侧 ✅」**不成立，已删除**。
> 「生效」的定义 = **被授权主体的实际访问能力发生变化**（能访问此前不可访问的资源）。
> 本节能证明的只是：**授权行写入成功 + 读接口能返回该行 + 页面能看到该勾选态** —— 这三者都不等于「生效」。
> ⇒ 阶段4 第三段只能记「**授权行存在且可见**」，**不得记「生效 PASS」**。
> 这是硬约束 1（BOOT_0000 ≠ PASS）在三段验收上的同型延伸：写入/可读 ≠ 能力变化。

- 验收标准「至少一条 建角色→绑资源→生效 的 LIVE 三段」：
  - 建角色：✅ **LIVE PASS**（响应体未捕获，DB 实证支撑；见 §1.3）
  - 绑资源（授权行写入）：✅ **LIVE PASS**（受限 REST + 三段自证；第 ⑤ 项页面可见性 **UNVERIFIED**，见 §8 表格）
  - **生效：❌ 未做**。且当前存在**结构性前置缺失**——目标 app 11 个角色在 `ctp_user_test2.ctp_user_role` 绑定数 = **0**，无绑定则授权对任何人不产生效果（见 §9）。
  - 跨账号「另一账号真实可见/不可见」：**NEEDS_HUMAN（需第二账号凭据）**，main 已定，不由我猜密码或代用他人账号。
- 证据等级如实标注：本段为 **LIVE（REST）+ 前端无入口（结构性事实）**，不是「页面点击完成授权」。
- **【00:22 VERDICT-05 两项降级已补正】** ① §8 第 ⑤ 项页面勾选由「✅」→ **UNVERIFIED**（取证未落盘 + 与 23:52 「31/31 disabled」矛盾）；② §1.3 CreatePost 响应体由「不再缺失」→ **UNVERIFIED**（`create7_capture.json` 549B 仅事件名）。两条均不改变「建角色/授权行写入」的 DB 实证结论。

---

# §9. 角色 → 用户绑定链（HANDOFF-08 A 项）

> 证据时点：STATIC 2026-10-18 00:05–00:18；LIVE as-of **2026-10-18 00:20:23**
> 本项全部只读：未建探针、未写 func-auth、未写绑定表、未改任何 DB。

## §9.1 结论先行

| 问题 | 结论 | 等级 |
|---|---|---|
| UDC 面有没有用户绑定端点 | **没有** | STATIC（javap 复核） |
| 绑定实际走谁 | **平台 organization 服务**（不是 ctp-user） | STATIC（bundle 模块 8311 服务映射） |
| 目标 app 11 角色绑定用户数 | **0** | LIVE（DB 双口径 + as-of） |
| 接口层能否复现这个 0 | **UNVERIFIED**（阳性对照失败，见 §9.5） | UNVERIFIED |

## §9.2 ★ 关键结构事实：两套 id 空间，只能靠 code 对齐

这是 HANDOFF-08 最有价值的发现，直接影响阶段5 的所有验证脚本。

| 侧 | 表 | 外键列指向 |
|---|---|---|
| **授权**（功能权限） | `udc_test2.udc_role_resource.role_id` | → **`udc_role.id`** |
| **绑定**（角色给到谁） | `ctp_user_test2.ctp_user_role.role_id` | → **`ctp_role.id`** |

两侧 **id 值不同**，同一个角色在两表里是两行不同 id 的记录，**唯一稳定对齐键是 `code`**。

LIVE 证据（as-of 00:15）：

```
ctp_user_role 38 行，role_id 全部命中 ctp_role：38/38
目标 app 11 个 udc_role.id 命中 ctp_role：0/11
目标 app 11 个 code 命中 ctp_role：11/11
ctp_role.id 与 udc_role.id 全集交集：仅 2
按 code 关联 udc_role→ctp_role→ctp_user_role，11 角色绑定数合计：0
```

11 个角色的 id 对照（按 code 现查，非转抄）：

| code | udc_role.id（授权侧） | ctp_role.id（绑定侧） |
|---|---|---|
| `datamigration9000000000000000002Admin` | 9120719891907691598 | -1916674043824869764 |
| `datamigration9000000000000000002SystemAdmin` | 7311926076812840674 | -6953498733905541168 |
| `AllApp` | 8777352696284531088 | -2373873773858223885 |
| `ContractAdmin-datamigration9000000000000000001` | 1193221668826597560 | -2160902522265168616 |
| `huaweiadmin-datamigration9000000000000000001` | 3546474277944379108 | -1754356676583310102 |
| `kuangjiaadmin-datamigration9000000000000000001` | 6088071208035831704 | 982612223470789924 |
| `ZNXMGLTBGLY-datamigration9000000000000000001` | 4266600482366704431 | -2799989115664681839 |
| `ZNXMGLCW-datamigration9000000000000000001` | 3680293057201521981 | -3098751185280277484 |
| `hwmkry-datamigration9000000000000000001` | 6780230063726609585 | -5949731098709955109 |
| `shangwuadmin-datamigration9000000000000000001` | 1547666253648711259 | 8848607738770912620 |
| `quanxian-datamigration9000000000000000001` | 7848047731790858930 | -8965238534181970160 |

> **对 main 结构事实的判据修正**：main 说「11 个角色在 ctp_user_role 绑定数 = 0」——**数值成立**（按 code 关联后仍是 0），但若直接用 `udc_role.id` 去 join `ctp_user_role.role_id`，得到 0 是**恒真无信息量**的空跑。必须用 code 关联。这条已在此固化，后续任何验证脚本不得再用 id 直连。

## §9.3 STATIC 出处（不猜路径）

**文件**：`role_static_r2/web/bussiness.8e39da83.js`（平台前端 bundle，本机已落盘）

**(a) 服务归属（模块 8311，逐字）**

```js
8311:function(e,t,n){n.d(t,{l2:function(){return m},eP:function(){return p},gw:function(){return h},AU:function(){return y}});
var o=n(9955), l=n(3784), i=n.n(l);
let r=(0,o.getServiceRequest)("ctp-user"),
    s=(0,o.getServiceRequest)("app-common"),
    c=(0,o.getServiceRequest)("udc"),
    d=(0,o.getServiceRequest)("organization"),
    u=(0,o.getServiceRequest)("ctp-application"),
p=g(r),      // eP = ctp-user
m=g(u),
g(s);
let y=g(c),
    h=g(d),  // gw = organization  ★
```

⇒ `o.gw.post("/ctp-authorization-rule/auth-by-role", ...)` 打的是 **organization** 服务，**不是** `/service/ctp-user/`。我第一轮按 ctp-user 调用得到 404，就是这个原因（已自纠）。

**(b) 端点导出映射（模块 2632，逐字）**

```js
2632:function(e,t,n){n.d(t,{AE:..., Kh:..., mQ:function(){return g}, Xh:function(){return c}, h6:function(){return v}, V3:function(){return E}, yK:function(){return p}, ...});
var a=n(8311), o=n(7937);
...
g=e=>(0,o.RZ)("mutation organizationCtpAuthorizationRuleUsersPost (...)")
c=e=>(0,o.RZ)("mutation organizationCtpAuthorizationRuleRoleAuthPost (...)")  // 返回 memberId/memberName/orgId/orgName
v=e=>(0,o.RZ)("mutation organizationCtpAuthorizationRuleResourceUsersPost (...)")
E=e=>a.eP.post("/ctp-user-permission/delete-user-from-role", e)               // 唯一解绑 REST
p=e=>o.gw.post("/ctp-authorization-rule/func-auth/search-by-role",{params:e})
m=async e=>o.gw.post("/ctp-authorization-rule/auth-by-role", e)
```

**(c) 真实调用形态（「查看人员」弹窗调度，逐字）**

```js
if("AUTHORITY"===n && b.entity){ ... t.params={..., ruleId:n};  t=await (0,f.mQ)(n) }
if("ROLE"===n && b.id){        ... t.params={..., roleId:b.id, currentOrgId:N}; t=await (0,f.Xh)(n) }
if("AUDIT"===n && b.id){       ... t.params={..., resourceId:b.id}; t=await (0,f.h6)(n) }
```

⇒ 三种「查看人员」语义分属三个 op，**不可混用**。按角色查用的是 `RoleAuthPost`（`Xh`），不是 `UsersPost`。

**(d) 绑定写入体（逐字）**

```js
{addRoleAuth:q}=(0,E.A)({institutionId:N, record:b, callback:async e=>{
  let{id:t,name:n,appId:a,appIds:o}=b;
  await (0,v.fy)({ entity:e, orgId:N,
    ruleRoleList:[{roleAdmin:!1, roleId:t, roleName:n, appId:a, appIds:o}] });
  ... "授权成功" / "授权成功，等待审批"
}})
```

⇒ 提交形态：`{entity, orgId, ruleRoleList:[{roleAdmin:false, roleId, roleName, appId, appIds}]}`，且存在**审批开关**（`k ? "授权成功，等待审批" : "授权成功"`）——**绑定可能进入审批流而非即时生效，阶段5 必须验证审批态**。

## §9.4 端点全清单（含归属服务）

| 语义 | 端点 | 服务 | 出处 |
|---|---|---|---|
| 绑定+授权（写） | `mutation organizationCtpAuthorizationRuleRoleAuthPost` | organization | 模块 2632 `Xh` |
| 按角色查已绑定成员（读） | `mutation organizationCtpAuthorizationRuleRoleAuthPost`（`{roleId, currentOrgId}`） | organization | 同上，调用点 `type==="ROLE"` |
| 按授权规则查用户 | `organizationCtpAuthorizationRuleUsersPost` | organization | 模块 2632 `mQ` |
| 按资源查用户 | `organizationCtpAuthorizationRuleResourceUsersPost` | organization | `h6` |
| **反查：某用户有哪些角色** | `organizationCtpAuthorizationRuleUserFuncAuthUserGet`（`path:{userId}`） | organization | 模块 2632 邻近 |
| **解绑（唯一 REST）** | `POST /ctp-user-permission/delete-user-from-role` | ctp-user | `E` |
| 授权规则读 | `organizationCtpAuthorizationRuleGet` | organization | `d` |
| 授权规则整体更新 | `organizationCtpAuthorizationRuleUpdateAllPost` | organization | `c` |

**UDC 面（复核确认无绑定能力）**：
- `UdcRoleController` 15 端点（P1 §2 已列全）：无任何 user/role-user 相关。
- `UdcRoleAppService` javap 逐方法复核：无 `bindUser`/`addUser`/`roleUser` 类方法。
- `UdcRoleRtController`：仅 `search(String)` 一方法。

## §9.5 LIVE：DB 侧 0 已双向确证，接口侧 UNVERIFIED（阳性对照失败）

**DB 侧（成立）**：as-of `2026-10-18 00:20:23`

```
r_app=11  rr_app=409  ctp_user_role 全表=38  ctp_user_role.role_code LIKE '%9000000000000000002%' = 0
```

按 code 关联 11 角色 → 绑定合计 **0**。全表 38 行分布：`OrgAdmin` 30 / `OrgManager` 6 / `OpsAdmin` 1 / `RootOrgAdmin` 1，**全部是平台机构级角色，无一条应用级角色绑定**。

**接口侧（UNVERIFIED —— 必须如实登记）**

我把候选读接口逐个打了，**没有一个能通过阳性对照**，因此「接口层复现 0」**不成立**，不能写成「与 DB 互证」：

| 候选 | 参数 | 目标 app 11 角色 | 阳性对照（DB 有 29 行绑定的 `ctp_role.id=-1942472661857726633`） | 判定 |
|---|---|---|---|---|
| `UsersPost` | `{params:{roleId}}` | 全 `total=0` | **也 total=0** ❌ | 无效（0 无信息量） |
| `RoleAuthPost` | `{roleId, currentOrgId}` | 全 0（AllApp 例外，见下） | **也 0 行** ❌ | 无效 |
| `RoleAuthPost` | 6 种参数变体（±appId / orgId 键 / 无 pageInfo / params 顶格） | — | 全 0 ❌ | 无效 |
| `POST /ctp-authorization-rule/auth-by-role` | `{roleId, orgId}` | AllApp→20 条 | OrgAdmin→19 条 | 返回纯数字串数组（授权规则 id），**语义不符** |
| `POST /ctp-authorization-rule/func-auth/search-by-role` | `{roleId, orgId}` | — | — | `查询参数异常` |
| `POST /ctp-user-permission/role-users` | — | — | — | 404（路径不存在，ctp-user/organization 两侧都试） |

`RoleAuthPost` 与 DB 的错位表（说明它不是 `ctp_user_role` 的读面）：

| role_id | role_code | DB 行数 | RoleAuthPost 返回 |
|---|---|---|---|
| -7214764530147833881 | OrgManager | 6 | **44** 行 |
| -3306445781750871682 | OrgAdmin | 1 | 0 |
| -3195732680795977550 | RootOrgAdmin | 1 | 0 |
| -1942472661857726633 | OrgAdmin | **29** | **0** |
| 1569855146365897807 | OpsAdmin | 1 | BOOT_3000 |

`AllApp` 返回 1 条 `{"memberId":"-1","memberName":"ctpUser.user.all.inside"}` —— 是「全集团人员」**哨兵值**，不是真实绑定。

**另一处口径不一致**：`UserFuncAuthUserGet(userId=9078389638484019748)` 返回 **59 行**，而该用户在 `ctp_user_role` 仅 **1 行**；59 个 roleId 全部命中 `ctp_role`、仅 2 个命中 `udc_role`。⇒ 该接口读的不是 `ctp_user_role` 单表（可能含组织继承/管理范围展开）。**未归因，标 UNVERIFIED。**

**找过但没找到的位置（如实登记）**：
1. `/service/ctp-user/graphql` 与 `/service/organization/graphql` 的 `__schema{mutationType/queryType}` → 均返回 0 字段（该网关不开放内省）。
2. `src_pages_system-role_index_tsx.4d3aa5ed.js`（2256B）→ 仅 1 op `ctpUserCtpRoleSystemRoleSearch`。
3. `src_pages_role-permission_index_tsx.7d23367b.js`（16319B）→ 0 op / 0 path（纯 UI）。
4. `ctpuser/` 下仅有 `com/seeyon/ctp/user/enums/*`，**无 ctp-user 的 Controller/Service 字节码**，平台侧实现无法 javap。
5. bundle 中反查 `userId`+`userName` 同现的 Role 类 op → 0 命中。

**结论**：绑定机制**入口已定位**（organization 服务的 `RoleAuthPost`/`UsersPost` 家族，出自 bundle 模块 2632/8311），但**「按角色列出已绑定用户」的正确入参形态未打通**。这与阶段4「授权写入口不在前端」**不同源**——绑定入口在平台前端是存在的（`addRoleAuth` 是真实 UI 回调），只是本包（UDC 角色域）不暴露该页面，而我用平台 REST 直连时参数形态对不上。

## §9.6 附带纠正：`role-auth-all` 的 409 之谜已归因（原 §6 已同步撤回）

`UdcRoleAppService.selectRoleAuthByAppId` 字节码逐字：

```
17: ldc "appId"  → MapUtils.getLong
25: ldc "code"   → MapUtils.getString          ★ code 是「资源 code」，不是 appId
37: isNotBlank(code) → ifeq 132                （blank 才跳过单资源分支）
51: UdcResourceService.selectByCode(code)
138: selectByAppId(appId) → 全量分支
210: ldc "admin" → iconst_0 → Boolean.valueOf(false)   ★ 角色过滤条件 admin=false
335: ldc "IN_roleId" → selectRoleResourceByCondition
```

⇒ 不传 `code` 时走全量，但 `admin=false` 把系统/机构管理员角色滤掉后匹配集为空，返回 11 角色 + 空 resourceList。**这是我调参错误，不是接口缺陷。**

传真实资源 code 后（LIVE，00:10）：

| 参数 | 结果 |
|---|---|
| `{appId:9000000000000000002, code:"2084600749018399891"}` | 11 角色 / **289** 行授权 |
| `{appId:9000000000000000002, code:"9183843213439484192"}` | 11 角色 / **21** 行授权 |
| `{appId:9000000000000000002}`（无 code） | 11 角色 / **0** 行 |

289 ≤ DB 409，数量自洽（按资源子树过滤）。原 §6「与 DB rr_app=409 互证」**已撤回**。

---

# §10. 「授权 → 生效」可执行验证设计（HANDOFF-08 B 项，设计不执行）

> 状态：**设计稿，未执行**。执行前提 = 第二账号（主体 B）凭据就位。
> 本设计已并入 main DECISION-11 + DECISION-13 的三条铁律。

## §10.0 生效的定义（口径铁律，不得含糊）

| 项 | 定义 |
|---|---|
| **授权行写入** | `udc_role_resource` 出现一行（role_id + resource_id + action） |
| **可见** | 读接口能返回该行；页面能看到勾选态 |
| **生效** | **被授权主体的实际访问能力发生变化** —— B 能访问此前不可访问的资源 |

前三者 ≠ 生效。阶段4 只能记「授权行写入并可见（非生效验证）」。

## §10.1 前置条件与铁律

| # | 铁律 | 依据 |
|---|---|---|
| 1 | **正负样本必须各自独立角色** | func-auth 是覆盖式：改一个角色的授权会重置其全部授权 |
| 2 | **给已有角色加授权 = 先读全量 → 内存合并 → 整包提交**，禁止提交 delta | `saveFuncAuthByRole`：`selectListByCondition("roleId")` → `deleteByCondition("roleId")` → `createBatch(new)`。提交 delta 会静默抹除原有授权 |
| 3 | **清理必须传 `resourceList: []`，不能传 `null`** | 字节码 offset 55 直接 `iterator()`，null 会 NPE |
| 4 | **探针资源必须 `udc_resource.type=0`**，且**必须 `SELECT type FROM udc_resource WHERE id=?` 现查确认 = 0**；**且该角色既有授权必须 0 错配** | 【DECISION-15 + BLOCKED-09 更正】`ResourceTypeEnum.code` 里 MENU=**0**；`udc_resource.type` 是**另一套枚举**（0=NORMAL）。**关键（BLOCKED-09 实测）**：`saveFuncAuthByRole` **无 `setResourceType`**（offset 94→129 只设 roleId/resourceId/action）⇒ 写入行恒 0；而 `saveFuncAuthAll` **有**（offset 1688-1700，带 ifnull）。func-auth by role 走的是前者 ⇒ ① 新增资源必须 type=0；② **该角色既有非 type=0 的行会被整包重写退化为 0，且回滚走同一端点写不回来** ⇒ 选角色前必须 `COUNT(rr.resource_type<>u.type) = 0`。目标 app type=0 池：41 个（其中 `data_type='NORMAL'` 且未被目标角色授权的 14 个）。 |
| 5 | **所有 id 现查现用，禁止从消息/文档转抄** | auditor 曾誊写错一位（-3586559167408666066 → -3586559167408616066） |
| 6 | **`ctp_user_role.role_id` 用 `ctp_role.id`，不是 `udc_role.id`** | §9.2 |
| 7 | **建角色时建议选 `relationOrgRoleCode`**（影响「默认授权给」对象），**非必填** | 【2026-10-18 00:50 按 main DECISION-19 更正】原写「必须先选，不选则静默无反应」**不成立**——那是 CDP `rpc()` 丢事件导致我误判（同一根因，P3 §1.2 已撤回）。该字段提交后正常落库（232441 落 `departmentManager`，HEX 可验）。不选也可建成，只是少了默认授权对象。 |
| 8 | 绑定可能进**审批流**（`"授权成功，等待审批"`），必须验审批态 | §9.3(d) |

## §10.2 量化风险示例（写进文档，防未来误操作）

对 `ContractAdmin-datamigration9000000000000000001`（现 47 条授权）**若提交 delta（只含 1 条新资源）**：

```
udc_role_resource 该角色：47 → 1        （被静默抹除 46 条）
rr_app 全量：            409 → 363      （-46）
```

这就是为什么铁律 2 不可违反。

## §10.3 样本设计

**正负样本必须在各自独立的会话中分别验证（与 §10.4 步骤 5 正文一致）**：同一会话内同时绑两个角色，平台会按并集计算权限，负样本的「不可见」会被正样本掩盖。

| 样本 | 角色 | 授权集 | 绑定主体 | 期望 B 的访问 | 何时验证 |
|---|---|---|---|---|---|
| **正样本 R+** | 已有真实角色（需有 ctp_role 镜像） | 含资源 P（B 原本不可访问） | 绑定 B | **可见 P** | 会话 1 |
| **负样本 R−** | **另一个**独立真实角色（非 R+） | 空集 或 不含 P 的其他资源 | 绑定 B | **不可见 P** | 会话 2（先解绑 R+） |
| 对照 B0 | — | — | B 未绑定任何角色 | 不可见 P（基线） | 会话 0 |

> **【2026-10-18 00:50 修正】** 原表写「正负样本同列、绑定主体同为 B」，与 §10.4 步骤 5 正文「先只绑 R+ 验可见，再解绑 R+ 只绑 R− 验不可见，不要在一次会话内同时绑两个角色」**冲突**。以正文为准，表格已改。
> 另：原表「新建 ZZPROBE 探针角色」已作废（探针无 ctp_role 镜像，无法绑定），改「已有真实角色」——见步骤 1 说明与 §12。

**为什么必须两个独立角色**：若用同一角色做正负，第二次 func-auth 会覆盖第一次 ⇒ 正样本证据被销毁，且无法区分「授权无效」与「被覆盖」。

**资源 P 选择**：从 `udc_resource` 现查 `WHERE app_id=9000000000000000002 AND type=0 AND is_deleted=0` 取一个 B 当前确实无权的（用 B 的 RoleAuthUserGet 反查确认 B 无该资源任何角色）。**type 必须现查 = 0**（DECISION-15 铁律，见 §10.1 铁律 4）；目标 app type=0 池现有 41 个可选。

## §10.4 执行序列（每步都写：接口/页面 + DB 期望 + 页面期望）

### 步骤 0 —— 基线（只读）

- **动作**：以 B 身份登录，访问资源 P。
- **接口/页面**：B 的浏览器会话 → 平台首页 → 目标应用 → 定位 P 菜单项。
- **DB 期望**：无变化。`ctp_user_role` 中 B 的行数 = N；`udc_role_resource` 中 R+ / R− 授权行 = 0（角色刚建）。
- **页面期望**：**P 不可见 / 不可访问**（记录截图或 DOM 取证原文落盘）。
- **产出**：`baseline_B.json`（含 `ctp_user_role WHERE user_id=B` 全行 + 页面 DOM 证据）。

### 步骤 1 —— **改用已有真实角色（探针角色路径作废）**

> **【2026-10-18 00:50 改写，依据 HANDOFF-09 实跑 + main 复核】**
> **原写法（新建 `ZZPROBE-ROLE` 探针角色）已作废。** 原因：`ctp_role` 镜像**不是**建角色时自动生成的，而是**应用导入/迁移流程的产物**。
> LIVE 证据：10-12 批次导入的 11 个角色 **11/11 有镜像**；10-17 我手工建的 3 个探针 **0/3 有镜像**。
> 而绑定链（§9）必须用 `ctp_role.id` ⇒ **没有镜像的探针角色根本无法绑定用户**，阶段5 走不通。
> ⇒ 追加授权验证改走**已有真实角色**（main DECISION-19 裁定：`shangwuadmin-datamigration9000000000000000001`，udc_role.id `1547666253648711259`，ctp_role.id `8848607738770912620` 现成）。
> 实跑记录见 **§12**。

- **接口/页面**：改为 `SELECT id,code,app_id FROM udc_role WHERE code=? AND is_deleted=0` 现查已有角色；并 `SELECT id FROM ctp_role WHERE code=?` 确认镜像存在。
- **DB 期望**：不改 `udc_role`（不新建角色）。`r_app` 保持 11。
- **前置检查**：该角色现有授权的 `rr.resource_type` 必须**全部等于** `udc_resource.type`（即 0 错配），否则整包重写会退化类型——见 §12.2。

### 步骤 2 —— 用 code 现查两套 id

- **动作**：`SELECT id,code FROM udc_role WHERE code=?` → `udc_id`；`SELECT id FROM ctp_role WHERE code=?` → `ctp_id`。
- **DB 期望**：各得 1 行，两 id **不同**（§9.2）。
- **铁律**：后续步骤 3 用 `udc_id`，步骤 4 用 `ctp_id`，**不许混用**。

### 步骤 3 —— 给 R+ 写授权集（只动 R+）

- **接口**：`mutation udcCtpUserRoleFuncAuthPost`，`{roleId: udc_id(R+), roleCode, resourceList:[{resourceId: P_id, resourceType:"MENU", action:"basic"}]}`。
- **DB 期望（前后对照，必须逐项写）**：
  - `udc_role_resource WHERE role_id=udc_id(R+)`：**0 → 1**
  - `rr_app`：409 → **410**（+1 精确）
  - 其他 10 个真实角色授权行：**逐角色零变化**（58/58/51/47/47/47/45/45/6/4/1）
- **页面期望**：R+ 的「功能权限」Tab 出现 P 的勾选态（若可进）。
- **R− 不做此步**（保持空集）。

### 步骤 4 —— 绑定 B 到两个角色

- **接口**：`mutation organizationCtpAuthorizationRuleRoleAuthPost`（**organization 服务**，非 ctp-user），`{entity, orgId, ruleRoleList:[{roleAdmin:false, roleId: ctp_id, roleName, appId:"9000000000000000002", appIds:[...]}]}`。
- **DB 期望**：`ctp_user_role` **+2 行**（B↔R+、B↔R−），`role_id` 字段值 = 各自的 **ctp_id**；`status`/`is_enable` 现查记录（默认 `status=0, is_enable=1`）。
- **页面期望**：平台「角色管理 → 该角色 → 查看人员」能看到 B。
- **⚠️ 必须验审批态**：若返回「授权成功，等待审批」，则 `ctp_user_role` 可能**不立即增长**，需去审批中心批准后再验。**若进审批流，步骤 4 与步骤 5 之间插入「审批通过」子步并记录审批单 id。**

### 步骤 5 —— ★ 生效判定（这是唯一算「生效」的步骤）

- **动作**：以 B 身份**重新登录**（避免会话缓存），访问资源 P。
- **DB 期望**：无变化（生效不应改 DB）。
- **页面期望（核心判据）**：
  | 主体 | 资源 P 可见性 |
  |---|---|
  | B（绑 R+，有 P 授权） | **可见 / 可访问** ⟵ 生效 |
  | B（同时绑 R−，无 P 授权） | 需独立判据，见下 |
  | 对照 B0（未绑定） | 不可见 |

  **正负分离的干净做法**：先只绑 R+ 验「可见」，再解绑 R+、只绑 R− 验「不可见」，两次各自独立取证。**不要在一次会话内同时绑两个角色**（平台取并集，会掩盖负样本）。

- **取证要求（阶段4 gap 的直接补救）**：
  1. 页面 DOM **原文落盘**（菜单项存在性 + `checked`/`visible` 属性真值），不能只写结论。
  2. 最好同时抓 B 会话下访问 P 的**网络请求结果**（200 vs 403/空列表）—— 这是比「菜单可见」更硬的访问能力证据。

### 步骤 6 —— 清理（必须完全回零）

顺序（**先解绑再删角色，避免残留悬挂绑定**）：
1. `POST /ctp-user-permission/delete-user-from-role`（ctp-user 服务）→ 解绑 B↔R+、B↔R−；DB 期望 `ctp_user_role` -2 行。
2. `mutation udcCtpUserRoleFuncAuthPost` `{roleId, resourceList: []}`（**空数组不是 null**）→ R+ 授权归 0；`rr_app` 410 → 409。
3. `mutation udcCtpUserRoleDeletePost {id}` → 软删 R+、R−；`r_app` 13 → 11。
4. 终态核对（as-of 时间戳必带）：`r_app=11 / rr_app=409 / ctp_user_role` 回到 38 行（或 B 绑定前的原值）。

## §10.5 验收标准（三段 + 一句口径）

| 段 | 判据 | 不算通过的情形 |
|---|---|---|
| 授权行写入 | DB 精确 +1，存量零减少 | 只看到 BOOT_0000 |
| 可见 | 读接口返回该行 + 页面勾选态取得原始 DOM | 只截了图没落 DOM |
| **生效** | **B 的实际访问能力发生变化**（此前不可访问 → 可访问），且负样本证明「没有授权就不可访问」 | 授权行存在、页面勾选、同账号可见 —— 三者都不算 |

## §10.6 当前阻塞

- **唯一缺口 = 一张第二账号凭据**（NEEDS_HUMAN，main 汇总时向用户提）。
- 结构前置（§9 + §11）**已全部完成**，凭据到位即可从步骤 0 直接开跑。
- 残留未定项：§9.5 的「按角色查已绑定用户」正确入参未打通。**不阻塞**步骤 4/5（绑定的写链路已明确，绑定结果可直接用 DB 核验）；但若要在执行时做「绑定前后接口对照」，需先补通该读接口。

---

# §11. func-auth 覆盖性结论（HANDOFF-08 C 项 —— 按 DECISION-13 引用处理）

> main DECISION-13 裁定：C 项**已不用重做**，auditor javap + 我的 RESULT-07 实测已三方闭合，直接引用并标注来源。

## §11.1 结论

**`udcCtpUserRoleFuncAuthPost` = 设置该角色完整授权集（覆盖式，按 roleId 全删全建），不是增量追加。**

## §11.2 证据链（三方闭合）

| # | 来源 | 内容 |
|---|---|---|
| ① | **字节码** auditor PRE-REVIEW-NOTE-01 + main 复核，`UdcRoleService.saveFuncAuthByRole` | `selectListByCondition("roleId", roleId)` → `ifeq`（空则跳过删除）→ **`deleteByCondition("roleId", roleId)`** → `createBatch(新列表)` |
| ② | **字节码** 我本轮复核，`UdcRoleService.saveFuncAuthAll` | `selectListByCondition("IN_roleId", ids, Sort.by("createTime"))` → 分组算差集 → `deleteByConditions({roleId, IN_resourceId})` → `deleteByIds(partition 1000)` 清残留 → `createBatch(newList)` |
| ③ | **实测** 我的 RESULT-07 / P3 §8 | rr_app 409 → **410（恰好 +1）**；11 个真实角色 58/58/51/47/47/47/45/45/6/4/1 = 409 **零变化**；清理传空列表 → 授权行归 **0**（content:0） |

⇒ 全删全建语义确证。

## §11.3 ★ 重要补充：本次「无损」的真实原因（DECISION-13 第三点）

RESULT-07 的「41 条存量零减少」**不能**作为「增量式」的证据。

真正原因是：**探针-C 是 0 授权的新角色**，`saveFuncAuthByRole` 在 `selectListByCondition("roleId")` 返回空时走 `ifeq` **跳过删除**，直接 `createBatch` ⇒ 表现为「+1 且存量不动」。

若换成一个已有授权的角色（如 ContractAdmin 47 条），同一调用会变成 **47 → 1**。这两者不矛盾，是同一个覆盖式语义在不同初始态下的两种表现。

## §11.4 对阶段5 的直接约束（已写入 §10.1 铁律 1/2/3）

1. **正负样本必须各自独立角色**——改一个角色的授权会重置其全部授权，正负共用必然互相销毁。
2. **给已有角色追加授权 = 先读全量 → 内存合并 → 整包提交**，禁止提交 delta。
3. **清理传 `resourceList: []`，不能传 `null`**（字节码 offset 55 直接 `iterator()`，无 null 检查）。

量化例子见 §10.2：ContractAdmin 若提交 delta → 47→1，rr_app 409→363。

## §11.5 顺带确证的枚举口径（DECISION-11 第二点）

- `UdcRoleResource.<init>()` 逐字：`getstatic ResourceTypeEnum.MENU` → `putfield resourceType` ⇒ 构造器**默认 MENU**。
- `ResourceTypeEnum` 是 `("MENU", ordinal=1, code=0)` —— **ordinal ≠ 库值，库值用 code**（MENU=0 / PAGE=1 / CONTROL=2 / DATA=3）。
- 我的实测落库 `resource_type=0` 与 code 口径一致；auditor 初判「恒=1」是把 ordinal 当库值，已被数据否证。
- 真实风险：service 层**无 `setResourceType` 调用**（字节码确证）⇒ 写入行恒为 `resource_type = MENU.code = 0`。若资源实际 `type ≠ 0`，该行即为**错配**（rr_type=0 但资源是真 type），页面按 resource_type 分类渲染时会归到 MENU 类而非真实类型 ⇒ 权限清单显示不全 ⇒ **假阴性**。
- 全表实证：`rr_type=0` 共 4104 行、错配 **912** 行（100% 落在 rr_type=0，其余 1/2/6/5 错配全为 0）；近两月 715 行 = **78%**，说明该路径**仍在持续产出**（auditor FINDING-01 + main DECISION-15 独立复核）。目标 app 0 行错配，因其从未走过该路径（不是干净）。
- ⇒ **阶段5 铁律 4 修正**：样本必须选 `udc_resource.type=0` 的资源（现查确认）。先前写的「MENU 类 / type=1」是**把 `ResourceTypeEnum.code`（MENU=0）与 `udc_resource.type`（0=NORMAL，另一套枚举）混为一谈**，已按 DECISION-15 改正。上次探针-C 选 `2710418858302391088` 恰好 `type=0`，属**碰巧合规**，不是有意遵守。
- 912 行错配登记为**独立议题**（平台级写路径缺陷），不进阶段5，不在本域修复。

---

# §12. 追加授权整包实跑（HANDOFF-09 / DECISION-19，LIVE PASS）

> 执行时点：**2026-10-18 00:49:05 – 00:50:25 GMT+8**（每步带 as-of）
> 目标角色：`shangwuadmin-datamigration9000000000000000001`
> - `udc_role.id` = **`1547666253648711259`**（授权侧）
> - `ctp_role.id` = **`8848607738770912620`**（绑定侧，镜像现成）
> 本轮验证目标：**铁律 2「先读全量 → 内存合并 → 整包提交」是否真的保住存量**（而非变成 delta）
> 边界：不绑定用户、不触审批流、不动 `ctp_user_role`。全程在本域授权应用内。

## §12.0 为什么最终没用 ContractAdmin（执行前拦截）

HANDOFF-09 初版指定 ContractAdmin（47 条）。执行前我发现**不可逆破坏风险**，拦截并上报（BLOCKED-09），main 裁定改目标。

**根因：`saveFuncAuthByRole` 与 `saveFuncAuthAll` 是两个不同实现**

| 方法 | `setResourceType` | 后果 |
|---|---|---|
| `UdcRoleService.saveFuncAuthByRole`（func-auth **by role** 走这条） | **0 次**（offset 94→129 只 `setRoleId`/`setResourceId`/`setAction`，然后 `createBatch`） | `resource_type` 落构造器默认 MENU(**0**) |
| `UdcRoleService.saveFuncAuthAll`（func-auth **all** 走这条） | **有**（offset 1688–1700，`ifnull` 检查后 `setResourceType(resource.getType())`） | 写入真实 type |

Controller→AppService→Service 三跳 javap 已核实：`funcAuthByRole → saveFuncAuthByRole`（无 type）；`funcAuthAll → getResourceList + saveFuncAuthAll`（有 type）。

**破坏面量化（实测）**

| 角色 | 授权行 | 其中 `rr_type ≠ 资源真实 type`（=整包重写退化面） |
|---|---|---|
| Admin | 58 | 31 |
| SystemAdmin | 58 | 31 |
| AllApp | 51 | 30 |
| huaweiadmin | 47 | 27 |
| kuangjiaadmin | 47 | 27 |
| **ContractAdmin**（原定目标） | **47** | **27**（18 PAGE + 9 CONTROL） |
| ZNXMGLCW | 45 | 27 |
| ZNXMGLTBGLY | 45 | 27 |
| hwmkry | 6 | 1 |
| **shangwuadmin**（最终目标） | **4** | **0** ✅ |
| quanxian | 1 | 0 |

**关键的第三层**：回滚也是走 `saveFuncAuthByRole` ⇒ **回滚同样写不回原 type**。「快照是回滚依据」这条生命线在 byRole 语义下**不成立**。这是选 shangwuadmin（零退化）的另一半原因——它的 4 条全是 0↔0，回滚后类型无退化风险。

## §12.1 步骤 0 —— 写前全量快照（生命线）

**基线 as-of `00:49:05`**

```
rr_total = 12356   rr_app = 409   r_app = 11
shangwuadmin 授权行 = 4        ContractAdmin = 47
```

**shangwuadmin 现有 4 条逐行明细**（落盘 `h09_snapshot_4.json` / `h09b_snapshot_4.json`）

| id | resource_id | resource_type | action |
|---|---|---|---|
| 540616972335926618 | 3835144096067766754 | 0 | 0 |
| 7226836460491132588 | 5272047500345491850 | 0 | 0 |
| 7758046402137901354 | 6507095038478927155 | 0 | 0 |
| 1382997595608533155 | 9045337234040441658 | 0 | 0 |

4 条对应资源均为 `type=0`（子页面 `PRESET_SUBPAGE` / 数据迁移 `ROOT` / 外框 `PRESET_LAYOUT` / 首页 `BIZ_HOME`）⇒ **错配 0 行，整包重写零退化**。

**11 个角色逐角色计数（写前基准，回滚比对用）**

```
Admin 58 / SystemAdmin 58 / AllApp 51 / ContractAdmin 47 / kuangjiaadmin 47
huaweiadmin 47 / ZNXMGLCW 45 / ZNXMGLTBGLY 45 / hwmkry 6 / shangwuadmin 4 / quanxian 1
```

**读接口交叉核验（写前）**：`udcCtpUserRoleRoleAuthPost(roleId=1547666253648711259)` → `BOOT_0000`，`resourceList` = **4** 条，`resourceType` 全 `MENU`，与 DB 集合**逐 id 一致**（API 4 / DB 4，set 相等）。

**写前即时复核 as-of `00:49:53`**：rr_total 12356 / rr_app 409 / target 4 / ContractAdmin 47 —— 与 6 分钟前基线一致，窗口内无第三方写入。

## §12.2 步骤 1 —— 选资源（现查确认，不转抄）

**筛选条件**：`app_id=9000000000000000002 AND type=0 AND data_type='NORMAL' AND is_deleted=0 AND id NOT IN (该角色现有 4 条)`

候选共 **14 个**，剔除 `小爪验收菜单`/`小爪实验菜单*`/`xzhMenu*` 等历史测试数据后，选真实业务资源：

**选中：`3974578600125940031`「数据源配置」**（code `4774153827087238385`）

选前现查确认（铁律 4/5）：

```
{id: 3974578600125940031, code: '4774153827087238385', name: '数据源配置',
 type: 0 ✔, data_type: 'NORMAL' ✔, is_deleted: 0 ✔, app_id: 9000000000000000002 ✔}
```

并确认该角色**当前未授权**此资源（`SELECT ... WHERE role_id=... AND resource_id=...` 返回空）。

## §12.3 步骤 2 —— 整包合并提交（5 条）

**合并过程**：读全量 4 → 内存 +1 → **整包 5 条**（不是 delta）。
提交 body 全文已落盘 `h09b_evidence/request_body.json`（5 条 resourceList 全文，无截断）：

```json
{"roleId":"1547666253648711259",
 "roleCode":"shangwuadmin-datamigration9000000000000000001",
 "resourceList":[
  {"resourceId":"3835144096067766754","resourceType":"MENU","action":"basic"},
  {"resourceId":"9045337234040441658","resourceType":"MENU","action":"basic"},
  {"resourceId":"5272047500345491850","resourceType":"MENU","action":"basic"},
  {"resourceId":"6507095038478927155","resourceType":"MENU","action":"basic"},
  {"resourceId":"3974578600125940031","resourceType":"MENU","action":"basic"}
 ]}
```

**响应原文**（`h09b_evidence/response_raw.txt`，耗时 0.16s）：

```json
{"code":"BOOT_0000","data":{"content":5},"message":"SUCCESS","status":0}
```
traceId `3278935733288569020`（`content:5` = 实际写入 5 条）

## §12.4 步骤 3 —— 写后四条核验（全过）

**as-of `00:50:06`**

| # | 判据 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| (a) | `rr_total` | 12356 → **12357** | **12357** | ✅ |
| (b) | `rr_app` | 409 → **410** | **410** | ✅ |
| (c) | **shangwuadmin 授权行** | 4 → **5**（**不是 4→1**） | **5** | ✅ |
| (d1) | ContractAdmin | 保持 **47** | **47** | ✅ |

**(d2) 其余 10 个角色逐行不变**（全部 ✅）：

```
AllApp 51→51  ContractAdmin 47→47  ZNXMGLCW 45→45  ZNXMGLTBGLY 45→45
Admin 58→58   SystemAdmin 58→58    huaweiadmin 47→47  hwmkry 6→6
kuangjiaadmin 47→47  quanxian 1→1    变化角色数 = 0
```

**⇒ 铁律 2 得到 LIVE 证实**：整包提交**不是** delta，存量 4 条被完整保留，且只 +1。

## §12.5 步骤 4 —— 读接口回读

`udcCtpUserRoleRoleAuthPost(roleId=1547666253648711259)` → `BOOT_0000`，`resourceList` = **5** 条：

```
★新增  3974578600125940031   MENU   basic
       9045337234040441658   MENU   basic
       6507095038478927155   MENU   basic
       5272047500345491850   MENU   basic
       3835144096067766754   MENU   basic
```

新增那条在回读中 ✅。

**DB 逐行 + 原 4 条 type 零退化核验**：

| resource_id | 写前 type | 写后 type | 结果 |
|---|---|---|---|
| 3835144096067766754 | 0 | 0 | ✅ |
| 5272047500345491850 | 0 | 0 | ✅ |
| 6507095038478927155 | 0 | 0 | ✅ |
| 9045337234040441658 | 0 | 0 | ✅ |
| 3974578600125940031（新增） | — | 0 | ✅ |

该角色 `COUNT(rr.resource_type <> u.type)` = **0** ✅（零错配，未新增污染）

## §12.6 步骤 5 —— 回滚（整包提交原 4 条）

**回滚集取自写前快照文件**（`h09b_pre_readback.json`，非内存变量），断言 `len == 4` 后才提交。body 落盘 `h09b_evidence/rollback_body.json`：

```json
{"roleId":"1547666253648711259","roleCode":"shangwuadmin-...",
 "resourceList":[3835144096067766754 / 9045337234040441658 / 5272047500345491850 / 6507095038478927155，均 MENU/basic]}
```

**回滚响应**（`h09b_evidence/rollback_response_raw.txt`）：

```json
{"code":"BOOT_0000","data":{"content":4},"message":"SUCCESS","status":0}
```

**回滚后核验 as-of `00:50:25`**

| 项 | 期望 | 实测 | 结果 |
|---|---|---|---|
| `rr_total` | 12356 | **12356** | ✅ |
| `rr_app` | 409 | **409** | ✅ |
| shangwuadmin | 4 | **4** | ✅ |
| ContractAdmin | 47 | **47** | ✅ |

**逐行完全一致（不只是计数）**：

```
写前: [(3835144096067766754,0,0), (5272047500345491850,0,0), (6507095038478927155,0,0), (9045337234040441658,0,0)]
回滚: [(3835144096067766754,0,0), (5272047500345491850,0,0), (6507095038478927155,0,0), (9045337234040441658,0,0)]
逐行完全一致: True
```

**11 个角色全部回到写前值**（4→4, 47→47, 58→58, 51→51, 45→45, 6→6, 1→1）✅

## §12.7 边界确认（未越界）

| 项 | 期望 | 实测 |
|---|---|---|
| `ctp_user_role` 总行数 | 未变（38） | **38** ✅ |
| shangwuadmin 的 `ctp_role.id=8848607738770912620` 绑定数 | 未变（0） | **0** ✅ |
| 是否触审批流 | 否 | 未调 `organizationCtpAuthorizationRule*`，无审批单 ✅ |
| 全表错配总量 | 未增加（912） | **912** ✅ |
| 本轮写入 | 仅 2 次 func-auth（+1 / 回滚），均已归零 | ✅ |

## §12.8 结论

1. **铁律 2 获得 LIVE 验证**：整包 5 条提交后存量 4 条完整保留、只 +1；四条核验全过；回滚后逐行完全一致。⇒「先读全量 → 内存合并 → 整包提交」**是正确且必要的**，delta 提交会抹除存量。
2. **func-auth = 覆盖式（按 roleId 全删全建）再次确证**：`content:5` / `content:4` 是写入**总条数**，不是增量。
3. **`saveFuncAuthByRole` 缺 `setResourceType`** 这一机理级根因被 BLOCKED-09 钉死，解释了 FINDING-01 那 912 行错配 100% 集中在 `rr_type=0` 的成因；当前写路径仍在产出。已按 main 裁定与 912 行错配合并为同一独立议题上报，**不在本域修复**。
4. **探针角色路径作废**：`ctp_role` 镜像来自应用导入/迁移，手工建角色不产生镜像（11/11 vs 0/3）⇒ 阶段5 必须用已有真实角色。

**本次仍不构成「生效」**：未绑定任何用户，被授权主体的实际访问能力未发生变化。跨账号生效仍待第二账号凭据（NEEDS_HUMAN）。
