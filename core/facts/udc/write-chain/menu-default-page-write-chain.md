# 菜单写链（PAGE 子节点 / default_page / 树回读）—— 全链打通

> 领域：菜单/导航 → `udc/function` 下的 **PAGE 子节点创建** + **默认页设定** + **树回读**
> 状态：**LIVE PASS**（test2，app `8704025620829192834`）
> 证据：LIVE REST 双向回读（GET + GET 树）+ pod 真实堆栈 + DB 回读 + CFR 字节码
> 承接：`docs/audit/udc-semantics/MENU-FUNCTIONNODE-CONSTRAINTS.md`（字段面）补充**写链行为面**

## 0. 结果

| 指标 | 起点 | 终点 |
|---|---|---|
| 检测 ERROR | 0 | 0 |
| 检测 WARN | 9（04003×7 / 04009×1 / **08100×1**） | **8**（04003×7 / 04009×1） |
| 空目录菜单 | `-1628253460115858501` `default_page=0` 无子节点 | `default_page=4630606675502338872` 有 PAGE 子节点 |

`08100` 条目在检测面**消失**，证明该 WARN 的可消除路径 = 给菜单一个可指向的子页面。

## 1. ★ 端点选择：建 PAGE 子节点必须用 `create/function-refer`

`POST /udc/function` 的入参是 **`FunctionDto`**，CFR 逐字段确认它**没有 `resourceId`**：

```
FunctionDto      = {name, icon, permission, parentId, appId, terminalType,
                    defaultPage, url, relationId, tag, type, orderNo}
FunctionReferDto = {name, parentId, appId, terminalType, url, relationId,
                    resourceId, relationApp, openState, pageParam, type, pageType}
```

`FunctionNodeService.createFunctionNode`（:189）对 `type` 不在
`type2SchemaState(MENU/PORTAL_SPACE/EXT_LINK/REPORT)` 内的节点调用
`selectOnePageByPageId(appId, dto.getResourceId())`；`FunctionDto` 无该字段 ⇒ 条件值 `null` ⇒
`SearchFilter` 直接拒绝：

```
ERROR SearchFilter:83 | [resourceId]字段的条件数据不能为null
org.mybatis.spring.MyBatisSystemException ... BusinessException
  at FunctionNodeService.selectOnePageByPageId(FunctionNodeService.java:606)
  at FunctionNodeService.setSchemaState(FunctionNodeService.java:218)
  at FunctionNodeService.createFunctionNode(FunctionNodeService.java:189)
→ {"code":"BOOT_4000","message":"DB Error"}
```

**LIVE 实测 3/3 复现（`POST /udc/function` 建 PAGE 必 DB Error），且 `COUNT(*)=0` —— 零落库。**
改用 `POST /udc/function/create/function-refer`（`FunctionReferDto` 带 `@NotBlank resourceId`）即成功。

**校验链实测顺序**（逐步探针，避免误建垃圾）：

| 试探体 | 响应 |
|---|---|
| `{appId,terminalType,type:PAGE,name,parentId}` | `BOOT_4000 DB Error` |
| `+ url` | `BOOT_4000 DB Error` |
| `+ resourceId` | **`BOOT_0000`** `content = 4630606675502338872` |

## 2. 建 PAGE 子节点（LIVE PASS）

```
POST /service/udc/function/create/function-refer
{"appId":"8704025620829192834","terminalType":"PC","type":"PAGE","name":"小爪验收页面",
 "parentId":"-1628253460115858501","url":"xzhpage951440",
 "resourceId":"1520098474917276520","pageType":"SEARCH_LIST","openState":"EDIT"}
→ {"code":"BOOT_0000","data":{"content":"4630606675502338872"}}
```

回读 `GET /udc/function/4630606675502338872`：

```json
{"id":"4630606675502338872","name":"小爪验收页面","type":"PAGE",
 "parentId":"-1628253460115858501","url":"xzhpage951440",
 "resourceId":"1520098474917276520","openState":"EDIT",
 "schemaState":"FORMAL","tag":"NORMAL","defaultPage":null}
```

注意：服务端**按 `resourceId` 关联页面反查**出 `schemaState=FORMAL`（`setSchemaState` 命中
`selectOnePageByPageId` 得到原节点的 schema_state=2），未传也被正确派生。
`status:0 code:BOOT_0000 data.content=<新节点 id>`；写侧未传 `relationId` ⇒ 服务端 `Ids.gidLong()` 补。

## 3. ★ 父菜单 `default_page` **自动**落（无需显式调用）

`createFunctionNode`(:252) 对 `type != MENU` 的节点追加调用
`handleFunctionDefaultPage(parentId)`(:1181)，其判据（CFR）：

```
子节点 = (app_id=父appId) AND (parent_id=父id) AND type != MENU
         AND (pageType IS NULL OR pageType != SUBPAGE)，按 create_time 升序
若子节点为空        → 父: default_page=0, url='', out_app=false, relation_app=''
若 defaultPage ∉ 子节点集合 → 取「最早创建」的一个 → 写 defaultPage + url + relationApp
```

**LIVE 实测**：

```
建 C1 后 父: defaultPage=4630606675502338872 url=xzhpage951440
建 C2 后 父: defaultPage=4630606675502338872 url=xzhpage951440   ← 未被新节点改写（containsKey 判据正确）
删除 C2 后 父: defaultPage=4630606675502338872                    ← 保留
```

⇒ **建 PAGE 子节点一次调用即可同时消 `08100`**，不需要额外的 `default_page` 调用。

## 4. 显式 `default_page` 与三前提（LIVE PASS）

```
POST /service/udc/function/default_page
{"functionId":"-1628253460115858501","sourceId":"<子节点id>"}
→ {"code":"BOOT_0000","data":{"content":1}}
```

`FunctionNodeService.setFunctionDefaultPage`(:510) 的**三前提**：

1. `refer.getParentId() == function.getId()`，否则 `BOOT_1000`「菜单绑定的默认页面信息异常」；
2. `excludeSubPage(refer)`（`refer.type == PAGE` 时）：`resourceId` 非空，且
   （有 `relationApp` 直接放行，或 `resourceId` 是数字且 `!= NULL_ID`），
   且该页面 `pageType != SUBPAGE`（SUBPAGE 报「菜单只能绑定主页面」）；查不到页面报 `UDC_PAGE_0004`；
3. `lateralAuthChecker` 对 function 与 refer 的 appId 各查一次（水平权限）。

**三写入**：`function.url = refer.url`、`function.defaultPage = refer.id`、`function.relationApp = refer.relationApp`。

**LIVE A/B**：

| 动作 | 父 `defaultPage` | 父 `url` |
|---|---|---|
| 切到 C2 | `-9192829783122158852` | `xzhdetail958033` |
| 切回 C1 | `4630606675502338872` | `xzhpage951440` |

**负控**（`sourceId` 不是直接子节点，传另一菜单下的页面节点）：`BOOT_1000 菜单绑定的默认页面信息异常` ✓ 前提 1 生效。

## 5. ★ 树回读双端点差异（判「读面 0 子节点」前必须先确认口径）

| 端点 | 口径 | 子 PAGE 是否可见 |
|---|---|---|
| `POST /udc/function/find/tree-and-group {appId}` | `findMenuTree` 置 `onlyMenu=true` | **不可见**（恒空） |
| `POST /udc/function/select/function-tree {params,sort}` | 无 `onlyMenu` | **可见** |

`selectFunctionTree`(:1427) 先按 `type == MENU && tag ∉ {BIZ_HOME, SPACE_MENU}` 过滤，
再 `buildFunctionTree` —— 所以 `find/tree-and-group` 的 `pcTree` 里菜单 `childNodes` **恒为空，
不是「没建成」**。

**入参形状（实测踩坑）**：

```
POST /udc/function/select/function-tree  {"appId":...,"terminalType":"PC"}          → BOOT_3000
POST /udc/function/select/function-tree  {"params":{appId,terminalType},"sort":{}}  → BOOT_0000 ✓ 两层包装
```

另：`selectFunctionTree` 会**剔除值为 null/空白的参数**，`terminalType` 缺失即报 `UDC_APP_0026`。

**树回读实证**（`select/function-tree`）：

```
menu:  {"id":"-1628253460115858501","name":"小爪验收菜单","type":"MENU",
        "defaultPage":"4630606675502338872","url":"xzhpage951440"}
child: {"id":"4630606675502338872","name":"小爪验收页面","type":"PAGE",
        "url":"xzhpage951440","resourceId":"1520098474917276520","schemaState":"FORMAL"}
```

## 6. `08100` 的真实触发条件（CFR + LIVE 双证）

`FunctionNodeDetectionUtils#doDetection` 的叶菜单筛选逐条：

```
① terminalType == PC
② type == MENU
③ tag ∉ {ROOT, SPACE_MENU, BIZ_HOME}
④ childNodes 为空 或 无任何 type==MENU 的子节点        ← 注意「或」：子节点全为 PAGE 仍判空
⑤ 命中后 defaultPage == null 或 == NULL_ID(0) 才产 08100
```

`ConsistenceDetectionCodeEnum`：`UDC_CE_FUNCTION_NODE_MIS_DEFAULT_PAGE(500, "UDC_CE_FUNCTION_NODE_08100", ...)`。

⇒ **WARN 文案是「未设默认页」，真实充分条件是「无子页面可指向」**。因此：
- 只给菜单加 PAGE 子节点即可清零（LIVE 已验证 WARN 9 → 8）；
- 上一轮文档里写的「空目录无处设默认页」措辞**不准确**，正确表述是「**无子页面可指向**」。

## 7. 收尾与副作用登记（诚实记账）

- 为验证端点选择，我先用 `POST /udc/function` 做了 3 次逐步探针（`xzhPgProbe0/1` + 正式体），
  **全部 BOOT_4000 且零落库**（`COUNT(*)=0`，不是「建了再删」）。
- 为验证「切换」语义建了第二个 PAGE 子节点 `-9192829783122158852`，验完已
  `POST /udc/function/delete {"id":<裸 Long>}` 删除（`content=1`），DB 复核仅余 1 个子节点。
- 保留的验收对象：菜单 `-1628253460115858501`「小爪验收菜单」
  → 子节点 `4630606675502338872`「小爪验收页面」(`url=xzhpage951440`, `resourceId=1520098474917276520`)。
- `update/name/function-refer` 入参为 `@MultiRequestBody {appId, relationId, name}`（**用 relationId 不用 id**）。

## 8. 复现脚本（scratch，受 24h 清理）

`<HERMES_HOME>/cache/scratch/menu5/m1_probe.py`（读面）· `m2_create.py`（DB Error 复现）·
`m3_refer.py`（正确端点）· `m4_verify.py`（自动落 + 检测）· `m5_default_page.py`（A/B + 负控）·
`m6_cleanup.py`（删探针 + 改名 + 终态）· `m7_tree.py`（树回读双口径）· `m8_state.py`（检测状态形状）

**检测范式**：`POST /udc/application/do/detection {appId}` → 轮询
`POST /udc/application/do/detection-state {appId}`（`data.content.status`；`SUCCESS|DOING`，
`errorCount/seriouCount/warnCount`）→ 读 `POST /udc/graphql?udcApplicationSearchDetectionPost`。
