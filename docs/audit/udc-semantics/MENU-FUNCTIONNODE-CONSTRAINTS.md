# UDC 菜单/导航（功能节点）域 约束（后端权威，反编译 5.3.517）

**链路（前端→REST→biz→交互表）**：
前端 `src_pages_design_functions_index` / redux `module-17244`（`udcFunction*` op）
→ `FunctionNodeController`（`udc/function`）
→ `com.seeyon.udc.page.domain.service.FunctionNodeService`（业务逻辑）
→ `FunctionNodeEntity`（**交互表 `udc_function_node`**）
→ `FunctionNodeDto`（udc-plugin-api）

**跨店**：`udcMetaDataSelectFunctionNodeWithPageTreePost`（元数据侧菜单树）、`udcPageRouteGet`（页面路由）。

## 1. 功能节点创建/更新（FunctionNodeDto）必填

| 字段 | 类型 | 必填 | 限制 | 说明 |
| --- | --- | --- | --- | --- |
| `appId` | Long | ★ | — | appId |
| `terminalType` | TerminalTypeEnum | ★ | — | 端类型 PC/MOBILE |
| `type` | UdcNodeTypeEnum | ★ | — | MENU/PAGE/REPORT/EXT_LINK/PORTAL_SPACE |
| `name` | String | ★ | 1..64 (`@NotEmpty @Length`) | 功能显示名称 |
| `icon` | String | | ≤100 | 功能图标 |
| `permission` | Boolean | | — | 权限配置（默认 true） |
| `appBizHome` | Boolean | | — | 应用业务首页（默认 false） |
| `parentId` | Long | | — | 父功能id |
| `defaultPage` | Long | | — | 默认页面 |
| `url` | String | | ≤500 | url |
| `relationId` | Long | | — | 关联id |
| `tag` | FunctionTagEnum | | — | 功能标记（默认 NORMAL） |
| `resourceId` | String | | ≤255 | 引用资源 id 或 fullName |
| `relationApp` | String | | ≤100 | 关联应用 |
| `openState` | OpenStateEnum | | — | EDIT/VIEW/INPUT |
| `pageParam` | String | | — | 页面入参 |
| `pageType` | String | | ≤50 | 页面类型 |
| `orderNo` | Integer | | — | 排序号（默认 0） |
| `childNodes` | List\<FunctionNodeDto\> | | — | 子节点 |

## 2. 枚举
- **UdcNodeTypeEnum**：MENU 0 / PAGE 1 / REPORT 2 / EXT_LINK 3 / PORTAL_SPACE 4
- **OpenStateEnum**：EDIT 0 / VIEW 1 / INPUT 2
- **PageSchemaStateEnum**：NONE -1 / EMPTY 0 / DRAFT 1 / FORMAL 2 / CUSTOMIZE 3 / REFERENCE 4
- **FunctionTagEnum**（17+）：NORMAL 0 / ROOT 1 / BIZ_HOME 2 / ENUM_MANAGE 3 / PARAM_MANAGE 4 /
  DEDUCT 5 / EXTENSION_PLAN 6 / SERIAL_NUMBER 7 / BILL_CATEGORY 8 / ARCHIVE_CATEGORY 9 /
  DATA_FLOW 10 / BIZ_RULE 11 / BASE_SET 12 / SPACE_MENU 13 / DEFAULT_GROUP 14 /
  EXTENSION_REFER_CONTROL 15 / EXCEL_SETTING 16 / CUSTOM_PAGE 17
- **TerminalTypeEnum**：PC / MOBILE / ALL

## 3. 交互表 `udc_function_node`（FunctionNodeEntity）
列：`name`(VARCHAR 64 NOT NULL) / `icon`(100) / `permission`(TINYINT) / `app_biz_home`(TINYINT) /
`parent_id`(BIGINT) / `terminal_type`(SMALLINT) / `default_page`(BIGINT) / `url`(500) / `relation_id` /
`tag`(SMALLINT) / `resource_id`(255) / `relation_app`(100) / `open_state`(SMALLINT) /
`page_param`(LONGTEXT) / `page_type`(50) / `type`(SMALLINT) / `order_no`(INT) / `out_app`(TINYINT) /
`schema_state`(SMALLINT)。索引：app_id / resource_id / parent_id（均带 tenant_id）。

## 4. REST 端点（FunctionNodeController，`udc/function`）
`POST update` / `POST create/function-refer` / `POST update/function-refer` / `POST update/name/function-refer` /
`GET {id}` / `POST delete` / `POST batch-delete` / `POST copy` / `POST /app-biz-home` / `POST /cancel/app-biz-home` /
`POST default_page` / `POST select/function-tree` / `POST delete/refer-page` / `POST sort` /
`POST find/tree-and-group` / `POST update/root/to-user-center` / `POST update/root/handle-function` /
`GET page/in_params/{referId}`

## 5. 前端 op（`udcFunction*`）
`udcFunctionPost` / `udcFunctionUpdatePost` / `udcFunctionDeletePost` / `udcFunctionBatchDeletePost` /
`udcFunctionCopyPost` / `udcFunctionSortPost` / `udcFunctionDefaultPagePost` / `udcFunctionGet` /
`udcFunctionAppBizHomePost` / `udcFunctionCancelAppBizHomePost` / `udcFunctionCreateFunctionReferPost` /
`udcFunctionUpdateFunctionReferPost` / `udcFunctionUpdateNameFunctionReferPost` / `udcFunctionDeleteReferPagePost` /
`udcFunctionSelectFunctionTreePost` / `udcFunctionFindTreeAndGroupPost` / `udcFunctionPageInParamsReferGet`

## 6. 机器可读模型
`components/udc/menu_constraints.py`：`FUNCTION_NODE_FIELDS` / `FUNCTION_NODE_REQUIRED` / `NODE_TYPES` /
`OPEN_STATES` / `PAGE_SCHEMA_STATES` / `FUNCTION_TAGS` / `TERMINAL_TYPES` / `FUNCTION_NODE_TABLE` +
`validate_function_node`。

## 7. 写链行为面（第二十六轮 LIVE PASS）

字段面见上；**写链行为面**（端点选择 / 自动落默认页 / 三前提 / 树回读口径）已单独立档：
`core/facts/udc/write-chain/menu-default-page-write-chain.md`。要点：

| 事实 | 内容 | 证据 |
|---|---|---|
| ★ 建 PAGE 子节点 | **必须用 `POST /udc/function/create/function-refer`**；`POST /udc/function` 的 `FunctionDto` **无 `resourceId`** ⇒ `selectOnePageByPageId` 拿 null ⇒ `[resourceId]字段的条件数据不能为null` ⇒ `BOOT_4000` | LIVE 3/3 + pod 堆栈 + CFR |
| 自动落默认页 | 建 `type != MENU` 子节点后 `handleFunctionDefaultPage(parentId)` 自动写父的 `defaultPage/url/relationApp`（取最早创建者，仅 PC）；**一次调用即消 08100** | LIVE |
| 显式设默认页 | `POST /udc/function/default_page {functionId, sourceId}`；前提 `sourceId.parentId == functionId` 否则 `BOOT_1000` | LIVE A/B + 负控 |
| 树回读 | `find/tree-and-group` 置 `onlyMenu=true` ⇒ **子 PAGE 恒不可见**（不是没建成）；要带子节点须用 `select/function-tree`，**body 两层包装 `{params,sort}`** | LIVE |
| 改名 | `POST /udc/function/update/name/function-refer {appId, relationId, name}`（**relationId 而非 id**） | LIVE |
| 删除 | `POST /udc/function/delete` body = **裸 Long** `{"id":<Long>}` | LIVE |

**`08100` 的真实充分条件**（更正 §4 旧措辞）：
`FunctionNodeDetectionUtils#doDetection` 判据是「无子节点 **或** 无 `type==MENU` 的子节点」，
故子节点全为 PAGE 时仍算「空目录」。WARN 文案是「未设默认页」，**真实原因是「无子页面可指向」**。
