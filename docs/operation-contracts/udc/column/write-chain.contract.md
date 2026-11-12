# 栏目域 写链 + 读链契约（6 op）

> 切片：C1（HANDOFF-C1）｜ 生成时间：2026-10-18 +08
> 原料：`docs/audit/column-discovery/raw/` 7 件 + `ROUTE-S2-create-capture.md` + `ROUTE-S1-nav-capture.md` + `S2-WRITE-CHAIN-STATIC-20261017.md` + `static-s2-endpoint-map-20261017.txt` + ROUTE「S2 LIVE 事实更正」段
> 字段来源标注遵守 `README.md` §三（LIVE / STATIC / DISCREPANCY / INFERRED）。**无来源字段一律不写。**

## 通用约定

- **传输层**：全部 GraphQL over POST，URL 形态 `POST /service/udc/graphql?<RootField>`（root field 同时作为 URL 上的 op 标识）
- **GraphQL 信封**（LIVE，`raw/s2r1_group_create.json` L9 等）：
  ```json
  {"query":"...graphql query text...","variables":{ ... }}
  ```
- **返回信封**（LIVE，全部 6 op 一致）：
  ```json
  {"traceId":"<19位数字字符串>","data":{"<RootField>":{"code":"BOOT_0000","data":{"content":<...>},"message":"SUCCESS","status":0}}}
  ```
  两处变体需注意（LIVE）：
  - `udcPageInfoUpdatePost` / `udcPageInfoUpdateDrafPost` 的返回**无 `code` 字段**：`{"traceId":...,"data":{"<RootField>":{"data":{"content":1},"message":"SUCCESS","status":0}}}`（`raw/s2r1_page_save_submit.json` L66 段、`raw/s2r1_page_save.json` L16 段）
  - `query` 类（`udcPortletSelectByAppIdAppGet`）同样含 `code: "BOOT_0000"`
- **认证**：`SY_ACCESS_TOKEN` cookie（凭据只按路径引用，不落盘）
- **业务成功判定**：`code=="BOOT_0000" && status==0 && message=="SUCCESS"`。**HTTP 200 单独不构成成功**（阶段 1 已实证 HTTP 200 时 DB 可零落行）

---

# 1. 建分组 — `udcPortletCreatePost`

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPortletCreatePost` | LIVE `raw/s2r1_group_create.json` L7 |
| method | POST | LIVE 同上 |
| GraphQL 类型 | `mutation udcPortletCreatePost($body: udcPortletCreatePostInputBody)` | LIVE 同上 L9（query 文本） |
| 后端落点 | `PortletController` / 类级 `udc/portlet` / 方法 `/create`，入参 `PortletDto` | STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` §5.2.1 |
| 落表 | `udc_test2.udc_portlet`（type=0）+ 门户 `portal_test2.portal_portlet_category`（同步） | LIVE DB 回读 |

## 1.1 请求 schema

| 字段 | 类型 | 必填 | LIVE 样例值 | 说明 | 来源 |
|---|---|---|---|---|---|
| `variables.body.appId` | string(数字串) | 是 | `"8704025620829192834"` | 目标应用 id | LIVE raw L9 |
| `variables.body.terminalType` | enum string | 是 | `"PC"` | 枚举见 `enums.md` §terminalType | LIVE raw L9 |
| `variables.body.type` | enum string | 是 | `"GROUP"` | 建分组固定 `GROUP`；枚举见 `enums.md` §type | LIVE raw L9 |
| `variables.body.name` | string | 是 | `"S2GROUP20261017"` | 分组名称；DB 唯一键 `uk_udc_portlet_name(app_id,name,type)` | LIVE raw L9 + STATIC 唯一键 |

> 请求体只观测到上述 4 字段（`PortletDto` 的其余字段此入口未传）。**未传字段不写期望值**。

## 1.2 响应 schema（`data.udcPortletCreatePost.data.content`）

| 字段 | 类型 | LIVE 值样例 | 语义 / 注意 | 来源 |
|---|---|---|---|---|
| `appId` | string | `"8704025620829192834"` | 回显 | LIVE raw L11 |
| `groupId` | string \| null | `null` | 分组的父分组恒 null | LIVE raw L11 |
| `guid` | string \| null | `null` | **建分组响应内为 null**，落库后 `udc_portlet.guid=-4399224624179689670`（DISCREPANCY，见下） | LIVE raw L11 + DB |
| `id` | string(数字串) | `"-2821989384273517473"` | 新建分组 id，**后续建栏目 groupId 用它** | LIVE raw L11 |
| `name` | string | `"S2GROUP20261017"` | 回显 | LIVE raw L11 |
| `orderNo` | number | `0` | **恒 0，不反映落库值**（落库为 1）| LIVE raw L11 + DB（ROUTE Q6） |
| `pageRelationId` | string \| null | `null` | 分组无页面关联 | LIVE raw L11 |
| `portletList` | array \| null | `null` | 分组响应不返回子节点 | LIVE raw L11 |
| `publishState` | enum string \| null | `null` | **建分组响应内为 null**，落库 `publish_state=1`（DISCREPANCY，方向未知见 `enums.md` §4.2） | LIVE raw L11 + DB |
| `terminalType` | enum string | `"PC"` | 回显请求值 | LIVE raw L11 |
| `type` | enum string | `"GROUP"` | 回显请求值 | LIVE raw L11 |

**DISCREPANCY 登记（响应 vs DB，不静默取一）**——本表全部行 = 响应侧 `LIVE`（raw）+ DB 侧 `LIVE` 双源对照
| 字段 | 响应值（LIVE/raw） | DB 落库值（LIVE/DB） | 判读 |
|---|---|---|---|
| `orderNo` | `0` | `udc_portlet.order_no = 1` | 响应不反映落库；断言 orderNo 只能用 DB 或 `SelectByAppIdAppGet` 回读（= 建前 max+1） |
| `guid` | `null` | `udc_portlet.guid = -4399224624179689670` | 响应缺；guid 由服务端生成，前端无法预知 |
| `publishState` | `null` | `udc_portlet.publish_state = 1` | 响应缺；**本租户库**落库默认 1（`udc_test2` 157/157）。⚠️ 接口字符串 `UNPUBLISH` 与 DB `1` 方向未知，见 `enums.md` §4.2，**不得据此断言 DB 1 = 已发布或未发布** |

## 1.3 LIVE 样例（原文）

请求：
```json
{"body":{"appId":"8704025620829192834","terminalType":"PC","type":"GROUP","name":"S2GROUP20261017"}}
```
响应：
```json
{"traceId":"17922483013725158661","data":{"udcPortletCreatePost":{"code":"BOOT_0000","data":{"content":{"appId":"8704025620829192834","groupId":null,"guid":null,"id":"-2821989384273517473","name":"S2GROUP20261017","orderNo":0,"pageRelationId":null,"portletList":null,"publishState":null,"terminalType":"PC","type":"GROUP"}},"message":"SUCCESS","status":0}}}
```
raw 指针：`raw/s2r1_group_create.json` L7（请求）/ L11（响应）

## 1.4 枚举映射

见 `enums.md`：`type`、`terminalType`、`category`（响应未返 category，落库为 1=ADVANCED）、`publishState`。

## 1.5 前置条件（LIVE）

| 条件 | 证据 | 来源 |
|---|---|---|
| 建分组本身无前置分组要求（本应用 0 分组时直接成功） | `raw/s2r1_group_create.json` 成功 + DB 0→1 行 | LIVE |
| 建分组产生的门户分类挂在**应用根**下（parent=app_code），不需要父分类先存在 | DB：`portal_test2.portal_portlet_category` 建分组同秒生成，`parent_category_code='datamigration9000000000000000001'` | LIVE |
| 名称需符合唯一键 `(app_id,name,type)` | 唯一键 `uk_udc_portlet_name(app_id,name,type)` | STATIC（失败形态 UNVERIFIED） |

> **反向依赖登记（供建栏目参考）**：应用内若无 type=0 行，建栏目表单的「栏目分组」下拉为空且该字段 required → **这是建栏目 op 的前置条件，不是建分组的前置条件**。22:36 与 22:45 的对比支持该依赖存在，但失败文案未取到，真因保留 `UNVERIFIED-22:36真因未定论`（见 §1.6）。

## 1.6 失败形态

| 形态 | 表现 | 来源 / 等级 |
|---|---|---|
| **前置校验拒绝（请求不出网）** | 前端 antd 表单校验拦截，网络层无该 op 请求。触发条件：必填项为空（如「栏目分组」未选）。**本 op（建分组）只一个必填「分组名称」，未观测到拒绝实例**；同机制在建栏目 op 已观测（见 §2.5） | 机制 LIVE（§2.5 实测）+ 本 op **未观测** |
| 业务失败 | `code != BOOT_0000` 或 `status != 0`，`message` 带原因 | 信封结构 LIVE；本 op 未观测失败实例 |
| 重名冲突 | 未观测（唯一键 `uk_udc_portlet_name(app_id,name,type)` 存在） | STATIC 唯一键；**失败形态 UNVERIFIED** |

> **22:36 首轮"静默失败"的准确登记（不写成已定论）**：
> - 事实（LIVE）：22:36 该 op 在网络层**确有请求记录**（CDP `requestWillBeSent` 抓到 url + postData，HTTP 200），但响应体未取到（`getResponseBody` 在导航后失效），且 DB **零落行**。
> - 事实（LIVE）：22:45 先建分组后，同一表单一次提交即成功（DB 落 1 行 + 完整响应体）。
> - **推断（INFERRED，非已证实）**：首轮失败最可能因「栏目分组下拉为空」导致列端状态不完整/后端拒绝；但 22:36 请求已出网这一事实**不支持「纯前端拦截」解释**，故真因**尚未定论**，登记为 `UNVERIFIED-22:36真因未定论`。
> - 纪律：不得把「下拉为空导致拦截」写成已证实的失败形态；契约只承诺已观测到的形态（必填项缺失 → 前端校验），其余留 UNVERIFIED。

---

# 2. 建栏目 — `udcPortletCreatePortletPost`

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPortletCreatePortletPost` | LIVE `raw/s2r1_portlet_create.json` L22 |
| method | POST | LIVE 同上（`raw/s2r1_portlet_create.json` call.method） |
| GraphQL 类型 | `mutation udcPortletCreatePortletPost($body: udcPortletCreatePortletPostInputBody)` | LIVE 同上 L24 |
| 后端落点 | `PortletController` 方法级 path **`/create-portlet`**，入参 **`PageDefinitionDto`** → `PortletService#createPortlet(PageDefinitionDto)` L133-149 | STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` L31 / L106 / L110（**原文路径与 DTO 已补全**；`udcPortletCreatePortletPost` 是前端 GraphQL op 名，非后端路径） |
| 落表 | `udc_test2.udc_portlet`（type=1）+ `udc_test2.udc_page_info`（page_type='PORTLET'，按 pageItems 端数） | LIVE DB |

## 2.1 请求 schema

| 字段 | 类型 | 必填 | LIVE 样例值 | 说明 | 来源 |
|---|---|---|---|---|---|
| `variables.body.appId` | string | 是 | `"8704025620829192834"` | 应用 id | LIVE raw L24 |
| `variables.body.caption` | string | 是 | `"S2PROBE20261017"` | 栏目显示名（落 `udc_page_info.caption`） | LIVE raw L24 |
| `variables.body.curTerminalType` | enum string | 是 | `"PC"` | 当前端（与 pageItems 端对应） | LIVE raw L24 |
| `variables.body.groupId` | string | 是 | `"-2821989384273517473"` | 所属分组 id（必须先有 type=0 行） | LIVE raw L24 |
| `variables.body.pageItems` | array\<object\> | 是 | `[{"menuId":"-2821989384273517473","urlType":"PC"}]` | 每端一项；端数决定生成几条 page_info | LIVE raw L24 + DB（page_info 1 行） |
| `variables.body.pageItems[].menuId` | string | 是 | `"-2821989384273517473"` | **LIVE 观测到传的是分组 id，非栏目 id**（前端既有形态，登记备查） | LIVE raw L24 |
| `variables.body.pageItems[].urlType` | enum string | 是 | `"PC"` | 端类型，见 `enums.md` §urlType | LIVE raw L24 |
| `variables.body.pageType` | enum string | 是 | `"PORTLET"` | 页面类型 | LIVE raw L24 |
| `variables.body.pageUrl` | string | 是 | `"S2PROBE20261017"` | 栏目标识（无横线）。**注意：`ROUTE L71` 的「测试命名避 `-`」是给测试对象起名的约定（便于辨认），不是平台校验规则** —— 在盘无任何「横线被拒」的证据；15:35 / 16:10 两次带 `-` 的尝试失败原因是渲染进程卡死 + DB 0 行，与横线无关 | LIVE raw L24；**命名约定 = STATIC/约定，非平台规则** |

## 2.2 响应 schema（`data.udcPortletCreatePortletPost.data.content`）

| 字段 | 类型 | LIVE 值 | 说明 | 来源 |
|---|---|---|---|---|
| `appId` | string | `"8704025620829192834"` | 回显 | LIVE raw L26 |
| `groupId` | string | `"-2821989384273517473"` | = 请求 groupId（落 DB `group_id`） | LIVE |
| `guid` | string \| null | `null` | 响应缺；DB `guid=-7672842714696691825`（DISCREPANCY） | LIVE + DB |
| `id` | string | `"5810462779490574369"` | 新建栏目 id | LIVE |
| `name` | string | `"S2PROBE20261017"` | = 请求 caption | LIVE |
| `orderNo` | number | `0` | **恒 0，不反映落库**（落库 2） | LIVE + DB（Q6） |
| `pageRelationId` | string | `"8758458332069176381"` | **门户定义 portlet_id 就取这个值**（Q2） | LIVE + DB |
| `portletList` | array \| null | `null` | 创建响应不返回子节点 | LIVE |
| `publishState` | enum string \| null | `null` | 响应缺；DB `publish_state=1` | LIVE + DB |
| `terminalType` | enum string | `"PC"` | 回显 curTerminalType | LIVE |
| `type` | enum string | `"PORTLET"` | 固定 PORTLET | LIVE |

**DISCREPANCY 登记**——本表全部行 = 响应侧 `LIVE`（raw）+ DB 侧 `LIVE` 双源对照
| 字段 | 响应（LIVE/raw） | DB（LIVE/DB） | 判读 |
|---|---|---|---|
| `orderNo` | `0` | `2` | 同 §1.2，只能 DB/选择器回读 |
| `guid` | `null` | `-7672842714696691825` | 服务端生成 |
| `publishState` | `null` | `1` | 本租户库默认落库值（方向未知，见 `enums.md` §4.2） |

## 2.3 LIVE 样例

请求：
```json
{"body":{"appId":"8704025620829192834","caption":"S2PROBE20261017","curTerminalType":"PC","groupId":"-2821989384273517473","pageItems":[{"menuId":"-2821989384273517473","urlType":"PC"}],"pageType":"PORTLET","pageUrl":"S2PROBE20261017"}}
```
响应：
```json
{"traceId":"17922483545794594178","data":{"udcPortletCreatePortletPost":{"code":"BOOT_0000","data":{"content":{"appId":"8704025620829192834","groupId":"-2821989384273517473","guid":null,"id":"5810462779490574369","name":"S2PROBE20261017","orderNo":0,"pageRelationId":"8758458332069176381","portletList":null,"publishState":null,"terminalType":"PC","type":"PORTLET"}},"message":"SUCCESS","status":0}}}
```
raw 指针：`raw/s2r1_portlet_create.json` L22 / L26

## 2.4 前置条件（LIVE）

| 条件 | 证据 |
|---|---|
| 「栏目分组」required 且必须有值 | `raw/s2r1_portlet_form.json`（`required=True`，提交前已 `selected="S2GROUP20261017"`） |
| 「栏目名称」「栏目标识」「适配终端」均 required | 同上（三项 `required=True`） |
| 栏目标识**建议不含 `-`**（**测试命名约定，非平台规则**） | `ROUTE` L71「测试命名避 '-'」= 为便于辨认而定的起名习惯；**全盘零条「横线被拒」LIVE 记录**（15:35 / 16:10 两次带横线失败系渲染进程卡死 + DB 0 行）。**不得当作平台校验断言** |
| 适配终端默认只勾 PC | `raw/s2r1_portlet_form.json`：`PC=checked true / MOBILE=checked false` |
| 建栏目**不触发**门户分类同步（仅 type=GROUP 走分类同步） | STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` §2.2「仅 type=0 走」 |

## 2.5 失败形态

| 形态 | 表现 | 来源 / 等级 |
|---|---|---|
| **前置校验拒绝（请求不出网）** | 必填项为空时前端 antd 表单校验拦截，网络层无该 op 请求。本 op 有 4 个必填（栏目分组/栏目名称/栏目标识/适配终端），其中「栏目分组」在应用无 type=0 行时下拉为空 | 机制 **LIVE**（表单快照 `raw/s2r1_portlet_form.json` 四项 `required=True`）；**具体失败文案未取到 → UNVERIFIED**。**22:36 那次不列为本机制的实证**：该轮网络层确有 `requestWillBeSent`（HTTP 200）但响应体缺失 + DB 零落行，真因 `UNVERIFIED-22:36`（见 §1.6） |
| 业务失败 | `code/status/message` 非成功态 | 信封结构 LIVE；本 op 未观测失败实例 |
| 级联副作用（非失败，但必知） | 建栏目同时创建 `udc_page_info`（按 pageItems 端数）+ op-log 1 条（sub_module=40，2 元素） | LIVE DB + op-log |

> **22:36 真因：不写成已定论**（与 §1.6 同一登记），标 `UNVERIFIED-22:36真因未定论`。

---

# 3. 删栏目 / 删分组 — `udcPortletDeleteIdPost`

> **同一 op 服务两种对象**：传栏目 id 删栏目，传分组 id 删分组（含级联）。

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPortletDeleteIdPost` | LIVE `raw/s2r1_delete_portlet.json` L7、`raw/s2r1_delete_group.json` L7 |
| method | POST | LIVE 同上（两件 raw 的 call.method 均为 POST） |
| GraphQL 类型 | `mutation udcPortletDeleteIdPost($path: udcPortletDeleteIdPostInputPath)` | LIVE |
| 后端落点 | `PortletService#deleteById` | STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` §3 |

## 3.1 请求 schema

| 字段 | 类型 | 必填 | LIVE 样例 | 说明 | 来源 |
|---|---|---|---|---|---|
| `variables.path.id` | string(数字串) | 是 | 栏目 `"5810462779490574369"` / 分组 `"-2821989384273517473"` | 被删对象 id（`udc_portlet.id`） | LIVE raw 两件 L9 |

> 请求只有 `path.id` 一个字段。无 `type` 参数 —— **删栏目与删分组在前端无法从请求体区分**，只能由传入 id 对应的 DB 行 `type` 判定。

## 3.2 响应 schema（`data.udcPortletDeleteIdPost.data.content`）

| 字段 | 类型 | LIVE 值 | 说明 | 来源 |
|---|---|---|---|---|
| `content` | number | `1` | 影响行数形态；两种删除均返回 1 | LIVE 两件 L11 |

## 3.3 LIVE 样例

删栏目：
```json
{"path":{"id":"5810462779490574369"}}
→ {"traceId":"17922503199724992371","data":{"udcPortletDeleteIdPost":{"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}}}
```
删分组：
```json
{"path":{"id":"-2821989384273517473"}}
→ {"traceId":"17922509930521996766","data":{"udcPortletDeleteIdPost":{"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}}}
```
raw 指针：`raw/s2r1_delete_portlet.json` L7/L11；`raw/s2r1_delete_group.json` L7/L11

## 3.4 级联语义（LIVE 实测，非推测）

| 删除对象 | 级联效果 | 证据（LIVE DB 回读） |
|---|---|---|
| 栏目（type=1） | `udc_portlet` 1 行删 + `udc_page_info`（relation_group_id=page_relation_id）删 + 门户 `portal_portlet_definition` **软删**（delete_flag 0→1） | page_info 1→0 行；definition delete_flag=1，update_time=23:18:39 |
| 分组（type=0） | `udc_portlet` 1 行删 + 门户 `portal_portlet_category`（category_code=分组 id）**物理删** | category 1→0 行 |

## 3.5 前置条件 / 顺序约束（LIVE）

- **必须先删栏目再删分组**：`deleteById(GROUP)` 会级联删除子栏目（STATIC §3.2 L300-311），先删分组会失去「删栏目」独立证据（裁定 H3）。
- 删除入口需**真实 hover**（`Input.dispatchMouseEvent`）才出现 `filled-more` 图标（Q7）；JS `dispatchEvent(mouseover)` 不触发。
- 确认弹窗文案可作为对象类型旁证（LIVE）：
  - 删栏目 → 「删除静态栏目页面 / 您确定要删除S2PROBE20261017页面吗？」
  - 删分组 → 「删除文件夹 / 您确定要删除文件夹S2GROUP20261017吗？」

## 3.6 失败形态

| 形态 | 表现 | 来源 |
|---|---|---|
| id 不存在 | 未观测 | — （不写猜测） |
| 本地事务成功但 Dubbo 门户删失败 | 理论上会留下门户脏行（Dubbo 不在本地事务内） | STATIC §3.3；**本轮未观测**。注：原记「H2 复查结果为零残留」需收窄 —— 门户侧**有意**保留 `delete_flag=1` 的软删行（§3.7.3），那不是脏行；「零残留」仅指**无 flag=0 的悬挂活跃行**。 |
| 软删 vs 物理删 | **UDC 侧物理删 / 门户侧软删**（§3.7 逐表实证，原「定义软删 / 分类物理删」的二分已细化到表级） | LIVE DB §3.7 |

## 3.7 删除语义判定（DB 只读回读，2026-10-18 02:50）

> 本节为 HANDOFF #C-04（PORTLET-S2-DEL）追加。**纯只读 DB + 既有 LIVE 抓包；零 /service、零页面操作、零新写。**
> **页面可见性未验证（SSO 窗口待补）** —— 本节的「删除生效」仅指 DB 层，不得据此声称页面侧 PASS。

### 3.7.1 `udc_portlet`：物理删除（无软删列）

```sql
DESC udc_test2.udc_portlet;
-- 20 列：id, create_time, tenant_id, update_time, version, guid, backup_code,
--        owner_code, publish_state, app_id, group_id, name, order_no,
--        page_relation_id, terminal_type, type, category, template_type, original_id
-- 无 is_deleted / delete_flag / state / status 任一列
```

```sql
SELECT id, name, type FROM udc_test2.udc_portlet WHERE id IN (
  '5810462779490574369',   -- 被删栏目
  '-2821989384273517473'); -- 被删分组
```

**结果：两行均 `0 rows`（NOT_FOUND）。**

```sql
SELECT COUNT(*) FROM udc_test2.udc_portlet
WHERE name LIKE '%S2PROBE%' OR name LIKE '%S2GROUP%';
-- → 0
```

**判定**：`udc_portlet` 无软删列 ⇒ 删除只能是**物理 DELETE**。两个被删对象 id 查无、探针名零残留 ⇒ **物理删除成立（LIVE）**。

### 3.7.2 级联范围（逐表回读）

| 表 | 判定 | SQL 与结果 |
|---|---|---|
| `udc_portlet` | **物理删** | `SELECT ... WHERE id IN(栏目id,分组id)` → **0 rows**；`name LIKE '%S2PROBE%'/'%S2GROUP%'` → **0** |
| `udc_page_info` | **物理删** | 该表 32 列，软删相关仅 `publish_state`/`schema_state`（是状态非删除标记）；`WHERE caption LIKE '%S2PROBE%' OR caption LIKE '%S2GROUP%'` → **0 rows** |
| `udc_portlet_group` | **零残留** | 14 列，无软删列；`WHERE name LIKE '%S2GROUP%' OR name LIKE '%S2PROBE%'` → **0** |
| `portal_test2.portal_portlet_category` | **物理删** | 该表 **无 delete_flag 列**；`WHERE category_code=分组id OR category_name LIKE '%S2GROUP%'` → **0** |
| `portal_test2.portal_portlet_definition` | **软删（delete_flag 0→1），且残留行保留** | 见 §3.7.3 |

### 3.7.3 门户 definition 侧：软删残留（关键，且带一个必须标注的语义疑点）

```sql
SELECT id, portlet_id, name, delete_flag, create_time, update_time, app_id
FROM portal_test2.portal_portlet_definition
WHERE id = 329969732608628974;
```

| 字段 | 值 |
|---|---|
| id | 329969732608628974 |
| portlet_id | `8758458332069176381` |
| name | `datamigration9000000000000000001.S2PROBE20261017.caption` |
| **delete_flag** | **1** |
| create_time | 2026-10-17 22:47:38（= 建栏目时刻） |
| **update_time** | **2026-10-17 23:18:39（= 删栏目时刻）** |
| app_id | `datamigration9000000000000000001` |

**判定**：`udc_portlet` 行被物理删除，但门户定义行**未删、仅置 `delete_flag=1`**
⇒ **两层删除语义不同：UDC 侧物理删 / 门户侧软删**。行仍在表中，靠 `delete_flag` 过滤。

**⚠️ 必须登记的语义疑点（不影响上述判定，但禁止反向使用该列）**：

```sql
SELECT app_id, SUM(delete_flag=0) active, SUM(delete_flag=1) deleted, COUNT(*) total
FROM portal_test2.portal_portlet_definition
GROUP BY app_id HAVING total>=3 ORDER BY total DESC;
```

| app_id | active | deleted | total |
|---|---|---|---|
| app9000000000000000001 | 166 | 130 | 296 |
| **datamigration9000000000000000001** | **0** | **149** | **149** |
| znxmglptcopy5791640252914287064 | 0 | 84 | 84 |
| datamigration9000000000000000001 | 0 | 42 | 42 |
| xiangmuguanli9000000000000000001 | 6 | 6 | 12 |

- 本应用 **149/149 全部 `delete_flag=1`**，包括 2026-10-12 批量导入的 148 行。
- 另有 2 个 app 同样 0 active。
- ⇒ **`delete_flag=1` 不能单独作为「已删除」判据**。**本契约只把它用作「该行在删栏目后变为 1」这一时序证据**
  （同一行的 `update_time` 从建栏目时刻跳到删栏目时刻），**不**用它做全表增量统计。

#### PORTLET-D1｜`delete_flag` 真实语义域（2026-10-18 03:30，切片 #C-05）

**结论等级：已定位（机制层）/ 一处前序表述被实证推翻。**

##### D1-① 权威定义（STATIC，源码级，非反编译推断）

门户侧实体 `com.seeyon.portal.domain.entity.PortalPortletDefinition`
（源码：`backend/portal/portal-biz/src/main/java/com/seeyon/portal/domain/entity/PortalPortletDefinition.java` **L117-119**）：

```java
@Column(name = "delete_flag", columnDefinition = "TINYINT(1) COMMENT '栏目删除标识:第三方栏目会逻辑删除'")
@EntityAttribute(value = "栏目删除标识:第三方栏目会逻辑删除", dataType = DataType.BOOLEAN)
private Boolean deleteFlag = false;
```

**DDL 注释与实体注解原文一致：「栏目删除标识:**第三方栏目**会逻辑删除」**，实体默认值 `false`。

DTO 侧同样带此注解（CFR 反编译 `udc-portal-5.3.517`
`com/seeyon/udc/portal/dto/PortalPortletDefinitionDto.class` → L95）：

```java
@DtoAttribute(value = "栏目删除标识:第三方栏目会逻辑删除")
private Boolean deleteFlag;
```

⇒ **语义定义明确：`delete_flag=1` = 该栏目被逻辑删除（仅第三方栏目走逻辑删）。**

##### D1-②-a 主写入路径代码原文（`deletePortletByIds`，本环境唯一业务可达）

`PortalPortletDefinitionService.deletePortletByIds(String appCode, List<String> portletIds)`
（同文件 **L1572-1591**，方法注释原文：`批量删除设计态栏目接口,逻辑删除`）：

```java
Wrapper wrapper = new Wrapper(PortalPortletDefinition.class);
if (StringUtils.isNotBlank(appCode)) wrapper.and().andEqualTo("appCode", appCode);
wrapper.and().andIn("portletId", portletIds);
wrapper.and().andEqualTo("dataStatus", PortalConstant.DATA_STATUS_0);   // 只筛设计态
List<PortalPortletDefinition> definitionList = portalPortletDefinitionDao.selectListByWrapper(wrapper);
if (CollectionUtils.isNotEmpty(definitionList)) {
    for (PortalPortletDefinition definition : definitionList) {
        definition.setDeleteFlag(true);                                  // ← 路径②
    }
    count = portalPortletDefinitionDao.versionNoUpdateBatchIgnoreVersion(definitionList);
}
```

##### D1-②-b 全量写入点（全文件 `setDeleteFlag` 共 **5 处**：3 处 true / 2 处 false）

> **本节经两轮修正**：首版写「唯一 1 处」→ 二版写「3 处」→ 本版按 main VERDICT #C-05-FINAL 补全为 **5 处**。
> 我两次都漏了 false 分支。教训见 §八-4：**「N 处」这类全域计数必须给出搜索命令与命中总数**（D8 条款）。

**搜索命令（可复跑）**：
```bash
grep -n "setDeleteFlag(" \
  backend/portal/portal-biz/src/main/java/com/seeyon/portal/domain/service/portlet/PortalPortletDefinitionService.java
```
**命中总数 = 5**，逐条归属如下：

| # | 行号 | 值 | 所属方法（签名行） | 触发条件 | 本环境可达 |
|---|---|---|---|---|---|
| ① | **L1347** | `true` | `deleteThirdPortlet(ThirdPortletRequestDto)`（L1336） | 删**第三方栏目**：校验 orgId → 置 true → 删 PC/移动权限 → 进回收站 | **否**（本库无 type=3 行，见下） |
| ② | **L1585** | `true` | `deletePortletByIds(String, List<String>)`（L1573） | 批量删**设计态**栏目，筛 `dataStatus=0` | **是**（UDC 删栏目走这条） |
| ③ | **L2683** | `true` | `resetDataVersion(Long, PortalDataTypeEnum)`（L2680）分支 `PORTLET_DELETE(6)` | 运维接口置删 | 需人工调 `reset-data` |
| ④ | **L1617** | `false` | `restoreById(Long)`（L1593） | 回收站**还原**栏目 | 需走还原入口 |
| ⑤ | **L2686** | `false` | `resetDataVersion(Long, PortalDataTypeEnum)`（L2680）分支 `PORTLET_ENABLE(7)` | 运维接口置启用 | 需人工调 `reset-data` |

⇒ **`delete_flag` 是标准的「逻辑删除开关」：3 处置 1（删）、2 处置 0（还原/启用）。**
这从正反两面印证了 D1-① 的语义定义，比只看置 true 更完整 ——
**有对称的 restore 路径，说明它确实可逆，不是单向墓碑。**

**路径适用域（必须写明，否则会误归因）**：

| 路径 | 适用对象 |
|---|---|
| ① `deleteThirdPortlet` | **仅 `portlet_type = 3 (DYNAMIC_THIRD_COLUMN)`** |
| ② `deletePortletByIds` | 任意设计态（`data_status=0`）栏目，**不限 type** |

⚠️ **枚举同名陷阱**：`PortletTypeEnum` 在本源码树有 **4 个同名类**，取值不同：

| 全限定名 | 取值 | 备注 |
|---|---|---|
| `com.seeyon.portal.**enums**.PortletTypeEnum` | 0/1/2/**3** | **实体字段用的是这个**（`PortalPortletDefinition.java` L104-107） |
| `com.seeyon.portal.**portlet.enums**.PortletTypeEnum` | 0/1/2（**无 3**） | main 提示的另一个，勿混引 |
| `com.seeyon.udc.portal.enums.PortletTypeEnum` | 0/1/2/**3** | UDC 侧同名 |
| `com.seeyon.udc.page.enums.PortletTypeEnum` | 另有定义 | UDC page 侧 |

⇒ 引用时必须带**全限定包名**，只写「PortletTypeEnum」会产生歧义。

**本应用适用域实测**：本应用 149 行 `portlet_type` **全部 = 0**（全库 788 行亦无 1/2/3）
⇒ **③ 之外的置 true 路径中，本应用只能用 ②，不可能是 ①（第三方路径）**。

##### D1-②-c 风险登记：`deleteThirdPortlet` 缺类型防护（STATIC-源码级 + UNVERIFIED-RISK）

**结论：`deleteThirdPortlet` 方法体内不做任何 `portletType` 校验，属缺防护。**

方法边界与区间内命中数（**先给签名行 + 结束行成对，再给区间计数**，D8 实施规范 a）：

```bash
F=backend/portal/portal-biz/src/main/java/com/seeyon/portal/domain/service/portlet/PortalPortletDefinitionService.java
sed -n '1336p' $F   #     public Long deleteThirdPortlet(ThirdPortletRequestDto thirdPortletRequestDto) {
sed -n '1364p' $F   #     }
sed -n '1365p' $F   # （空行）
for kw in portletType PortletType Wrapper andEqualTo; do sed -n '1336,1364p' $F | grep -c "$kw"; done
# 输出：0 / 0 / 0 / 0
```

⇒ **deleteThirdPortlet = L1336–L1364，区间内 `portletType`、`Wrapper`、`andEqualTo` 命中均为 0。**
它只校验 `orgId`（同集团），**不检查目标行 `portlet_type` 是否为 3**。

**本文件 `portletType` 全部 14 处逐处归属（程序输出，非人工点数）**

```bash
grep -c "portletType\|PortletType" $F      # => 14
grep -n "portletType\|PortletType" $F | cut -d: -f1 \
  | while read L; do echo "L$L: $(sed -n "${L}p" $F | sed 's/^ *//')"; done
```

按**代码形态**分三类（分类依据是每行原文，不是印象）：

| 形态 | 行号 | 处数 | 说明 |
|---|---|---|---|
| ① `import` | L92 | 1 | 仅导入，非使用 |
| ② **Wrapper 等值筛选**（真正把 type 变成查询条件） | **L1110 / L1392 / L1459** | **3** | 全部是 `andEqualTo("portletType", DYNAMIC_THIRD_COLUMN)` |
| ③ 其余（取值比较 / set / paraMap） | L375 L1123 L1200 L1210 L1323 L1517 L1661 L1779 L2029 L2450 | 10 | 判断或赋值，**不是查询筛选** |

**逐处归属（②③ 中与「第三方栏目」有关的）**：

| 行号 | 所属方法（签名行） | 原文形态 |
|---|---|---|
| **L1110** | `selectThirdPortletByCategoryCode`（L1105） | `andEqualTo("portletType", DYNAMIC_THIRD_COLUMN)` |
| **L1392** | **`stopThirdPortletsByAppId`（L1388）** | `andEqualTo("portletType", DYNAMIC_THIRD_COLUMN)` —— **不属 deleteThirdPortlet** |
| **L1459** | `selectOptionThirdPortlets`（L1449） | `andEqualTo("portletType", DYNAMIC_THIRD_COLUMN)` |
| L1779 | `updateThirdPortletStatus`（L1776） | `paraMap.put("portletType", …)` ← **MyBatis 参数，不是 Wrapper** |
| L1200/L1210 | `addPortletResourceAth`（L1195） | `if (dto.getPortletType() == …)` 分支判断 |
| L2029 | `filterDefinition`（L1953） | `if (…getPortletType() == …)` 分支判断 |
| L2450 | `savePortletAuth`（L2445） | `if (entity.getPortletType() == …)` 分支判断 |

⇒ **删除入口 `deleteThirdPortlet`（L1336–1364）在这 14 处中一处不占。**

> **自查更正（本版）**：我初稿把 L1779 也写成「Wrapper 更新筛选」，并说「带校验语义的 4 处」。
> **错了** —— L1779 原文是 `paraMap.put(...)`，是 MyBatis 参数不是 Wrapper；
> 真正的 Wrapper 筛选是 **3 处**（L1110/L1392/L1459）。
> 这又是一次「按印象归类没逐行看原文」。现按程序输出逐行重列，并给出归类依据。
> 结论方向不变（删除入口 0 处），但**「4 处」这个数字是我编的，已改 3 处**。

**为何这是风险**：`deleteThirdPortlet` 的入参 `ThirdPortletRequestDto` 只带 id，
服务端不自行判定「该 id 是否为第三方栏目」，而是**由调用方保证**。
⇒ 若上层把非 `type=3` 的 id 传进来，本方法仍会执行 `setDeleteFlag(true)`（L1347）并删权限。
**调用方是否真的做了前置过滤，本切片未取证 ⇒ 标 `UNVERIFIED-RISK`，不作「必然可被利用」的升级。**
（旁证：同类筛选在 L1110/L1459 都显式写了 `andEqualTo("portletType", DYNAMIC_THIRD_COLUMN)`，
唯独删除入口没有 —— **筛选是同层惯例，删除是明显例外**，此对比支持「遗漏」而非「有意设计」，
但仍是推断，不作定论。）

**orgId 校验的真实来源与其门槛（main 2026-10-18 04:0x 补，FIX4 ③ 的落地）**

`deleteThirdPortlet` 内部只有一句 `if (!thirdPortletRequestDto.getOrgId().equals(entity.getOrgId())) throw UNAUTHORIZED;`（**L1340-1342**）。
**它比较的是「调用方传进来的 orgId」vs「目标行的 orgId」** —— 服务端不自己取当前登录组织。

调用方是唯一入口 `PortletController`（`backend/portal/portal-web`）：

```bash
$ sed -n '325,334p' PortletController.java
L325  @RestApiOperation(value = "删除第三方栏目", ...)
L326  @PostMapping("third-portlet/delete")
L327  @HasRole({RoleName.ORG_ADMIN, PortalConstant.SYSTEM_PORTAL_ROLE_CODE})
L328  public SingleResponse<Long> deleteThirdPortlet(@MultiRequestBody Long id) {
L329      ThirdPortletRequestDto dto = new ThirdPortletRequestDto();
L330      dto.setId(id);
L331      dto.setOrgId(super.getLoginOrgId());   // ← 来自登录态
L332      dto.setUserId(super.getUserId());
L333      return portletDefinitionAppService.deleteThirdPortlet(SingleRequest.from(dto));
L334  }
```

`super.getLoginOrgId()` 落在 `boot-starter-web/BaseController.java` **L23-25**：
```java
public Long getLoginOrgId() { return RequestContext.get().getLoginOrgId(); }
```
⇒ **`orgId` 的唯一来源是登录态**，客户端无法伪造（`@MultiRequestBody Long id` 只收 id）。

**因此攻击面不在「能否伪造 orgId」，而在「登录态的 orgId 是否恰好等于目标行的 orgId」**：

```sql
SELECT org_id, COUNT(*) FROM portal_portlet_definition GROUP BY org_id;
-- 1 行：org_id = -1，COUNT = 788（全库 788 行，含本应用 149 行）
```

⇒ 库内 **788/788 行 org_id 全为 -1**。若登录态 `loginOrgId` 也为 **-1**（平台/根组织态），
则 L1340 的等值比较**恒真**，orgId 守卫等于不存在 —— 无需知道目标栏目的 orgId。

**但入口还有角色闸门（本段是 04:0x 新增的收紧，不能漏）**：
`@HasRole({RoleName.ORG_ADMIN, PortalConstant.SYSTEM_PORTAL_ROLE_CODE})`
⇒ 调用者必须是**组织管理员**或**系统门户角色**。这使该风险从「任一登录用户可越界删」收窄为
「**具备管理员角色的账号，可对本组织内任意 `portlet_type` 的栏目执行第三方删除流程**」。

**证据等级与禁止升级（按 FIX4 要求逐字保留）**
- **STATIC-源码级**：方法体内 `portletType`/`Wrapper`/`andEqualTo` 命中 **0**（区间 1336–1364）；`ThirdPortletRequestDto` 无判定字段
- **STATIC-源码级**：`orgId` 来源唯一 = `getLoginOrgId()`；入口角色 = `ORG_ADMIN` / `SYSTEM_PORTAL_ROLE_CODE`
- **DB**：`GROUP BY org_id` → 788 行全为 `-1`
- **未证（禁写为「已证实可利用」）**：登录态是否可取得 `loginOrgId = -1`、以及管理员能否对本组织 `type=0` 栏目走通该端点，本切片**均未做 LIVE 验证** ⇒ 仍标 **UNVERIFIED-RISK**

> **本条曾被 auditor 一度撤回**（称「判定条件在方法的 wrapper 里，L1386-1394」）。
> 经 main 与我各自按「签名行+结束行成对」独立复核：L1386-1394 属
> `stopThirdPortletsByAppId`（签名 **L1388**），**不在 deleteThirdPortlet 内**。
> auditor 已自行撤回并承认为「用行号顺序冒充作用域归属」。**本契约按复核结果写，不采纳撤回稿。**

另有 `resetDataVersion` 入口：`PortalSetController.resetDataVersion`
（`GET reset-data/{id}/{type}`，L366-385），属后台数据版本工具，不是用户删除路径。

**创建路径的反证**：`createPortlet(PortletDefinitionDesignerDto)`（**L1499-1539**）通篇
**未调用 `setDeleteFlag`** ⇒ 新建行取实体默认 `false`。这与 §3.7.3 的探针实测一致
（建栏目时刻该行 flag=0，删后翻 1）。

**为什么「UDC 侧不设」不会写出 null 覆盖默认值（补强，2026-10-18 03:45）**

DTO 侧 `deleteFlag` **无默认值（初值 null）**，门户实体默认 `false`。二者能共存，靠的是拷贝策略：

```java
// boot-core/.../BaseEntity.java L70-76
public void from(Object dto) {
    BeanCopier.copy(dto, this, BeanCopier.CopyStrategy.IGNORE_NULL, BeanCopier.defaultNoMatchingRule);
}
public void fromContainNull(Object dto) {
    BeanCopier.copy(dto, this, BeanCopier.CopyStrategy.CONTAIN_NULL, BeanCopier.NoMatchingRule.EXCEPTION);
}
```

`createPortlet` L1511/L1531 调用的是 **`entity.from(designerDto)` = `IGNORE_NULL`**
⇒ DTO 的 `null deleteFlag` **不覆盖**实体默认 `false` ⇒ 新建行落库必为 **0**。
（`fromContainNull` 虽会写入 null，但 `portal` 模块内**无任何调用点**，已全模块搜索确认。）

⇒ **UDC 建栏目路径在结构上不可能产出 `delete_flag=1`。** 这条比「代码里没看到 setDeleteFlag」更强：
不是「没找到」，而是**有明确的 null 忽略策略保证它不会被写成 null 或 1**。

##### D1-③ 148 行「导入即 1」—— 前序表述被推翻（这是本节最重要的一条）

原 §3.7.3 写「`create_time = update_time = …17:16:02`，**生成时就是 1**」。**该断言不成立于全部 148 行。**

实测 `create_time` 与 `update_time` 联合分布：

| 情形 | 行数 | 说明 |
|---|---|---|
| `create_time = update_time` | **65** | 建后再未改动（成因见 D1-③-b） |
| `create_time ≠ update_time` | **83** | 见下方精确秒分布 |

**83 行的精确秒分布（修正：不是「全部同一秒」）**

> **本条经修正**。我二版写「全部在同一秒 17:25:46」，**错了** —— 实测是 **6 个不同秒**。
> 这是我第二次在同一段里犯「未做精确分组就下全域断言」的错。

```sql
SELECT update_time, COUNT(*) FROM portal_portlet_definition
WHERE app_id='datamigration9000000000000000001'
  AND DATE(create_time)='2026-10-12' AND create_time<>update_time
GROUP BY update_time ORDER BY update_time;
```

| update_time | 行数 | 距 create(17:16:02) |
|---|---|---|
| 17:25:46 | 11 | +584 s |
| 17:25:48 | 7 | +586 s |
| 17:25:51 | 22 | +589 s |
| 17:25:54 | 1 | +592 s |
| 17:25:57 | 21 | +595 s |
| **17:26:00** | **21** | **+598 s** |
| **合计** | **83** | 6 个不同秒，差 584–598 s |

⇒ **正确表述**：这 83 行是「**导入后约 10 分钟，被 6 次独立批量操作置为 1**」，
**不是**「生成时就是 1」，也**不是**「一次操作同一秒完成」。

**为什么 6 个秒值 = 6 次独立调用（STATIC 支撑）**

`BaseMybatisDao.versionNoUpdateBatchIgnoreVersion` 在 MySQL（`parametersLimit = FINAL_PARAMETERS_LIMIT`）
下走**单条批量 UPDATE** ⇒ 一次调用只产生**一个** `update_time` 秒值。
⇒ 6 个秒值 = **6 次调用**，不是一次调用的多批分片。

**调用方已由 main 只读闭合（DB 证据，见 §3.7.3 D1-⑦ 残余2 已消除）**：
`udc_operation_log` 在同 6 个秒值的前 1 秒各有一条 `sub_module=6 (PORTLET_GROUP)` / `action_type=2 (DELETE)` 记录，
操作人 `-2638952494757493308`，分组名依次为
销售员门户(11) / 分总门户(7) / 事总门户(22) / 客开自定义栏目-勿删(1) / 本部总门户(21) / 平台门户(21)
—— **行数与 6 个秒值逐条对齐**。

**双维对齐（比单看秒值更强，2026-10-18 04:2x 独立复算）**

秒值分组只证明「有 6 个时间点」，不能证明「每个时间点恰对应一个分组」。
补做 `category_code` 维后，两个维度**互为 1:1**：

```sql
-- A 向：按分组看，每组是否组内同秒
SELECT category_code, COUNT(*) n, MIN(update_time) mn, MAX(update_time) mx,
       CASE WHEN MIN(update_time)=MAX(update_time) THEN 'SAME' ELSE 'DIFF' END
FROM portal_portlet_definition
WHERE app_id='datamigration9000000000000000001'
  AND DATE(create_time)='2026-10-12' AND create_time<>update_time
GROUP BY category_code ORDER BY mn;
-- 输出 6 行，same_sec 全为 SAME，n = 11/7/22/1/21/21，合计 83

-- B 向（逆命题）：每个秒值是否只落在一个分组上
SELECT update_time, COUNT(DISTINCT category_code) n_cat, COUNT(*) n_rows
FROM ... GROUP BY update_time ORDER BY update_time;
-- 输出 6 行，n_cat 全为 1
```

| # | category_code | 行数 | update_time | 组内同秒 |
|---|---|---|---|---|
| 1 | 7461931604267058275 | 11 | 17:25:46 | SAME |
| 2 | 2082886341477419864 | 7 | 17:25:48 | SAME |
| 3 | 1852890431448566325 | 22 | 17:25:51 | SAME |
| 4 | 3271005994774777712 | 1 | 17:25:54 | SAME |
| 5 | 60309101710821587 | 21 | 17:25:57 | SAME |
| 6 | 8144112359944309216 | 21 | 17:26:00 | SAME |
| | **合计** | **83** | 6 个秒 | 6/6 全 SAME |

⇒ **A 向证明「一次调用不会跨分组」（组内同秒）；B 向证明「一个分组不会被拆成多次调用」（秒内仅一分组）。**
两向合起来才是「**6 个分组 × 6 次调用**」的严格证据 —— 单看秒值分布只能得到「6 个时间点」。

⇒ **最终表述（main 2026-10-18 04:0x 定稿）**：「83 行 = 操作员一次性批量删除 **6 个栏目分组**的设计态操作，
经 UDC 删除链同步门户，**每分组一次调用，共 6 次**」。

> **三段证据链必须一起给，缺一段则不成立（main 逐段标注证据等级）**：
> ① **6 个秒值 = 6 条 UPDATE 语句**（STATIC-源码级）：MySQL 下 `versionNoUpdateBatchIgnoreVersion`
>    走单条批量 UPDATE ⇒ **一次调用只落一个 `update_time` 秒值**。
> ② **每个秒值只含 1 个 `category_code`**（LIVE-DB，B 向逆命题 `COUNT(DISTINCT category_code)=1`）
>    ⇒ **一条 UPDATE 只覆盖一个分组**。
> ③ **op-log 6 条 DELETE 与 6 个秒值逐条对应**（LIVE-DB，`create_time` = 秒值 −1s，
>    `domain_id` = `category_code`，操作人唯一）
> ①②③ 合起来 ⇒ **一次调用 = 一个分组 = 一个秒值 = 一条 op-log**，共 6 次。
>
> **⚠️ 两处必须写清的边界（否则数字会被误用）**：
> - `deletePortletByIds` 是**批量**接口（`portletIds` 为 List），「行数 11/7/22/1/21/21」是
>   **一次批量删除请求命中的行数**，**不是调用次数**；调用次数只能由「秒值数」得出（即 ①）。
>   另注：该业务动作在界面层是**删分组**（op-log `sub_module=6 PORTLET_GROUP`），
>   行数是分组内栏目数；因此「1 次界面动作」在服务层可能对应**多条** UPDATE 语句（本切片未能分离二者）。
> - op-log 的 `elements_size` = **27/15/45/3/43/43**，与行数 **11/7/22/1/21/21** 不等
>   （它含分组自身等元素）⇒ **禁止用 `elements_size` 反推行数或 portletIds 长度**。
>
> **若 ①（单条批量 UPDATE）日后被证伪**（例如分片提交），则「6 次调用」退化为「≥6 条语句」，
> 但「83 行非单次操作」这一结论与 D1-⑧ 约束**不受影响**。

（剩下 65 行 `create=update` 的成因已由 main 闭合，见 D1-③-b。）

**对那 65 行的进一步排查（2026-10-18 03:47，排除「批量更新不改 update_time」这一可能）**

曾怀疑：65 行其实也被更新过，只是批量更新跳过了 `update_time`，所以看着 `create=update`。
**该假设已被源码排除**：

```java
// UpdateInterceptor.java L106
boolean ignoreTime = mappedStatement.getId().endsWith("IgnoreTime");
// L206
if (!ignoreTime) { entityable.setUpdateTime(date); }
```

`versionNoUpdateBatchIgnoreVersion` 的方法名以 **`IgnoreVersion`** 结尾，**不含 `IgnoreTime`**
⇒ `ignoreTime=false` ⇒ **必然刷新 `update_time`**。

⇒ 所以 65 行的 `create_time = update_time` 是**真实的「建后未再被 UPDATE 过」**，
它们**在创建那一刻 `delete_flag` 就是 1**。

这与 D1-②「UDC 建栏目路径结构上不可能产出 1」并不矛盾 ——
**恰恰相反：它证明这 65 行不是走 UDC 建栏目 API 产生的**。

#### D1-③-b 65 行成因：拷贝继承 `delete_flag=1`（main 已闭合，证据等级 DB-INFERENCE）

> 本条原为残余 UNVERIFIED（「无日志可证」）。**main 用只读 DB 证据闭合了它**，本节如实采纳，
> 但**不升为 LIVE** —— 因为它是「分布对称性 + 源码语义」的推断，不是抓到那次操作本身。

**因果**：这 65 行是**从源应用拷贝过来时，把源侧已删行的 `delete_flag=1` 一并继承**的。

**证据 1｜后缀匹配的不对称性（DB）**

去掉 app 前缀与 `.caption` 后缀，用栏目名后缀去源应用 `app9000000000000000001` 匹配：

| 组 | 行数 | 源侧存在同名 | 源侧该名含 `flag=1` 行 |
|---|---|---|---|
| **65 组**（create=update） | 65 | **65** | **65（100%）** |
| **83 组**（create≠update） | 83 | 83 | **11（13%）** |

⇒ 两组显著不对称：**65 组 100% 能在源侧找到「已删」同名行，83 组只有 13%**。
若 `delete_flag` 是这两组自身产生的，不该有这种整齐的差异。

**证据 2｜源码语义（STATIC）**

```java
// portal-biz/.../PortalSetService.java
//   importPortalDesignInfo  L2556 / L2570
setDeleteFlag(Optional.ofNullable(...).orElse(false));
```

导入路径**保留原 `deleteFlag`，不强制重置为 false**。
调用链：`udc-portal/PortalImport.java` **L309**（应用复制）。

**与 D1-② 的关系**：这恰好解释了「UDC 建栏目 API 结构上产不出 1」与「确有 65 行 create 时即 1」
两个事实如何共存 —— **那 65 行根本没走建栏目 API，是导入复制时带进来的。**

**证据等级：DB-INFERENCE**（分布对称 + 源码语义，未抓到该次导入的实际执行记录）。
不写「已证实」，也不退回「未知」。

##### D1-④ DB 分布证据：`delete_flag` 与 `data_status` 是**正交两维**，不是同数据两份拷贝

先排除一个错误假设：本应用 149 行 vs `znxmglpt` 的 166/130 看似「成对」，曾疑为「每栏目两行（0/1 各一份）」。

实测**否定**该假设：

```sql
-- flag=1 且 ds=0 的行，是否存在同 portlet_id 的 flag=0/ds=0 兄弟？
SELECT COUNT(*) FROM portal_portlet_definition a
WHERE a.delete_flag=1 AND a.data_status=0
  AND EXISTS(SELECT 1 FROM portal_portlet_definition b
             WHERE b.portlet_id=a.portlet_id AND b.delete_flag=0 AND b.data_status=0);
-- → 0   （290 行里面 0 行有这种兄弟）
```

全表 `delete_flag × data_status`：

| | ds=0 | ds=1 | 合计 |
|---|---|---|---|
| **flag=0** | 178 | 139 | 317 |
| **flag=1** | 290 | 181 | 471 |

各行同 `portlet_id` 的多行实为 **`data_status`（设计态0 / 发布态1）两种状态**，不是删除标记的副本。
2 行组的组合分布：`0:0+0:1` → 95 组、`1:0+1:1` → 3 组、`0:0+0:0` → 2 组、`1:0+0:1` → 1 组。

⇒ **`delete_flag` 是独立于 `data_status` 的删除标记**，两者互不派生。

##### D1-⑤ 为什么本应用是 149/0（全 flag=1、无 ds=1）

| app | f1/ds0 | f1/ds1 | f0/ds0 | f0/ds1 |
|---|---|---|---|---|
| **datamigration9000000000000000001** | **149** | **0** | **0** | **0** |
| app9000000000000000001 | 65 | 65 | 83 | 83 |
| znxmglptcopy5791640252914287064 | 42 | 42 | 0 | 0 |
| datamigration9000000000000000001 | 0 | 42 | 0 | 0 |
| ctp-affair | 0 | 0 | 20 | 8 |

本应用是全库唯一「**全部行都被逻辑删除、且一条 ds=1（发布态）都没有**」的 app。
结合 `original_id ≠ id`（149/149，说明是复制/迁移来源而非原地创建），
最简解释：**该应用是一批栏目被导入后又整批逻辑删除后留下的残骸**
（与 83 行「导入后 +584–598 s 内被 **6 次**批量删除」吻合 —— 注意**不是一次**操作，见 D1-③）。
**此解释为最简推断，未取得该次批量操作的来源证据 ⇒ 标 STATIC-推断，不升为 LIVE。**

##### D1-⑥ 已排除项（逐条，不是笼统「未知」）

| 假设 | 判定 | 依据 |
|---|---|---|
| `delete_flag` 是「导入标记」 | **排除** | 实体/DDL/DTO 三处注解一致写「栏目删除标识:第三方栏目会逻辑删除」 |
| `delete_flag` 是「模板/版本覆盖标记」 | **排除** | 版本走独立 `version` 列（`setVersion(0)`），与 flag 无耦合 |
| 新建栏目默认 `delete_flag=1` | **排除** | `createPortlet` 全程不设 flag；实体默认 `false`；探针实测建后为 0 |
| 同 `portlet_id` 有 flag=0/1 双行副本 | **排除** | `flag=1,ds=0` 行中 0/290 存在 `flag=0,ds=0` 兄弟 |
| `delete_flag` 与 `data_status` 互相派生 | **排除** | 四象限分布独立（178/139/290/181） |
| `enabled` 列可解释 flag | **排除** | 全库 `flag=1` 471 行**全部** `enabled=1`（无一条 enabled=0），flag 与 enabled 不同步 |
| 148 行全部「生成即 1」 | **排除（推翻前序）** | 83 行 `create≠update`，导入后 +584–598 s 被 **6 次**批量置 1（65 行走拷贝继承，见 D1-③-b） |
| 「置 true 只有一处代码路径」 | **排除（两轮修正）** | 全文件 5 处 `setDeleteFlag`（3 true + 2 false）；本环境业务可达仅 ②（见 D1-②） |
| 「本应用 149 行是被 `deleteThirdPortlet` 逻辑删的」 | **排除** | 全库 788 行 `portlet_type` 全为 0，无 type=3 ⇒ 该路径无作用对象 |
| 「83 行是一次操作同一秒完成」 | **排除（二版错误，本版修正）** | 实测 **6 个不同秒**（17:25:46→17:26:00），对应 6 次 `deleteById(GROUP)` 调用 |

##### D1-⑦ 残余 UNVERIFIED（诚实边界，2026-10-18 04:08 按 VERDICT #C-05-FINAL 收窄）

**原 3 项中，2 项已闭合、1 项收窄。现仅剩 1 项真 UNVERIFIED。**

> **计数口径（防歧义，必读）**：这里的「1 项」指**原 3 项残余**的结余。
> 本轮另在 **D1-②-c** 新增登记一条 **`UNVERIFIED-RISK`（deleteThirdPortlet 缺类型防护）**，
> 它是**新识别的风险项，不属于原 3 项残余**，因此**不改变本处「1 项」的计数**。
> 两者性质不同：残余项问「事实未知」，风险项问「已知无防护、但可否被触发未知」。
> 两类分开计，不合并成「2 项 UNVERIFIED」，也不把风险项藏进「1 项」里。

**① 65 行 `create_time = update_time` 且 flag=1 —— 已闭合（DB-INFERENCE）**
成因 = 拷贝继承源应用已删行的 `delete_flag=1`（详见 **D1-③-b**）：
65 组后缀在源侧 `znxmglpt…` 100% 命中有 `flag=1` 的同名行，83 组仅 13%；
源码 `PortalSetService.importPortalDesignInfo` L2556/L2570 `setDeleteFlag(orElse(false))` 保留原值不重置。
⇒ **不再列为 UNVERIFIED**，等级 **DB-INFERENCE**（未抓到该次导入执行记录，故不升 LIVE）。

**② 83 行批量删除的调用方 —— 已闭合（LIVE-DB，main 只读取证）**
`udc_operation_log` 在同一时段有 **6 条** `sub_module=6 (PORTLET_GROUP)` / `action_type=2 (DELETE)`：
17:25:45 销售员门户(11 行) / 17:25:48 分总门户(7) / 17:25:51 事总门户(22) / 17:25:54 客开自定义栏目-勿删(1)
/ 17:25:57 本部总门户(21) / 17:26:00 平台门户(21)，操作人 `-2638952494757493308`。
**6 条日志的秒值 = 6 个 update_time 秒值 −1 秒**，行数逐条对齐（11/7/22/1/21/21 = 83）。
⇒ **不再列为 UNVERIFIED**。注：auditor 曾称「需 udc_operation_log、超只读范围」—— 实测**只读即可得**，
该说法不成立（main 已在本轮更正）。

**③ 「第三方栏目」判定字段 —— 已定位，但该路径在本环境无样本**
判定字段 = **`portlet_type = 3 (DYNAMIC_THIRD_COLUMN)`**
（全限定 `com.seeyon.portal.enums.PortletTypeEnum`，实体字段见 `PortalPortletDefinition.java` L104-107）。
**保留的唯一 UNVERIFIED**：本库 `portlet_type` **788 行全为 0**、无一条 3
⇒ 「第三方栏目逻辑删」这条业务在本环境**从未实际发生**，其真实运行行为**无法用本环境数据验证**，
只能靠源码（本切片已给）。**源码正确 ≠ 该路径跑通过，两者不混。**

##### D1-⑧ 约束（强化，取代原表述）

**`delete_flag` 禁止用于全表删除增量统计**，理由现已有机制依据而非仅经验：
它是「逻辑删除」标记，但本环境大量行在**导入后的 6 次**批量操作中被置 1（83 行分 6 组、每组组内同秒），
且存在整表全 1 的 app（本应用 149/149）⇒ **单列计数会把「整批导入后清理」误读成「逐条删除事件」**。

**允许的唯一用法**：同一行 `delete_flag` 的 **0→1 时序翻转**，
且必须与 `update_time` 跳变联合举证（如 §3.7.3 探针行 `22:47:38→23:18:39`）。

**证据等级**：D1-①②（写入/定义）**STATIC-源码级**（本机 `v8_3.12-hotfix_20250220` 源码，非反编译）；D1-③-b **DB-INFERENCE**（main 闭合，分布对称+源码语义，未抓执行记录）；D1-⑦② **LIVE-DB**（main 只读 `udc_operation_log` 取得）；
D1-④⑤⑥（分布/排除）**LIVE-DB**；D1-⑤ 因果解释 **STATIC-推断**；
D1-⑦ **仅剩 1 项 UNVERIFIED**（= 第三方栏目逻辑删路径在本环境无样本、真实运行行为无法用本环境数据验证；
另 2 项已分别由 DB-INFERENCE / LIVE-DB 闭合，见 D1-⑦）；
D1-②-c **UNVERIFIED-RISK**（缺类型防护，单独登记，不并入上项计数）。

### 3.7.4 删除前后行数差

> ⚠️ **口径警告（2026-10-18 新增，请先读这段再看表）**
> 下表把**删栏目**与**删分组**两次不同操作的结果写在同一张表里，容易被误读成「删栏目会动 category」。
> **实际归因（LIVE，见 §3.7.6）**：
> - **删栏目**（type=1）：`udc_portlet` −1、`udc_page_info` −1、`portal_portlet_category` **0（不变）**
> - **删分组**（type=0）：`udc_portlet` −1、`portal_portlet_category` −1（`category_code` = 分组 id）、`udc_page_info` **0（不变）**
>
> 下表 `category` 行的 **−1 属删分组**，**不得**写成「删栏目 category 1→0」。

| 表 | 删前 | 删后 | 差 | 归属操作（2026-10-18 补注） |
|---|---|---|---|---|
| `udc_portlet`（栏目） | 1 | 0 | **−1** | 删栏目 |
| `udc_portlet`（分组） | 1 | 0 | **−1** | 删分组 |
| `udc_page_info`（对应栏目页） | 1 | 0 | **−1** | 删栏目（分组无 page 行） |
| `portal_test2.portal_portlet_definition` | 1（flag=0） | 1（**flag=1**） | **0（行数不变，状态变）** | 删栏目（**且仅当该栏目曾「保存并提交」过**，见 §4.6） |
| `portal_test2.portal_portlet_category` | 1 | 0 | **−1** | **删分组**（与删栏目无关） |

行数差与上表语义判定逐行吻合：物理删的三处各 −1，软删的一处 0 行差但 flag 翻转。

### 3.7.5 本节的证据等级与边界

| 项 | 等级 |
|---|---|
| 删除端点/入参/响应体（§3.1–3.3） | **LIVE**（`raw/s2r1_delete_portlet.json` L7/L9/L11；`raw/s2r1_delete_group.json` L7/L9/L11） |
| 物理/软删语义判定（§3.7.1–3.7.3） | **LIVE**（DB 只读回读，本节 SQL 可原样复跑） |
| 级联范围与行数差（§3.7.2/3.7.4） | **LIVE** |
| **删栏目 vs 删分组的影响面分表归属（§3.7.6）** | **LIVE**（S1–S3 建→删全链，DB + 页面点击 + 操作日志三路） |
| `delete_flag` 真实语义域 | **UNVERIFIED**（PORTLET-D1，见 §3.7.3 疑点） |
| **页面可见性（删除后列表是否消失）** | **LIVE（栏目，PORTLET-S2-VIS S3）** —— 见 §3.7.7；**删分组页面侧仍 UNVERIFIED** |

> **口径铁律**：`content:1` + DB 行消失 ≠ 页面可用。
> 页面侧 PASS 必须另有 CDP 点击取证（删后列表实际消失、DOM 原文落盘），未取得前一律 UNVERIFIED。

### 3.7.6 删栏目 vs 删分组：分表归属（2026-10-18 LIVE 补证）

**来源**：PORTLET-S2-VIS 切片 S1–S3（建分组 → 建栏目 → 删栏目），应用 `datamigration9000000000000000001`，test2。
**证据等级**：DB 回读 + 页面点击 + 操作日志，三路俱在 ⇒ **LIVE**。

#### (a) 删栏目的真实影响面（3 表，category 不动）

```
S2 建栏目后（05:24:16）           S3 删栏目后（10:58:31）
udc_portlet            2     →    1      （只剩分组 3314443730917955770）
udc_page_info         32     →   31      （栏目页 id=6854945873513807584 物理删）
portal_portlet_category 3    →    3      ← 不变
portal_portlet_definition —   →    —      该栏目从未「保存并提交」，无行可翻转（见 §4.6）
```

删栏目后回读四路复核：

```sql
-- 被删栏目：物理删
SELECT COUNT(*) FROM udc_test2.udc_portlet WHERE id = 2167176325786336959;        -- → 0
-- 栏目页：物理删（id 与 caption 双查）
SELECT COUNT(*) FROM udc_test2.udc_page_info WHERE id = 6854945873513807584;      -- → 0
SELECT COUNT(*) FROM udc_test2.udc_page_info
 WHERE app_id = 8704025620829192834 AND caption LIKE '%S2VIS20261018%';           -- → 0
-- category：按被删栏目 id 查（应为 0，因为 category 存的是分组 id）
SELECT COUNT(*) FROM portal_test2.portal_portlet_category
 WHERE category_code = '2167176325786336959';                                     -- → 0
-- category：按分组 id 查（应仍在 1 行）
SELECT COUNT(*) FROM portal_test2.portal_portlet_category
 WHERE category_code = '3314443730917955770';                                     -- → 1（仍在）
```

**结构性解释**：`portal_portlet_category.category_code` 存的是**分组 id**（= `udc_portlet.id` where type=0），
与栏目 id 无关 ⇒ **删栏目天然不会减少 category 行**。这不是「没删干净」，是设计如此。

#### (b) 删分组的影响面（category −1，page_info 视引用而定）

`udc_page_info.group_id` **存的就是分组 id**（全表 1574 行实测：0=1422 / NULL=16 / **非空非 0=136，
这 136 行 100% JOIN 命中 `udc_portlet.type=0`，孤儿 0 行**）。
**本应用删前恰好无引用**：被删栏目行（id=6854945873513807584）的 `group_id` 正是分组 id
3314443730917955770，已在删栏目时一并物理删 ⇒ 删分组时该 group 引用为 0（因果：先删栏目，不是结构规律）：

```sql
-- 本案局部事实（S4 依据）：本应用删分组前，page_info 已无引用该 group 的行 → 0
SELECT COUNT(*) FROM udc_test2.udc_page_info
 WHERE app_id = 8704025620829192834 AND group_id = 3314443730917955770;   -- → 0
SELECT COUNT(*) FROM udc_test2.udc_page_info
 WHERE app_id = 8704025620829192834 AND relation_group_id = -6614000841111425014; -- → 0
-- 全表值域（勿推广成本应用快照）：0=1422 / NULL=16 / 非空非 0=136（全部 type=0 分组）
SELECT SUM(group_id=0), SUM(group_id IS NULL), SUM(group_id<>0 AND group_id IS NOT NULL)
  FROM udc_test2.udc_page_info;                                          -- → 1422 / 16 / 136
```

⇒ **本切片 S4：`udc_page_info` 31→31 不变**（依据=上面局部事实，非全表规律）。
⇒ **「删分组是否级联物理删 page_info」= UNVERIFIED**（跨应用存在 136 行挂在现存分组下，
如「门户报表」31 行；需一次跨应用真删分组取证，勿在其他应用直接套「不变」断言）。

历史对照（2026-10-17 同应用删分组，LIVE）：

```sql
-- 操作日志：删分组行 domain_id = 分组 id
SELECT create_time, action_type, sub_module, domain_caption, domain_id, trace_id
  FROM udc_test2.udc_operation_log
 WHERE app_id = 8704025620829192834 AND create_time = '2026-10-17 23:29:52' AND module = 4;
-- → action_type=2, sub_module=6, domain_caption='S2GROUP20261017', domain_id=-2821989384273517473

-- 删后：category 行与 udc_portlet 行均查无
SELECT COUNT(*) FROM portal_test2.portal_portlet_category WHERE category_code = '-2821989384273517473';  -- → 0
SELECT COUNT(*) FROM udc_test2.udc_portlet WHERE id = -2821989384273517473;                              -- → 0
```

#### (c) 一句话对照表

| 操作 | `udc_portlet` | `udc_page_info` | `portal_portlet_category` | `portal_portlet_definition` |
|---|---|---|---|---|
| 删**栏目**(type=1) | −1 | **−1** | **0** | 0 行差（**曾保存过**才 0→1 软删） |
| 删**分组**(type=0) | −1 | **0** | **−1** | 0（分组不产生定义行） |

### 3.7.7 页面可见性（PORTLET-S2-VIS S3 取证，2026-10-18 10:58）

**证据等级：LIVE**（CDP 真实鼠标事件 + 刷新后 DOM 回读）。这是 §3.7 原先唯一缺口「页面可见性 UNVERIFIED」的补证。

#### (a) 删除前的页面正证据

| 项 | 实测 |
|---|---|
| 路由 | `/main/child-frame/udc/app-design/page-manage/portlet?appId=8704025620829192834`（**非** `column-list`） |
| 会话态 | `cookieLen=375  hasToken=true`（排除缓存空壳） |
| 树节点 | `S2VISG20261018`（分组，缩进 0 层，259×30）+ `S2VIS20261018`（栏目，缩进 1 层，259×30） |

#### (b) 删除操作链（必须真实鼠标事件）

```
hover 到栏目节点 (176,174)   → .filled-more 出现 (287,164,20×20) display=block
                              （hover 前该节点可视图标数=0 ⇒ 图标是 hover 态渲染）
点 filled-more (297,174)     → 菜单三项：重命名(298,183) / 编辑(298,215) / 删除(298,247)
点「删除」(373,263)          → 确认弹窗 .ant-modal-confirm 416×164，原文：
                              "删除静态栏目页面 / 您确定要删除S2VIS20261018页面吗？ / 取消 确定"
                              「确定」class 含 ant-btn-dangerous
点「确定」(660,497)          → POST /service/udc/graphql?udcPortletDeleteIdPost
```

- **JS `dispatchEvent(mouseover)` 不触发** `filled-more`，必须 `Input.dispatchMouseEvent`（沿用 §3.5 Q7 结论，本次复现）
- 弹窗文案是**对象类型旁证**：删栏目 = 「删除静态栏目页面」，删分组 = 「删除文件夹」（§3.5）

#### (c) 删除后的页面反证据（刷新后重抓，排除 SPA 局部状态）

```
cookieLen=375  hasToken=true                                  ← 会话未掉
.ant-tree 的 textContent = "S2VISG20261018"                    ← 只剩分组
树节点：占位(w=24,h=0) + S2VISG20261018(indent=0,w=259,h=30)
        「S2VIS20261018」节点不存在
td 含 'S2VIS20261018' 命中 = 0
```

#### (d) ⚠️ 两个必须写进判据的坑（否则会误判）

**坑 1：空态不能当判据。**
删除**前后**「欢迎来到栏目空间 / 请创建栏目」都可见（`w=112 h=44 display=block`）。
它反映的是「列表是否还有其他栏目」，不是「本次删除是否成功」⇒ **空态出现与否都不是判据**。

**坑 2：不刷新时，「设计日志」tab 的历史行会被误判成「删失败」。**
删除后未刷新时，DOM 里仍存在一条 `td.ant-table-cell` 含 `S2VIS20261018`。归属取证结果：

```
owner = #RnDrjBMh-panel-operation-log
        （「设计日志」tab 的操作日志表格，行高 h=0 未渲染）
text  = "操作时间 操作人 模块 ... 2026-10-18 05:24:16 ... 栏目\栏目页面[S2VIS20261018][PC] ..."
```

⇒ 那是**历史操作记录**，不是栏目树节点。刷新后该命中归 0（tab 未激活）。
**凡在「设计日志」tab 存在时做 DOM 反证据，必须先做 td 向上归属到 `panel-operation-log` 的排除。**

> **坑 2 的取证方法已升级（2026-10-18 11:49–11:50，auditor 复核促成，记入方法层；commit 935dec5）**：
> 单靠「td 向上冒泡到某个容器」**证不了**归属 —— 栏目列表本身也是 `ant-table`，
> 只有 class 链（`TD → TR → TBODY → TABLE → … → DIV.ant-spin-container`）说明不了是哪个面板。
> **正解是读「目标面板容器自身的 textContent」**，而不是靠排除法：
> ```json
> panes: [{ "id": "r2DbdSZZ-panel-/app-design/page-manage/portlet",
>           "w": 972, "h": 841, "disp": "block",
>           "text": "栏目列表\nS2VISG20261018\n欢迎来到栏目空间\n请创建栏目" }]
>   → contains "S2VISG20261018" = true
>   → contains "S2VIS20261018"  = false     ← 面板级归 0，直接读，不靠排除
> ```
> 再加一重佐证：`tabs` 里「设计日志」`active=true` 但 **`w=0 h=0`** ⇒ 未渲染，
> 那条 `td` 属未渲染面板，**不构成用户可见证据**。
> **判据写法**：取「栏目列表面板容器 id + 该面板 textContent 是否含被删名称」，
> 这比「全页 body 匹配 + 人工排除日志 tab」**更难被下一个取证者读错**。
>
> **证据文件**：`<HERMES_HOME>\cache\scratch\s3_h_container_isolation.json`（派生件，11:50:15 机械复算），
> 源数据 `s3_h_reload.json`（**真实观测 10:59:28–10:59:37，唯一一次「刷新后 DOM」**）。
> ⚠️ **证据等级不变**：这是**同一次观测的重投影** —— 观测次数未增、观测方未变（同一浏览器同一 token）。
> 判据质量提升了，**证据等级仍是单方 LIVE**。"双方 LIVE" 需 auditor 在 SSO 恢复后亲自开一次页面。

#### (e) 判据（本节定稿口径）

| 判据 | 可接受值 | 不可接受的伪判据 |
|---|---|---|
| **栏目列表面板容器内 textContent 不含被删名称** | ✅ **首选**（`panes[id=*-panel-/app-design/page-manage/portlet].text`） | — |
| 栏目树 namedNode 中不再含被删名称 | ✅ 页面判据 | — |
| DB `udc_portlet` / `udc_page_info` 双表回读 | ✅（§3.7.6a） | — |
| 操作日志 `action_type=2` + traceId | ✅（§3.8） | — |
| 空态文案变化 | ❌ **不作判据** | 前后都可见，恒真 |
| 未做归属取证的 `td` 含名 | ❌ 不作判据 | 可能是日志 tab 历史行 |
| 只有 class 链、无容器 id 的 td 归属 | ❌ 不作判据 | 栏目列表也是 ant-table，区分不了 |

### 3.8 第一取证点：`udc_operation_log`（2026-10-18 新增，推荐优先使用）

**为什么单独立一节**：本切片（S1 建分组 / S2 建栏目 / S3 删栏目）三轮实测下来，
`udc_test2.udc_operation_log` 是**信息密度最高、成本最低**的取证点 ——
一条 SQL 同时给出「谁、何时、对什么对象、做了什么、traceId、业务路径」，
而抓响应体需要开 CDP + 监听 Network + 同连接取 body（易失效，S2 那次就没取到）。

#### (a) 字段语义（本切片实测确认）

| 列 | 语义 | 实测值域 |
|---|---|---|
| `action_type` | 动作类型 | **1=CREATE，2=DELETE，3=UPDATE，7=RECOVER（回收站恢复，全表枚举 10 行）**（全表枚举反证：1=4810/2=1274/3=30766/7=10，零例外，非文档抄写） |
| `module` | 业务域 | `4` = 栏目（`log_details.module="PORTLET"`） |
| `sub_module` | 对象类型 | **`6` = 栏目分组**，**`40` = 栏目页面**，`4` = 栏目主体（保存/属性更新） |
| `domain_caption` | 对象名称 | 如 `S2VIS20261018` |
| `domain_id` | 对象 id | 删栏目 = `udc_page_info.id`；删分组 = 分组 id |
| `trace_id` | **服务端 traceId** | 如 `17922923107887978900`（20 位数字串） |
| `operation_time` | 毫秒时间戳 | 与 `create_time` 秒级对齐 |
| `log_path` | 业务路径 | 如 `terminal=PC&relationGroupId=-6614000841111425014&pageId=6854945873513807584` |
| `log_details` | JSON 全文 | 含 `actionType`（字符串 `DELETE`/`CREATE`/`UPDATE`）、`element`、`beforeSnapshot`/`afterSnapshot`、`ip` |

#### (b) 本切片三条实测样本（可直接用作判据模板）

```sql
SELECT id, create_time, action_type, module, sub_module, domain_caption, domain_id,
       operator_id, trace_id, operation_time, elements_size, log_path
  FROM udc_test2.udc_operation_log
 WHERE app_id = 8704025620829192834
   AND log_element LIKE '%S2VIS%'
 ORDER BY create_time;
```

```
05:22:27  action_type=1  sub_module=6   S2VISG20261018  trace=17922721467020787990   ← S1 建分组
05:24:16  action_type=1  sub_module=40  S2VIS20261018   trace=17922722557227434454   ← S2 建栏目
10:58:31  action_type=2  sub_module=40  S2VIS20261018   trace=17922923107887978900   ← S3 删栏目
          domain_id=6854945873513807584  operator_id=-2638952494757493308
          log_path=terminal=PC&relationGroupId=-6614000841111425014&pageId=6854945873513807584
```

`log_details` 里服务端自己写的语义（**不是我的推断**）：

```json
{"actionType":"DELETE","module":"PORTLET","subModule":"PORTLET_PAGE",
 "element":"栏目\\栏目页面[S2VIS20261018][PC]",
 "elementId":"6854945873513807584","ip":"10.0.0.1"}
```

#### (c) 使用纪律（避免把这张表用坏）

1. **`action_type` 的数字含义必须由本环境对照得出**，不要抄外部文档 —— 本切片用
   「同 `module` + 同 `sub_module` + 已知操作」三条件对照，得出 1/2/3。
2. **`domain_id` 的语义随 `sub_module` 变**：删栏目取 `udc_page_info.id`，删分组取分组 id。
   直接拿它去 `udc_portlet.id` 查会查不到 —— **不是删除失败**。
3. **操作日志只能证明「平台执行了该动作」，不能证明「页面已正确反映」**。
   页面可见性仍须 §3.7.7 的 DOM 取证 ⇒ **两者不可互替**。
4. **它不替代响应体**：请求级契约（入参 schema、响应 schema）仍须 `raw/*.json` 的 LIVE 抓包。
   操作日志是**结果级**证据，不是**协议级**证据。

#### (d) 一句话

> 想省 /service 配额拿 traceId 与动作语义 → 查 `udc_operation_log`。
> 想拿请求/响应协议形态 → 仍须抓包。
> **两者证据等级都是 LIVE，但证明的东西不同。**

---

# 4. 保存并提交 — `udcPageInfoUpdatePost`

> **本 op 是「栏目 → 门户定义」的唯一同步出口**（暂存不触发）。

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPageInfoUpdatePost` | LIVE `raw/s2r1_page_save_submit.json` L66 段 |
| method | POST | LIVE 同上（`raw/s2r1_page_save_submit.json` call.method） |
| GraphQL 类型 | `mutation submitPage($body: udcPageInfoUpdatePostInputBody)` | LIVE（query 文本别名 `submitPage`） |
| 后端落点 | `PageInfoService#update` → `syncPortalToPortal` → `syncPortal` → Dubbo `createOrUpdatePortlet` | STATIC `S2-WRITE-CHAIN-STATIC-20261017.md` §4 + 裁定 H6 |
| 副作用 | ①`udc_page_info` 更新（isDraftPage true→false）②门户 `portal_portlet_definition` upsert ③op-log 1 条（action_type=3, sub_module=4） | LIVE DB + op-log |

## 4.1 请求 schema（`variables.body`，20 字段，全部 LIVE）

| 字段 | 类型 | LIVE 样例 | 说明 | 来源 |
|---|---|---|---|---|
| `appId` | string | `"8704025620829192834"` | 应用 id | LIVE |
| `id` | string | `"-1695224980799982257"` | **页面 id（udc_page_info.id）**，非 portlet id | LIVE |
| `urlType` | enum string | `"PC"` | 端类型 | LIVE |
| `inParams` | string(JSON 串) | `"[]"` | 入参定义 | LIVE |
| `inPortletParams` | string(JSON 串) | `"[]"` | 栏目入参 | LIVE |
| `pageSchema` | string(JSON 串) | 857 字符（空白页最小 schema） | 页面结构；空白页 `children:[]` | LIVE |
| `publicAccess` | boolean | `false` | 公开访问 | LIVE |
| `pageUrl` | string | `"S2PROBE20261017"` | 栏目标识 | LIVE |
| `pageType` | enum string | `"PORTLET"` | 页面类型 | LIVE |
| `defaultOpenType` | null | `null` | 默认打开方式 | LIVE |
| `description` | string | `""` | 描述 | LIVE |
| `groupId` | string | `"-2821989384273517473"` | 分组 id | LIVE |
| `guid` | string | `"-8194165606485703903"` | **page_info.guid**（非 portlet guid） | LIVE |
| `relationGroupId` | string | `"8758458332069176381"` | = portlet 的 `page_relation_id` | LIVE |
| `sortNo` | number | `331` | 页面排序号 | LIVE |
| `layoutId` | string | `"0"`（串形态） | 布局 id；PORTLET 页恒 0 | LIVE |
| `layoutInfo` | string | `""` | 布局信息 | LIVE |
| `referConfigParameters` | array | `[]` | 引用配置参数 | LIVE |
| `defaultPlan` | string(JSON 串) | `"[]"` | 默认方案 | LIVE |
| `operationLog` | object | 见 §4.2 | 操作日志（服务端据此写 op-log） | LIVE |

## 4.2 `operationLog` 子结构

> **本节全部字段 = `LIVE`**（来源：`raw/s2r1_page_save_submit.json` 中 `udcPageInfoUpdatePost` 请求体的 `variables.body.operationLog`，逐字段实读）。


| 字段 | 类型 | LIVE 值 | 说明 |
|---|---|---|---|
| `operationLog.appId` | string | `"8704025620829192834"` | 应用 id |
| `operationLog.domainId` | string | `"-1695224980799982257"` | 页面 id（= body.id） |
| `operationLog.domainCaption` | string | `"S2PROBE20261017"` | 页面 caption |
| `operationLog.path` | string | `"terminal=PC&relationGroupId=8758458332069176381&pageId=-1695224980799982257"` | **与 op-log.log_path 同形**，可交叉核对 |
| `operationLog.elementRecords` | array | 1 项起 | 变更明细 |
| `operationLog.elementRecords[].actionType` | string | `"UPDATE"` | 动作类型 |
| `operationLog.elementRecords[].element` | string | `"栏目\\栏目"` | 元素路径，**对应 op-log.log_element 单元素** |
| `operationLog.elementRecords[].elementId` | string | `"-1695224980799982257"` | 页面 id |
| `operationLog.elementRecords[].path` | string | `"terminal=PC&...&componentId=PAGE"` | 元素路径（比 operationLog.path 多 componentId） |
| `operationLog.elementRecords[].attributeRecords` | array | 5 项（创建时间/属性配置/栏目事件/外框布局-页面布局/名称） | 逐属性 before/after |
| `operationLog.elementRecords[].attributeRecords[].name` | string | `"创建时间"` 等 | 属性中文名 |
| `operationLog.elementRecords[].attributeRecords[].before` | object | `{"type":"STRING","extendInfo":null}` | 变更前 |
| `operationLog.elementRecords[].attributeRecords[].after` | object | `{"type":"STRING","value":"...","extendInfo":null}` | 变更后 |
| `operationLog.actionType` | string | `"UPDATE"` | 顶层动作类型 |

## 4.3 响应 schema

```json
{"traceId":"17922484587530491237","data":{"udcPageInfoUpdatePost":{"data":{"content":1},"message":"SUCCESS","status":0}}}
```
| 字段 | 类型 | LIVE 值 | 注意 | 来源 |
|---|---|---|---|---|
| `data.udcPageInfoUpdatePost.data.content` | number | `1` | 无 `code` 字段（与其他 op 不同） | LIVE |

raw 指针：`raw/s2r1_page_save_submit.json` L66 段

## 4.4 门户同步判读（LIVE 实测，配合 `enums.md`）

| 现象 | LIVE 证据 |
|---|---|
| 保存并提交**同秒**生成 `portal_test2.portal_portlet_definition` 行（22:47:38） | DB：id=329969732608628974，expose_name=S2PROBE20261017，category_code=-2821989384273517473 |
| 定义行 `portlet_id` = **pageRelationId**（8758458332069176381），非 udc_portlet.id | DB + ROUTE Q2 |
| 单端保存（仅 PC）→ 该端三项齐全（enable_pc=1 + expose_name + definition_info），手机端不写（enable_mobile=0、m_definition_info=NULL） | DB + 裁定 M/H6-b |
| 删除时定义行软删（delete_flag 0→1） | DB |

**未能取证（明确不写结论）**：Dubbo `createOrUpdatePortlet` 的 RPC 契约、`tryLock` 竞争失败路径、`syncPortal` 内部异常明细 → 留 C3，仅静态。

## 4.5 失败形态

| 形态 | 表现 | 来源 |
|---|---|---|
| 前置：页面被他人锁定 | `udcMultiEditLockPost` 先取锁（同一流程中先调用） | LIVE `raw/s2r1_page_save_submit.json` L16 段 |
| Dubbo 失败（静态推演） | 服务端抛 `BusinessException「栏目数据发送失败！」`，接口返回失败 | STATIC 字节码（裁定 K/L/M）；**本 op 本轮未观测到失败实例** |
| 锁竞争（>=2 端） | 仅 `log.info`「栏目锁竞争失败」，接口仍成功 | STATIC；**未观测** |
| 门户查不到定义 | 不得判「同步失败」或「删除残留」，记 UNVERIFIED 并查服务端日志 | 裁定 H6-b |

## 4.6 「同步只发生在保存」的 LIVE 侧证（2026-10-18 补，填 §4.4 原有空白）

§4.4 已用 DB 证明「保存并提交同秒生成 definition 行」，但那是**单点正向证据**。
它没回答一个反向问题：**「建栏目」这个 op 到底会不会顺手写 definition？**
2026-10-18 的 S2/S3 序列正好给出了**同一应用内的对照实验**，这条从 STATIC 契约推论升级为 **LIVE 侧证**。

### (a) 对照实验：同应用、同一天、两种操作

| 操作 | 时刻 | definition 是否生成 |
|---|---|---|
| 2026-10-17 **建栏目** `S2PROBE20261017`（`udcPortletCreatePortletPost`） | 22:45:55 | ❌ 当天 22:45:55 时点无行 |
| 2026-10-17 **保存并提交**（`udcPageInfoUpdatePost`） | 22:47:38 | ✅ **同秒生成** id=329969732608628974 |
| 2026-10-18 **建栏目** `S2VIS20261018`（`udcPortletCreatePortletPost`） | 05:24:16 | ❌ 未生成 |
| 2026-10-18 **删除该栏目**（`udcPortletDeleteIdPost`） | 10:58:31 | ❌ 无行可翻转（Never existed） |

### (b) 操作日志把两次操作分得很清楚

```sql
SELECT create_time, action_type, sub_module, domain_caption, trace_id, log_path
  FROM udc_test2.udc_operation_log
 WHERE app_id = 8704025620829192834
   AND create_time BETWEEN '2026-10-17 22:40:00' AND '2026-10-17 23:35:00'
   AND module = 4
 ORDER BY create_time;
```

```
22:45:02  action_type=1  sub_module=6   S2GROUP20261017   trace=17922483013725158661
22:45:55  action_type=1  sub_module=40  S2PROBE20261017   trace=17922483545794594178   ← 建栏目
22:47:38  action_type=3  sub_module=4   S2PROBE20261017   trace=17922484587530491237   ← 保存
23:18:39  action_type=2  sub_module=40  S2PROBE20261017   trace=17922503199724992371   ← 删栏目
23:29:52  action_type=2  sub_module=6   S2GROUP20261017   trace=17922509930521996766   ← 删分组
```

`22:47:38` 那条（`action_type=3` = UPDATE）的 `log_details`：

```json
{"actionType":"UPDATE","module":"PORTLET","subModule":"WIDGET",
 "element":"栏目\\栏目","path":"terminal=PC&relationGroupId=8758458332069176381&pageId=-1695224980799982257"}
attributeRecords 的 name 序列：['创建时间','属性配置','栏目事件','外框布局-页面布局','名称']
```

而 definition 行 `id=329969732608628974` 的 `create_time = 2026-10-17 22:47:38` —— **与那次 UPDATE 同秒**。

### (c) 结论与证据等级

| 结论 | 等级 | 依据 |
|---|---|---|
| **建栏目 op 不写 `portal_portlet_definition`** | **LIVE（侧证）** | 两次建栏目（10-17 / 10-18）均零生成；保存后才出现 |
| **仅「保存并提交」写 definition** | **STATIC（主证）+ LIVE（侧证）** | 主证：`PageInfoService#update → syncPortal`（§4 表头）；侧证：本 §4.6(b) |
| definition 的 `0→1` 软删翻转**只在「曾保存过」时可能发生** | **LIVE** | 10-17 栏目保存过 ⇒ 删时有行可翻转；10-18 栏目未保存 ⇒ 删时 0 行，翻转**不可能发生** |

> **口径警告**：因此「删栏目后 definition 应留 1 行 flag=1」**不是一个无条件断言**。
> 若该栏目从未保存过，正确结果是「definition 该 portlet_id 查 0 行」——
> **这既不是 FAIL 也不是 PASS，应记 N/A**。把「正确的零」判成缺陷，是本切片最容易踩的坏判据。

### (d) 可复跑核对 SQL

```sql
-- 本次 S2VIS 栏目是否真的没有 definition 行
SELECT COUNT(*) FROM portal_test2.portal_portlet_definition
 WHERE portlet_id = '-6614000841111425014';                    -- → 0
SELECT COUNT(*) FROM portal_test2.portal_portlet_definition
 WHERE name LIKE '%S2VIS%' OR expose_name LIKE '%S2VIS%';      -- → 0
-- 本应用今日零增零改
SELECT COUNT(*) FROM portal_test2.portal_portlet_definition
 WHERE app_id = 'datamigration9000000000000000001'
   AND create_time >= '2026-10-18 00:00:00';                    -- → 0
SELECT COUNT(*) FROM portal_test2.portal_portlet_definition
 WHERE app_id = 'datamigration9000000000000000001'
   AND update_time >= '2026-10-18 00:00:00';                    -- → 0
-- 10-17 那次确实生成并被软删
SELECT id, portlet_id, delete_flag, create_time, update_time
  FROM portal_test2.portal_portlet_definition WHERE id = 329969732608628974;
-- → delete_flag=1, create_time=22:47:38, update_time=23:18:39（与建/删时刻精确对齐）
```

> **键口径（重要，勿混）**：本表 `app_id` 与 `app_code` **都是 varchar，值存 code 字符串**。
> `WHERE app_id = 8704025620829192834`（数字形式）→ **0 行**，会被误读成「没有数据」。
> 正确写法：`WHERE app_id = 'datamigration9000000000000000001'`（→ 149）。
> 两列结果不同（`app_id` 列 149 / `app_code` 列 160，差 11 行 = `app_id` 为 `-1`(7) + `cdp-data`(2) + `ctp-affair`(2)）。
> **断言必须锁定同一列，并在文档里写明是哪一列。**

---

# 5. 暂存草稿 — `udcPageInfoUpdateDrafPost`

> **不触发门户同步**（与 §4 的关键区别）。

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPageInfoUpdateDrafPost` | LIVE `raw/s2r1_page_save.json` L16 段、`raw/s2r1_page_save_submit.json` L26 段 |
| method | POST | LIVE 同上（两件 raw 的 call.method 均为 POST） |
| GraphQL 类型 | `mutation savePageDraf($body: udcPageInfoUpdateDrafPostInputBody)` | LIVE（别名 `savePageDraf`） |
| 落表 | 仅 `udc_page_info`（`isDraftPage` 保持 true），**不写门户** | LIVE DB（门户定义未变） |

## 5.1 请求 schema（`variables.body`，20 字段）

> **本节全部字段 = `LIVE`**（来源：`raw/s2r1_page_save_submit.json` 的 `udcPageInfoUpdateDrafPost` 请求体；与 §4.1 的 17 个公共字段已逐值比对一致）。


与 §4.1 的差异（**LIVE 逐字段集合比对：两者各 20 字段，公共 17 字段，各独有 3 字段**）：

| 字段 | UpdatePost | UpdateDrafPost | 说明 |
|---|---|---|---|
| `pageSchema` | ✅ 有（857 字符） | ❌ 无 | 草稿不写正式 schema |
| `draftPageSchema` | ❌ 无 | ✅ 有（同结构，写入草稿位） | — |
| `operationLog` | ✅ 有 | ❌ 无 | 草稿不产生 op-log（op-log 表无对应草稿行） |
| `referConfigParameters` | ✅ 有（`[]`） | ❌ 无 | 引用配置参数，草稿不带 |
| `eventDefine` | ❌ 无 | ✅ 有（`"[]"`） | — |
| `pageVariable` | ❌ 无 | ✅ 有（`"[]"`） | — |

**公共 17 字段**（**值逐字段完全相同**，LIVE 已比对）：
`appId` / `id` / `urlType` / `inParams` / `inPortletParams` / `publicAccess` / `pageUrl` / `pageType` / `defaultOpenType` / `description` / `groupId` / `guid` / `relationGroupId` / `sortNo` / `layoutId` / `layoutInfo` / `defaultPlan`

## 5.2 请求原文样例（LIVE）

> **本节全部内容 = `LIVE`**（来源：`raw/s2r1_page_save.json` 中 `url=/service/udc/graphql?udcPageInfoUpdateDrafPost`、`method=POST`、`status=200` 的那一次调用，`body` 字段原文逐字复制，未做任何裁剪或改写）。

```
{"query":"\n          mutation savePageDraf($body: udcPageInfoUpdateDrafPostInputBody) {\n            udcPageInfoUpdateDrafPost(body: $body) {\n              data {\n                content\n              }\n              message\n              status\n            }\n          }\n        ","variables":{"body":{"appId":"8704025620829192834","id":"-1695224980799982257","urlType":"PC","inParams":"[]","inPortletParams":"[]","draftPageSchema":"{\"children\":[],\"id\":\"-1695224980799982257\",\"appId\":\"8704025620829192834\",\"pageType\":\"PORTLET\",\"pageUrl\":\"S2PROBE20261017\",\"urlType\":\"PC\",\"defaultOpenType\":null,\"description\":\"\",\"groupId\":\"-2821989384273517473\",\"guid\":\"-8194165606485703903\",\"relationGroupId\":\"8758458332069176381\",\"sortNo\":331,\"masterEntityIds\":null,\"createTime\":\"1792248354000\",\"version\":null,\"handWritten\":false,\"inPortletParams\":[],\"settings\":{\"styles\":{},\"alignment\":\"center\",\"backgroundAdapt\":\"cover\",\"backgroundColor\":\"#ffffff\",\"gap\":\"20px 0\",\"boxModel\":{\"margin\":\"0 auto 0 auto\",\"padding\":\"0 0 0 0\"}},\"portletEvents\":[{\"eventTitle\":\"更多\",\"isMoreEvent\":true,\"eventType\":\"onClick\",\"actionName\":\"\",\"actionType\":\"\"}],\"pageLayout\":false,\"originId\":\"-1695224980799982257\",\"name\":\"页面\",\"type\":\"PAGE\",\"childById\":{},\"pageVariable\":[],\"terminal\":\"PC\",\"expressSchemaPathMaps\":{}}","publicAccess":false,"pageUrl":"S2PROBE20261017","pageType":"PORTLET","pageVariable":"[]","defaultOpenType":null,"description":"","groupId":"-2821989384273517473","guid":"-8194165606485703903","relationGroupId":"8758458332069176381","sortNo":331,"layoutId":"0","layoutInfo":"","defaultPlan":"[]"}}}
```

> 该 body 共 1711 字符。注意 `draftPageSchema` 是**字符串化的 JSON**（双重转义），不是嵌套对象 —— 这是本 op 与前 4 个 op 最易踩的形态差异。

## 5.3 响应 schema

```json
{"traceId":"17922484586071937191","data":{"udcPageInfoUpdateDrafPost":{"data":{"content":1},"message":"SUCCESS","status":0}}}
```
同样**无 `code` 字段**。

## 5.4 与 UpdatePost 的行为对照

> **本节全部行 = `LIVE`**（接口对比来自 raw 两件；DB 对比来自建删链回读）。


| 维度 | UpdateDrafPost | UpdatePost |
|---|---|---|
| `udc_page_info.isDraftPage` | 保持 `true` | true→`false` |
| `portal_portlet_definition` | **不变**（不触发同步） | 同秒 upsert |
| op-log | **不产生** | 产生 1 条（action_type=3/sub_module=4） |
| 页面 schema 位 | `draftPageSchema` | `pageSchema` |

raw 指针：`raw/s2r1_page_save.json` L16 段；`raw/s2r1_page_save_submit.json` L26 段

---

# 6. 读栏目树 — `udcPortletSelectByAppIdAppGet`

| 项 | 值 | 来源 |
|---|---|---|
| URL | `POST /service/udc/graphql?udcPortletSelectByAppIdAppGet` | LIVE 全部 5 件 raw 均有该调用（如 `raw/s2r1_group_create.json` L17） |
| method | POST | LIVE 同上（全部 5 件 raw 的 call.method 均为 POST） |
| GraphQL 类型 | `query udcPortletSelectByAppIdAppGet($path: udcPortletSelectByAppIdAppGetInputPath)` | LIVE |
| 用途 | 栏目列表页首屏唯一读接口；返回**两层树** | LIVE + S1 结论 |

## 6.1 请求 schema

| 字段 | 类型 | 必填 | LIVE 值 | 说明 | 来源 |
|---|---|---|---|---|---|
| `variables.path.appId` | string | 是 | `"8704025620829192834"` | 应用 id；**唯一观测到的参数** | LIVE |

> 未观测到分页/排序/过滤参数 → 本契约不写（留 C2 补）。

## 6.2 响应 schema（`data.udcPortletSelectByAppIdAppGet.data.content` 数组，每项一个顶层节点）

| 字段 | 类型 | 顶层(GROUP) LIVE 值 | 子层(PORTLET) LIVE 值 | 说明 | 来源 |
|---|---|---|---|---|---|
| `appId` | string | `"8704025620829192834"` | 同 | 应用 id | LIVE |
| `groupId` | string \| null | `null` | `"-2821989384273517473"` | 分组节点无父；栏目节点指向分组 | LIVE |
| `guid` | string | `"-4399224624179689670"` | `"-7672842714696691825"` | **此处有值**（与创建响应 null 不同） | LIVE |
| `id` | string | `"-2821989384273517473"` | `"5810462779490574369"` | udc_portlet.id | LIVE |
| `name` | string | `"S2GROUP20261017"` | `"S2PROBE20261017"` | 名称 | LIVE |
| `orderNo` | number | `1` | `2` | **此处为真实落库值**（建前 max=0 → +1/+2） | LIVE（Q6） |
| `category` | enum string | `"ADVANCED"` | `"ADVANCED"` | 仅本 op 返回 category | LIVE |
| `portletList` | array \| null | 子栏目数组 | `null` | 顶层挂子节点，子节点不再嵌套 | LIVE |
| `pageRelationId` | string \| null | `null` | `"8758458332069176381"` | GROUP 恒 null，PORTLET 有值 | LIVE + S1 结论 |
| `publishState` | enum string | `"UNPUBLISH"` | `"UNPUBLISH"` | 见 `enums.md` §publishState | LIVE |
| `terminalType` | enum string | `"PC"` | `"PC"` | 端类型 | LIVE |
| `type` | enum string | `"GROUP"` | `"PORTLET"` | 节点类型判别键 | LIVE |
| `originalId` | string | `"0"` | `"0"` | 多版本原始 id | LIVE |
| `g_l_index` | string | `"1"` | `"1"` | **语义 UNVERIFIED**（无任何在盘来源解释该字段含义）。仅可陈述观测事实：同一次响应内按列表顺序自增（`raw/s2r1_portlet_create.json` data1 的依赖列表为 "1"…"33"；本树节点为 "1"）。**不得据此写分页/排序规则** | 值 LIVE；**语义 UNVERIFIED** |

## 6.3 LIVE 样例（完整两层树）

请求：
```json
{"path":{"appId":"8704025620829192834"}}
```
响应 content（`raw/s2r1_portlet_create.json` L32 段）：
```json
[{"appId":"8704025620829192834","groupId":null,"guid":"-4399224624179689670","id":"-2821989384273517473","name":"S2GROUP20261017","orderNo":1,"category":"ADVANCED","portletList":[{"appId":"8704025620829192834","groupId":"-2821989384273517473","guid":"-7672842714696691825","id":"5810462779490574369","name":"S2PROBE20261017","orderNo":2,"pageRelationId":"8758458332069176381","publishState":"UNPUBLISH","terminalType":"PC","type":"PORTLET","category":"ADVANCED","originalId":"0","g_l_index":"1"}],"pageRelationId":null,"publishState":"UNPUBLISH","terminalType":"PC","type":"GROUP","originalId":"0","g_l_index":"1"}]
```

空态样例（`raw/s2r1_delete_group.json` L17 段）：`"content":[]` —— **接口空态，不等于页面空态**（页面空态需 DOM innerText 作证）。

## 6.4 判读要点（LIVE）

- 删除后用同一 op 复读可作为「DB 已清」的交叉验证，但**不能**充当「页面可见」证据（阶段 1 VERDICT T 裁定）。
- `terminalType` 在该 op 中可能为 `ALL`（S1 在应用 3289082814923688017 观测到 `"ALL"`），非恒定 `PC`。
- `category` 仅本 op 返回，创建响应不返回 category。

---

## 附录 A：raw 文件与 op 对应

| raw 文件 | 含 op | 时刻 |
|---|---|---|
| `raw/s2r1_group_create.json` | CreatePost + SelectByAppIdAppGet | 22:45:06 |
| `raw/s2r1_portlet_create.json` | CreatePortletPost + SelectByAppIdAppGet + 9 个设计器初始化 op | 22:46:01 |
| `raw/s2r1_portlet_form.json` | （无请求）表单快照 | 22:45:37 |
| `raw/s2r1_page_save.json` | UpdateDrafPost + MultiEditLockPost 等 4 个 | 22:47:25 |
| `raw/s2r1_page_save_submit.json` | UpdatePost + UpdateDrafPost + 8 个 | 22:47:46 |
| `raw/s2r1_delete_portlet.json` | DeleteIdPost + SelectByAppIdAppGet | 23:18:45 |
| `raw/s2r1_delete_group.json` | DeleteIdPost + SelectByAppIdAppGet | 23:30:00 |

## 附录 B：本契约的边界（不写什么）

1. 不写未观测到的请求字段（如 `PortletDto` 的 `category`/`orderNo` 在此入口未传）。
2. 不写 Dubbo RPC 契约（C3）。
3. 不写错误码全集，只写已观测形态。
4. 不把「HTTP 200」当成功判据，不把「接口 content:[]」当页面可见。
5. 不写任何未在 `raw/` 或 DB 中出现过的字段值。
