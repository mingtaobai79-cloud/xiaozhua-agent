# P1｜设计器「角色」页面接口调用链（STATIC 闭合 + LIVE UNVERIFIED）

- 任务：HANDOFF-02 子项B（阶段2，P0 缺口第二条：前端调用链）
- 证据分级：STATIC = 字节码/bundle 实读（本 implementer 独立解包/javap 产物，权威）；LIVE = UNVERIFIED（原因见 §6）
- 本片计数 as-of：2026-10-17 18:0x（GMT+8）；STATIC 证据提取自 16:26–17:30 会话窗口的磁盘产物
- R2 口径声明：本片全部 STATIC 证据来自 implementer 自产产物目录
  `<HERMES_HOME>/cache/scratch/implementer-only/role_static_r2/`（extract→javap 全程自己执行）。
  `scratch/audit03_role_static/`（auditor 待命期预取）本 implementer **未打开、未引用**，
  其结论与本文档的交叉一致性 = UNVERIFIED（非结论，见 §7）。
- 边界自查：全程只读（无 DB 写、无业务写请求）；未跨域；未引用 core/role/ Agent 角色卡。

> **📍 补充文件指针（2026-10-18 11:57 加，main #VIS-S4-WAIT §四 授权）**
> 本文档缺三块结构性内容，已另立 `docs/audit/role/P1-STRUCTURE-SUPPLEMENT.md`（15,746 B，全 STATIC）补齐：
> **① 版本边界表**（5 面，2 面硬锚：class SHA-256 / 产物 sha16；3 面 BLOCKED 明示）
> **② chunk 按调用形态归类**（8 chunk 构造器计数 + 12 op 逐条认定；
>    纠正「按 Get/Post 后缀推形态」的坑：`AppResourceGet` 实为 `udcApolloQuery` 而非 loader）
> **③ 端点↔页面元素映射**（15 端点全覆盖：**11 有 UI 入口 / 2 无入口 / 1 入口未确证 / 1 页面不接 = 15**）
>
> **本文档结论不因补充文件而改变**；如有冲突，以补充文件的实测数据为准。
> 另：`docs/audit/role/P1-LIVE-GAP-MATRIX.md` 是 15 端点的 LIVE 缺口清单（只列不跑）。

---

## 0. 权威来源清单（全部 implementer 自产，可抽查）

| 产物 | 内容 | 来源 jar / bundle | 生成方式 |
|---|---|---|---|
| `role_static_r2/classes/…` | udc-user 5.3.517 解包 class 树 | `scratch/djars/udc-user-5.3.517.jar` | `unzip -o`（worker.log 3024） |
| `role_static_r2/ctrl_v.txt` (77,922B) | `javap -v -p` UdcRoleController 全量（常量池+注解+字节码） | 上项 | javap 17 |
| `role_static_r2/ResourceActionEnum.5.3.351.javap.txt` (6,236B) | `javap -p -c` ResourceActionEnum static 块 | `<MAVEN_REPO>/com/seeyon/ctp-user-facade/5.3.351/…jar` | javap -c |
| `role_static_r2/v429/`、`v351/` | ResourceActionEnum 双版本对照提取 | facade 5.3.429 / 5.3.351 | javap -c + sha256 对比 |
| `role_static_r2/ResourceTypeEnum.5.3.351.javap.txt` | ResourceTypeEnum static 块 | facade 5.3.351 | javap -c |
| `role_static_r2/ctrl_resource_action_enum.txt` (13,185B) | `javap -v` UdcControlResourceActionEnum（udc 侧同族枚举） | udc-common-5.3.517（classes/ 解包） | javap -v |
| `role_static_r2/GraphQLController.javap.txt` (80,157B) | GraphQLController 端点注解 | boot-starter-graphql（5.3.358，djars 系） | javap -v |
| `role_static_r2/ctpuser/com/seeyon/ctp/user/enums/*.class` | RoleTypeEnum/RoleLevelEnum 等全家 | facade 5.3.429 | unzip |
| `role_static_r2/web/*` | ctp-user 前端真实 bundle chunk（remoteEntry + role-* 4 个 chunk + module1622 抽取） | `GET https://lowcode-test2.example.com/ctp-user/remoteEntry.js` = 200 | curl 下载（worker.log 1597–1616） |
| `role_static_r2/live_net_probe2.json`、`live_login_state.json`、`live_probe1..6.py` | LIVE 尝试与 403 证据 | — | CDP 9231 |

---

## 1. 后端控制器（STATIC，权威）

`com.seeyon.udc.user.controller.UdcRoleController`（udc-user-5.3.517.jar，javap 显示 major 52 / 18 方法 / 4 字段）

类级注解（`ctrl_v.txt` 文件尾 RuntimeVisibleAnnotations 段逐字读出）：

```
@RestController
@RequestMapping(value=["udc/ctp-user/role"])
@RestApi(value="角色相关接口")
@HasRole(value=["OrgAdmin","udcAppDesigner","udcSystemAdmin"])
```

⇒ 后端真实 REST 基路径 = **`udc/ctp-user/role`**（网关全路径形态见 §6）。
⇒ 类级权限闸：OrgAdmin / udcAppDesigner / udcSystemAdmin 三角色可进入。

## 2. 端点全集（15 个带映射方法，注解逐条读出）

> 口径差异说明：前序会话交接摘要写「端点全集 16 个」，本文按 javap 逐条提取实为
> **15 个**（11 POST + 4 GET）；`checkPermission(Long)` 是私有校验方法，无 Mapping 注解，不计入。
> 15 = 11 POST + 4 GET，与映射 token 总数（PostMapping 12 处含类级引用复用、GetMapping 5 处）核对无第三种取值。

| # | 方法 | HTTP | 子路径 | 参数形态（注解实读） | 返回 |
|---|---|---|---|---|---|
| 1 | create | POST | `create` | @RequestBody UdcRoleDto | SingleResponse\<Long\>（"新建角色"） |
| 2 | update | POST | `update` | @RequestBody UdcRoleDto | SingleResponse\<Integer\>（"修改角色"） |
| 3 | delete | POST | `delete` | @MultiRequestBody（id） | SingleResponse（"删除角色"） |
| 4 | deleteByAppId | POST | `delete-resource/app/{appId}` | @PathVariable | SingleResponse（"按appId删除资源"） |
| 5 | deleteById | POST | `delete-resource/{id}` | @PathVariable | SingleResponse（"按Id删除资源"） |
| 6 | selectById | GET | `{id}` | @PathVariable id | SingleResponse\<UdcRoleDto\>（"查询应用角色详情"） |
| 7 | selectRoleList | POST | `select-list` | @MultiRequestBody PageInfo+Map+Sort | 分页角色列表（"分页获取应用角色列表"） |
| 8 | selectResourceByApp | GET | `app-resource` | @RequestParam appId, admin | 资源树（"按应用获取资源列表"） |
| 9 | selectPageResource | GET | `select/page-resource` | @RequestParam appId, code | 页面功能控制资源（"获取页面功能控制资源"） |
| 10 | selectResourceType | GET | `app-resource-type` | — | 资源类型参数（"获取资源类型对应的参数"） |
| 11 | selectRoleAuthById | POST | `role-auth` | @MultiRequestBody | 角色授权列表（"获取角色权限"） |
| 12 | selectRoleAuthByAppId | POST | `role-auth-all` | @MultiRequestBody | 全部角色授权（"获取全部角色的角色权限列表"） |
| 13 | saveFuncAuthByRole | POST | `func-auth` | @RequestBody UdcRoleFuncPermissionDto | 按角色设置功能权限 |
| 14 | saveFuncAuthAll | POST | `func-auth-all` | @RequestBody List\<UdcRoleFuncPermissionDto\> | 批量设置功能权限 |
| 15 | createSystemAdmin | POST | `create-system-admin` | @MultiRequestBody | 建系统管理员（"创建系统管理员, 有则不创建"） |

注意：#15 `create-system-admin` 是**写操作**（幂等创建），阶段2 只读边界下仅 STATIC 登记、LIVE 不触发。

## 3. DTO（javap 实读，非推测）

`com.seeyon.udc.user.dto.*`（udc-user-5.3.517.jar）：

- **UdcRoleDto**（extends BaseMultipleVersionDto）：
  `code, name, description, admin(Boolean), appId(Long), appName, type(RoleTypeEnum), relationOrgRoleCode, sortNumber(Integer), appAdmin(Boolean), roleLevel(RoleLevelEnum)`
- **UdcRoleResourceDto**（extends BaseMultipleVersionDto）：
  `roleId(Long), resourceId(Long), resourceCode(String), resourceType(ResourceTypeEnum), action(ResourceActionEnum)`
  构造器 `(Long, String, ResourceTypeEnum, ResourceActionEnum)` —— 授权写链的四元组形态。
- **UdcRoleFuncPermissionDto**（extends BaseDto）：
  `roleId(Long), roleCode(String), resourceList(List<UdcRoleResourceDto>)`
- 同 jar 另有 UdcRoleJsonDto / UdcRoleResourceJsonDto / UdcRoleApplicationDto（详情/快照/应用维度）。

## 4. 前端真实调用面（STATIC，bundle 实读）

证据 chunk（均来自线上 bundle 实抓，保存于 `role_static_r2/web/`）：
- `remoteEntry.js`（15,328B，HTTP 200）—— ctp-user 微前端入口
- `src_pages_role-permission_index_tsx.7d23367b.js`（16,319B）— 角色管理页（列表+功能权限 Tab）
- `src_pages_role-permission_entry_tsx.ebba5ac6.js`（16,574B）— 角色权限入口页（action 下拉选项在此）
- `src_pages_role-authority_index_tsx.cef9f043.js`（58,457B）— 角色授权布局页
- `module1622.js`（3,994B）— **GraphQL op 定义层（模块 1622）**，从 bundle 中原样抽出

### 4.1 调用链结构（三层，逐层证据）

```
页面组件 (role-permission_index_tsx / role-authority)
   │  redux thunk (bussiness.8e39da83.js 模块 6994, 实读 createAsyncThunk)
   │    fetchRoleList / handleRoleInfo / handleDeleteRole / fetchAuthByRoleId
   │    handleFunctionAuthByRoleId / fetchAppResource / fetchPageControlResource / fetchAppResourceType
   ▼
模块 1622 op 层 (module1622.js)
   │  l.udcApolloQuery("<mutation/query op 名>", {body|query})
   │  例外：a.AU.post("/ctp-user/role/create-system-admin", e)   ← 唯一直连 REST
   ▼
POST /service/udc/graphql  (udc graphql 端点)
   → 【UNVERIFIED，修正时点 2026-10-17 23:05，采纳 VERDICT-02 D2】
     下方「→ GraphQLController」一步不得当契约引用：
     - auditor 反证：bundle 中字面 `service/udc/graphql` 命中 0；真实拼址在 SDK
       `seeyon.vendor.global 5.3.41` 的 `ge=e=>{const t="/".concat(e,"/graphql")}`
       + `__SY_STATIC_API_ORIGIN__=//service-<host>`；
       GraphQLController 5 个映射均无裸 `graphql` 段。
     - P2 LIVE 反证：`POST https://lowcode-test2.example.com/service/udc/graphql` 实发且成功。
     - 两者并存 ⇒ 中间存在网关改写或另一 Controller，**机制 UNVERIFIED**。
   → GraphQLController(com.seeyon.boot.starter.graphql, class 级 @RequestMapping("/"),
       端点: POST openapi/graphql, GET graphql/update, GET graphql/cache/clear, GET graphql/getdoc,
             POST openapi/graphql-app/{app}/graphql) —— GraphQLController.javap.txt 逐条读出
   → 按 fieldType 路由到 UdcRoleController REST 契约
```

### 4.2 GraphQL op ↔ 后端端点对照（module1622.js 原文）

| op（fieldType） | 类型 | 入参 | 对应后端端点（§2 编号） |
|---|---|---|---|
| udcCtpUserRoleSelectListPost | mutation | body: PageInfo+params{appId} | #7 select-list |
| udcCtpUserRoleCreatePost | mutation | body: UdcRoleDto | #1 create |
| udcCtpUserRoleUpdatePost | mutation | body: UdcRoleDto | #2 update |
| udcCtpUserRoleDeletePost | mutation | body: {id} | #3 delete |
| udcCtpUserRoleRoleAuthPost | mutation | body: {roleId} | #11 role-auth |
| udcCtpUserRoleFuncAuthPost | mutation | body: UdcRoleFuncPermissionDto | #13 func-auth |
| udcCtpUserRoleRoleAuthAllPost | mutation | body: {appId, code} | #12 role-auth-all |
| udcCtpUserRoleFuncAuthAllPost | mutation | body: List | #14 func-auth-all |
| udcCtpUserRoleAppResourceGet | query | query: {appId, admin} | #8 app-resource |
| udcCtpUserRoleAppResourceTypeGet | query | — | #10 app-resource-type |
| udcCtpUserRoleSelectPageResourceGet | query | query: {appId, code} | #9 select/page-resource |
| udcCtpUserRoleGet | query | path: {id}（queryFields 含 relationOrgRoleCode/guid） | #6 {id} |
| （REST 直连）a.AU.post /ctp-user/role/create-system-admin | POST | — | #15 |

例证（module1622.js 原文节选，逐字）：

```
d=e=>l.udcApolloQuery("mutation udcCtpUserRoleSelectListPost ($body: udcCtpUserRoleSelectListPostInputBody) {
  udcCtpUserRoleSelectListPost(body: $body){ code data{content{admin appId code description id name type}
  pageInfo{needTotal pageNumber pageSize pages total}} message status } }",{body:e})
```

页面层调用例证（role-permission_index_tsx.7d23367b.js）：
- `(0,c.Jp)(c.fc)` → fetchRoleList（c.fc = `{pageInfo:{...}, params:{appId: u.vL}, sort: createTime DESC}`）
- `(0,c.Wq)(l.id)` → 删除角色（Popconfirm「确认删除此角色？」）
- `(0,c.bx)(e)` → 按 roleId 拉授权
- `(0,c.Pt)({resourceList:l, roleId:e, roleCode:t})` → 保存功能权限
- `(0,c.oY)({appId:u.vL, admin:!1})` → 资源树；`(0,c.Vu)({appId,code})` → 页面控制资源
- `(0,N.ig)(u.vL)` → AppResourceType；`(0,N.ic)(e)` → FuncAuthAll 保存

### 4.3 入口线索的形态纠正（HANDOFF 给的线索 vs 实测）

`/ctp-user/role/appRole/<appName>`（ROLE_MANAGE 菜单入口）是**设计器宿主壳的页面路由**，
不是接口路径。设计器「角色」页的真实接口形态 = GraphQL op（§4.2）+ 唯一 REST 例外
`create-system-admin`。前端 bundle 中不存在任何 `/ctp-user/role/select-list` 等直连 REST 调用。
LIVE 侧观察（live_net_probe2.json）：深链该 URL 只加载壳资源（静态资产 200）+
`/service/portal/main/pc-user-info`（403），不发角色业务请求 —— 与 STATIC 结论互相印证。

## 5. action / type 枚举权威定义（本片合并项）

### 5.1 udc_role_resource.action —— 权威 = com.seeyon.ctp.user.enums.ResourceActionEnum

`ResourceActionEnum.5.3.351.javap.txt` static{} 块逐指令读出：

| 枚举 | ordinal | code（写库值） |
|---|---|---|
| NONE | 0 | -1 |
| basic | 1 | **0** |
| readonly | 2 | **1** |
| disabled | 3 | **2** |
| invisible | 4 | **3** |

双版本一致性：facade **5.3.429 与 5.3.351 的 ResourceActionEnum.class sha256 完全相同**
（本 implementer 重新解包对比，2026-10-17 18:0x），枚举口径跨版本稳定。

同族交叉（udc 侧自有枚举）：`com.seeyon.udc.common.enums.UdcControlResourceActionEnum`
（`ctrl_resource_action_enum.txt`）：basic=0 / readonly=1 / disabled=2 / invisible=3 —— **与 ctp 侧一致**。

前端标签实证（role-permission_entry_tsx.ebba5ac6.js 内联，逐字）：
`B=[{value:"basic",label:"正常"},{value:"readonly",label:"只读"},{value:"disabled",label:"禁用"},{value:"invisible",label:"隐藏"}]`
⇒ **0=basic(正常) / 1=readonly(只读) / 2=disabled(禁用) / 3=invisible(隐藏)**。

> ⚠️ 有效发现（对 P0 的待修正项，不动 P0 避免混切片）：P0-role-object-model.md 把
> DB action 写成「0=访问、3=按钮」，与字节码+前端双重证据矛盾（0=basic/正常、3=invisible/隐藏）。
> 影响：阶段4/5 写链与授权生效判定的 action 语义必须按本片口径。
> （旁注：auditor 待命期预取 audit_t20–t23 曾得出 action=3 全 Button 的失配归因；因 R3 规则
> 其产物不作签字证据，本片不引用其数值，仅以自产字节码为准。）

### 5.2 udc_resource.type —— 权威 = com.seeyon.ctp.user.enums.ResourceTypeEnum

`ResourceTypeEnum.5.3.351.javap.txt` static{} 块逐指令读出：
`NONE=-1, MENU=0, PAGE=1, CONTROL=2, DATA=3, ENTITY=4, LAYOUT=5, SUBPAGE=6, NAV=7, GROUP=8`

> 同为待修正项：P0 把 type=3 写成「报表」，按枚举应为 **DATA=3**。
> P0 观察的 0/1/2/3/5/6 分布 ↔ MENU/PAGE/CONTROL/DATA/LAYOUT/SUBPAGE 可对上。

配套枚举（同 jar）：RoleTypeEnum（NONE=-1/PRESET=0/APP=1/ORG=2）、RoleLevelEnum（NONE=-1/GROUP=0/INSTITUTION=1）。

## 6. LIVE：UNVERIFIED @交付时点 → 已于 2026-10-17 22:44 后闭合（见 P2）

> **【修正时点 2026-10-17 23:05，采纳 VERDICT-02 D1：本节改双时点分栏】**
> 原「IP 级 403 → UNVERIFIED」归因仅对 17:20 时点为真。22:40 起环境状态迁移，
> LIVE 已由 P2（docs/audit/role/P2-role-live-readback.md，commit 135f17a）闭合（11/11 全字段一致）。
> 本节原文保留（当时证据自洽），归因分栏如下，**不再引用本节为「当前阻断状态」**。

### 6a. 时点一（交付时 17:20 左右）：nginx IP 级 403 → 当时 LIVE=UNVERIFIED

尝试链（live_probe1–6.py + live_net_probe2.json + live_login_state.json，CDP 9231）：

1. 凭据注入：shared-credentials/test2-web-credential.json（只路径引用），Network.setCookie success，tk 剩余 ~23.7h，SY_UID=test-account-1 正常写入。
2. `/main/portal` 可开（壳 200）；角色深链 `/main/child-frame/ctp-user/role/appRole/datamigration9000000000000000001` 文档 200，但只发静态资产请求，无角色业务请求（壳路由，需设计器壳内 SPA 点击）。
3. **一切 `/service/*` 一律 nginx 403（HTML 403）**，含：`/service/portal/main/pc-user-info`、`/service/ctp-user/menu/select-front-nav-menu`、`/service/udc/graphql`（GET/POST）、`/service/ctp-user/auth/token`（连登录端点都 403）。
4. 已排除假设：cookie 失效（注入有效）、Referer/Origin/XHR 头、https/http、直连 IP。
5. 归因：与 `core/facts/gateway/route-contract.md` §7「本机出口 IP 被 nginx 403（含登录端点），根路径 200 → IP 级策略」完全同型 → **本机出口 IP 被网关 IP 级策略拦截，LIVE 抓包本时点无法执行**。

结论：LIVE = UNVERIFIED（**仅限本时点**；环境事实，非本域契约问题）。

### 6b. 时点二（22:40–22:44）：403 解除 → BOOT_1006 会话失效 → 重新认证后 LIVE 闭合

- 22:40 main 裸探：`/service/*` 回到网关正常语义（200/405/redirectUrl），不再 nginx 403。
- 22:44 本 implementer：共享 cookie → `BOOT_1006 token黑名单`（会话失效，非 IP 拦截）；按凭据自带续期通路重新认证 → `udcCtpUserRoleSelectListPost` 成功返回 11 条。
- **当前阻断状态以 P2 §2.1 为准（LIVE 已通），本节 6a 不再是现状。**
- 另：LIVE 深链不可用（直开 = OSS `NoSuchKey`，P2 §4.3 旁证），需从 `/main/child-frame/udc/app-design/...` 设计器壳内点击「角色」导航触发
（P2 已 LIVE 验证该路径），且页面加载必然自动触发幂等写
`create-system-admin`（P2 §7：实测 3 次零新增，幂等）。

## 7. 交叉一致性 vs auditor 待命期预取：UNVERIFIED

本 implementer 未打开 `scratch/audit03_role_static/`（R2 降级对象），未做逐条 diff。
该目录按 R2/R3 只可作旁证；其 `ctrl_v.txt` 与本片 §1–§2 是否一致 = UNVERIFIED（如需交叉比对，由 auditor 在 REVIEW_REQUEST-02 自行执行——其产物其验，不构成本片证据依赖）。

## 8. 完成标准对照（HANDOFF-02）

- [x] D1 两处补丁 commit → **db93c36**（P0 §1 第 35 行 / §8 第 1112 行，as-of 15:15:18 实测 mtime）
- [x] 角色页接口链 STATIC 证据 → §1–§4（自产 javap + 线上 bundle，路径可抽查）
- [x] LIVE 请求原文或明确 UNVERIFIED 及原因 → §6 UNVERIFIED（IP 级 403，排除清单在案）【23:05 补注：该判定仅限 17:20 时点，LIVE 已于 22:44 由 P2 闭合，见 §6b】
- [x] action 枚举语义有权威来源 → §5.1（字节码双 jar 同值 + udc 侧同族一致 + 前端标签三重证据）

## 9. 对既有文档的修正建议（不在本片改动，留给后续切片/裁定）

1. P0 action/type 语义（§5 两处待修正项）。
2. SETTINGS-TABS-CALLCHAIN.md §4「角色权限后端 UNVERIFIED」可依本片 §1–§2 关闭。
