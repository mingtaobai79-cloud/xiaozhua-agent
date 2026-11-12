# P3b · 「查看权限」面板只读归因复盘（HANDOFF-05 / CORRECTION-05）

> 任务：HANDOFF-05（dedupe_key `role-handoff-05-auth-panel-recheck`）+ CORRECTION-05 修订（P-A 撤回，P-A'/P-B 二分）
> 证据时点：**2026-10-17 23:36–23:48 GMT+8**
> 方法论：只读；不改实现；不建探针；不发 func-auth（全程遵守）。

## 0. 结论速览（一句话）

**P-A'（结构性只读）成立，P-B（本账号权限位缺失）被否定**——「查看权限」面板的复选框 disabled 不是权限位计算结果，而是 `permissionLook` 组件入参（查看模式标志）在**按钮分发层**被固定为 true 的下游结果；**本账号实际持有 `CtpUserAdmin=true / RootCtpUserAdmin=true / OrgAdmin=true`（LIVE 实测）**，不存在权限缺口。真正缺口 = **当前 udc 设计器角色页面上，「设置权限」按钮（可写路由）未渲染**，原因待一步定位（见 §6）。

---

## 1. 四项必答证据（ROUTE 23:34 状态机清单）

### ① disabled 表达式逐字原文 + 依赖变量

来源：`src_pages_role-authority_index_tsx.cef9f043.js`（P1 §0 清单内同源 bundle）+ `out1.js`（授权表格组件，模块内 `L`）。**逐字**：

```js
// out1.js — 授权表格组件 L：
let {permissionLook: t = !1, type: l = "PC"} = e;
let O = (e,t,l,n) => { let a = (0,y.vd)(I,w,S,L,t,e,l,n); i((0,c.k6)(a)) };
// 菜单列复选框：
r().createElement(r.Checkbox, {
  checked: !!L[n],
  disabled: t,                       // ⭐ t = permissionLook（查看模式标志），非权限位
  onChange: e => O(e.target.checked, n, "menu", i)
}, e)
```

- `disabled` 的值 = `permissionLook`，**一个布尔 prop，与角色数据、权限位、isRoot 全部无关**
- React fiber 实测：checkbox 的 `disabled` prop 在 hop0/2/4/5 四层全部是**字面布尔 `true`**（非函数、非计算表达式）——上游某一层直接传了 `true`

### ② `permissionLook` 从哪来（按钮分发层）

来源：`src_pages_role-authority_index_tsx.cef9f043.js` 角色列表列定义（**逐字**）：

```js
// 第二组 columns（本页面实际渲染组）：
let {status:a, type:o, isRoot:i, editPermission:d=!1, appId:c, orgId:p} = n,
    m = o === u.A6.ORG,                                      // type===ORG?
    h = !i && [u.A6.APP, u.A6.PRESET].includes(o),           // 可编辑角色类型?
    v = m ? !Q(t,{orgId:p}) : h,                             // 「编辑/查看」按钮分支
    g = m ? !Q(t,{orgId:p}) : !1 === d,                      // ⭐「查看权限/设置权限」按钮分支
    y = v ? l?.permissions_view : l?.permissions_edit;
// 权限弹窗按钮二选一：
g ? Button{...(l?.permissions_view),   onClick:...M(!0),O(!0)}  i18n "查看权限"
  : Button{...(l?.permissions_setting), onClick:...M(!1),O(!0)}  i18n "设置权限"
```

**链条判定**（目标 app 角色 `type=APP`，`m=false`）：
- `g = !1 === d`，`d` 来自行解构默认值 `editPermission:d=!1`
- **列表行实体字段实测（React fiber 抓取）**：`admin, appId, code, description, id, name, type, g_l_index` —— **没有 `editPermission` 字段** ⇒ `d = false`（默认值）
- ⇒ `g = !1 === !1 = true` ⇒ **渲染「查看权限」按钮**（`permissionLook=true` 传入弹窗）⇒ 复选框全 disabled

⇒ **「查看权限」面板 = 查看模式，对所有角色、所有账号都只读。它根本不是授权写入口。**

### ③ 本账号权限位实际值（LIVE，逐字响应）

`GET /service/organization/org-unit/is-manager`（traceId `3278874923128326332`，as-of 23:46）：

```json
{"status":0,"code":"BOOT_0000","message":"SUCCESS",
 "data":{"content":{
   "RootCtpUserAdmin": true,     ⭐
   "OrgAdmin": true,             ⭐
   "CtpUserAdmin": true,         ⭐
   "GroupAdmin": true,
   "isAdminMap": {"-2638952494757493308": true},   （来自 pc-user-info USER_INFO_MAP，sy_uid 匹配）
   ...}}}
```

同时 `pc-user-info` → `USER_INFO_MAP`：`isAdmin=false`、`isOrgAdmin=true`、`isAdminMap[本uid]=true`。

**权限位计算（模块 1112，逐字）**：

```js
t.A = e => {
  let {adminInfo:t} = useSelector(s=>s.commonReducer),
      {rolePermission:n} = useContext(RolePermissionContext),
      i = useCallback(n => {
        let {modulePermission:a} = n;
        return ({"ctp-application": t?.isCtpApplicationAdmin || !1,
                 "ctp-user":        t?.isCtpUserAdmin        || !1})[e]
               ? a
               : {visible:!0, disabled:!1, readonly:!0}      // ⭐ 非管理员 → 强制只读
      }, [t,e]);
  return {rolePermission:n, getRolePermission:i};
};
// adminInfo 计算（reducer）：
{CtpApplicationAdmin:a, CtpUserAdmin:o, RootCtpUserAdmin:l, OrgAdmin:i, RootOrgAdmin:r} = content,
s = i || r;                       // OrgAdmin/RootOrgAdmin → 管理域标志
adminInfo = {...t, isCtpApplicationAdmin:a&&!s, isRootCtpUserAdmin:l&&!s, isCtpUserAdmin:o&&!s}
```

⇒ 按此逻辑：`s = OrgAdmin||RootOrgAdmin = true` ⇒ `isCtpUserAdmin = CtpUserAdmin && !s = true && !true = **false**`！
（`isCtpApplicationAdmin` 同理为 false。）

⇒ **修正后的 P-B 判定：权限位机制存在且生效——本账号因同时是 OrgAdmin，被 reducer 规则把 `isCtpUserAdmin` 归约为 false，`getRolePermission` 返回 `{visible:true, disabled:false, readonly:true}`（强制只读）。**
⇒ 但注意：这个 `readonly:true` 影响的是**按钮的 disabled 包装**（`J.K1`），而**复选框的 disabled 来自 `permissionLook`**（§1①）。两者是不同层的开关。当前页面「查看权限」按钮可点、弹窗打开，说明按钮层没被禁；复选框层是 `permissionLook=true` 所致——而 `permissionLook=true` 又由 §1② 的 `g=true`（按钮身份）决定，**与权限位无关**。

### ④ 面板完整 DOM 结构（as-of 23:39）

```json
{"title":"查看权限",
 "tabs":["web功能权限","移动功能权限"],
 "buttons":["","","","","","","","","",""],   // 十个按钮全部无文本（图标按钮，无保存/确定）
 "cbTotal":31, "cbEnabled":0, "cbChecked":0}
```

- 无保存/确定按钮（footer 只有图标按钮）；无 aria-disabled；disabled 落在 `input.disabled` + `label.ant-checkbox-wrapper-disabled` class
- 树形表格 96 行（数据完整渲染，MENU/PAGE/CONTROL 层级齐全）——**数据读得到，只是不可改**

---

## 2. P-A'/P-B 二分判定

| 假设 | 判定 | 依据 |
|---|---|---|
| P-A' 结构性只读（面板本身不承载写） | ✅ **成立（面板层）** | disabled=permissionLook（§1①），「查看权限」按钮身份由 `g=true` 决定（§1②），与账号无关 |
| P-B 权限位缺失（本账号无权限） | ⚠️ **部分反转** | 权限位机制真实存在；本账号 `isCtpUserAdmin` 因 OrgAdmin 归约规则被算成 false（§1③），但这影响的是按钮层，不是复选框层 |

**综合：面板只读是「查看权限」这个按钮的固有属性（查看模式），不是「我的权限不够」。**
**真正的问题：本页面（udc 设计器角色列表）上，「设置权限」按钮从未渲染 —— `g=true` 恒成立，因为列表行数据里根本没有 `editPermission` 字段。**

---

## 3. 新问题（本片收口点）：`editPermission` 为什么缺失？

列表数据源 = `POST /ctp-role/app-role/search`（模块 2899 `Jp`，**平台全局角色列表接口**——CORRECTION-04 曾判定它 BOOT_1004，但那是直接 curl 无 referer 场景；页面内由 ctp-user 微前端调用，本页列表 13 行就是它返回的）。

两个可能：
1. **该接口对 udc 设计器场景不返回 `editPermission`**（返回体字段实测只有 8 个：`admin/appId/code/description/id/name/type/g_l_index`——这是 GraphQL op `udcCtpUserRoleSelectListPost` 的字段投影，bundle 里 op 定义就是这样选的）。⇒ 前端拿到的是 GraphQL 精简投影，`editPermission` 在**服务端有、被 op 投影丢弃**，或**该接口本身不产这个字段**。
2. bundle 的另一分支（第一组 columns，有「授权用户」按钮）用的是**另一个数据源**（`/ctp-role/app-role/search` 直连版，字段更全）。当前 udc 页面走的是 GraphQL 版。

**验证途径（需 main 裁，涉及新请求）**：直接调 `POST /service/ctp-user/ctp-role/app-role/search`（带有效 referer 场景复放，只读），看响应里是否有 `editPermission` 字段。有 ⇒ 字段被 GraphQL op 投影丢弃，找 udc 侧入口或要求后端补投影；无 ⇒ 该接口在当前账号/场景下不产出此字段。

**另一条不需要新请求的线索**：bundle 第一组 columns 出现条件是 `n`（布尔，页面状态），且「授权用户」按钮 `disabled:!l`（`l=enabled` 行字段）——**列表行没有 `enabled` 字段**（8 字段里无），这组列在本页面必然渲染不出可写入口。⇒ udc 设计器角色页与平台全局角色页（`/ctp-user/role/appRole`）是**两套 columns 定义**，可写入口只在后者。而后者当前账号 BOOT_1004 被拒（P2 §4.1，ORG 维度参数）。

---

## 4. 对 main A/B/C 的影响

- **A（给 test-account-1 授 OrgAdmin）**：**作废**——本账号已经是 OrgAdmin（§1③ 实测）。授予不会改变复选框 disabled（那是 permissionLook）。
- **B（第二账号）**：**不必要**——权限位不是阻塞点。
- **C（REST 直连 func-auth）**：**仍倾向不批**（硬约束 6），且现在有了更精确的方向（§3）。

**替代路径（建议 main 裁，二选一）**：
- **D-1：从平台全局角色页走通**——该页有完整可写 columns（第一组，含「授权用户」）。先解 BOOT_1004：其请求参数 `roleLevel=0 + isAppAdmin=true + currentOrgId=<root org>`。`is-manager` 实测本账号 `RootCtpUserAdmin=true`，BOOT_1004 的真实原因待查（可能是 `currentOrgId` 传参、或缺 referer/token 场景差异）。这是纯前端参数问题的话，D-1 不需要任何人工输入。
- **D-2：查 udc 设计器「设置权限」按钮为何不渲染**——本质是 GraphQL op 投影缺字段，属平台契约面问题，超出本域可修范围，可能构成真实 NEEDS_HUMAN（向平台组提需求）。

---

## 5. 证据等级

| 项 | 等级 |
|---|---|
| disabled=permissionLook（bundle 逐字 + fiber 布尔实值） | **STATIC + LIVE** |
| 列表行 8 字段无 editPermission（fiber 实体抓取） | **LIVE** |
| g/`!1===d` 按钮身份推导（bundle 逐字） | **STATIC** |
| 本账号 CtpUserAdmin/RootCtpUserAdmin/OrgAdmin=true（is-manager 响应原文） | **LIVE** |
| adminInfo 归约逻辑（reducer 逐字） | **STATIC** |
| 面板 DOM 结构（title/tabs/buttons/cb 统计） | **LIVE** |
| 「设置权限/授权用户」按钮在 udc 页面不存在（全页文本检索 false） | **LIVE（负）** |
| D-1 前提（全局页可写入口存在性） | **STATIC（bundle）+ UNVERIFIED（LIVE 未验证 BOOT_1004 根因）** |

## 6. 遗留

- `editPermission` 字段在服务端是否存在/为何未到达前端：**UNVERIFIED**（需 D-1 复放 app-role/search 才能定）。
- 面板 footer 十个图标按钮的功能未逐个识别（无文本，需 i18n key 对照，本片未做——不阻塞判定）。
- 全程未发 func-auth、未建探针、未写任何表（零变更）。
