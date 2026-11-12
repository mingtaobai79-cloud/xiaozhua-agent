# UDC 页面保存、菜单功能节点、子页面与外框源码审计

日期：2026-10-11
主线：`<XIAOZHUA_AGENT_ROOT>`
源码树：`<PATH>
运行版本配置：`<XIAOZHUA_AGENT_ROOT>/config/artifact-versions.yaml`

证据边界：

- 下文 `backend/...` 是旧源码树静态证据；不能直接等同当前 test2 行为。
- `test2` 配置标记为 UDC 镜像 `5.3.496`，见 `config/environments.yaml:11-17`。
- 本地 5.3.517 是独立静态 artifact 证据族，不能与旧源码树或 test2 镜像混称。
- 本报告不执行平台写入、不调用网络、不触发构建、不抄录客户业务明细。

## 1. 结论

页面不是一个单独的 JSON 文件，也不是菜单或构建接口自动生成的副作用。设计态至少由以下对象协作：

```text
Application
  ├─ PageInfoEntity             页面基础信息
  ├─ PageSchemaEntity           页面 JSON / 草稿 JSON / 入出参
  ├─ PageDataSourceEntity       独立页面/外框数据源记录
  ├─ FilterPlan                 列表默认/自定义过滤方案
  ├─ ReferConfig                自定义参照配置
  ├─ FunctionNodeEntity         菜单、页面资源、页面引用
  └─ PageLayoutEntity           外框基础信息
       └─ PageSchemaEntity      layout_id 对应的外框 JSON
```

页面设计器链路应理解为：

```text
前端控件注册表
  → Redux childById 控件树
  → pageSchema JSON string
  → 草稿保存 / 正式提交
  → PageInfo + PageSchema + DataSource + FilterPlan + ReferConfig
  → FunctionNode/资源注册
  → 一致性检测/构建
  → 发布元数据/运行态页面
```

当前 `xiaozhua-agent` 只具备证据、只读和方案生成能力，不具备正式的页面 schema builder、菜单写入器、外框 builder 或构建按钮验收器。

## 2. Controller 路径证据

### 2.1 PageInfo

旧源码：

```text
udc/udc-web/src/main/java/com/seeyon/udc/controller/PageInfoController.java:41
```

类级路径是 `udc/page-info`。方法级路径包括：

```text
POST /udc/page-info/base-info/create
POST /udc/page-info/base-info/update
POST /udc/page-info/batch-create
POST /udc/page-info/update
POST /udc/page-info/update-draf
GET  /udc/page-info/{id}
GET  /udc/page-info/detail/{id}
GET  /udc/page-info/select-by-appId/{appId}
POST /udc/page-info/select-list-with-draft-schema/by-conditions
```

对应源码行：

```text
PageInfoController.java:55-68
PageInfoController.java:92-105
PageInfoController.java:122-143
PageInfoController.java:160-167
```

由类级和方法级注解拼接出的 REST 路径，不能直接当作前端 GraphQL resolver 的证据。前端 bundle 静态证据显示：

```text
savePageDraf → udcPageInfoUpdateDrafPost
submitPage   → udcPageInfoUpdatePost
```

这只证明前端 mutation 字段名和保存意图。GraphQL resolver 到上面 REST Controller 的实际桥接，仍需当前运行 artifact/Network/Resolver 证据确认。

5.3.517 字节码目录中的 `PageInfoController.javap.txt` 确认类级 `udc/page-info` 及上述方法字面量；这是 5.3.517 静态字节码事实，不是当前 test2 live 成功证据。

### 2.2 FunctionNode

旧源码：

```text
udc/udc-web/src/main/java/com/seeyon/udc/controller/FunctionNodeController.java:40
```

类级路径为 `udc/function`，关键方法：

```text
POST /udc/function                         创建功能/节点
POST /udc/function/create/function-refer   创建页面引用
POST /udc/function/update/function-refer   修改页面引用
POST /udc/function/select/function-tree    查询功能树
POST /udc/function/find/tree-and-group     查询菜单树与分组
POST /udc/function/default_page            设置默认页面
GET  /udc/function/page/in_params/{referId}
```

源码行：`FunctionNodeController.java:40-49`、`61-79`、`115-127`、`145-164`。

这说明菜单资源不是页面 JSON 顶层的一个 caption 字段；菜单/页面引用有独立的 FunctionNode DTO/Entity 和服务。

### 2.3 PageLayout

旧源码：

```text
udc/udc-web/src/main/java/com/seeyon/udc/controller/PageLayoutController.java:40
```

类级路径为 `udc/page-layout`，关键方法：

```text
POST /udc/page-layout/base-info/create
POST /udc/page-layout/base-info/update
POST /udc/page-layout/update
POST /udc/page-layout/update-draf
GET  /udc/page-layout/{id}
GET  /udc/page-layout/detail/{id}
GET  /udc/page-layout/detail-app-id/{appId}
GET  /udc/page-layout/params/{layoutId}
```

源码行：`PageLayoutController.java:48-73`、`78-114`。

5.3.517 字节码目录中的 `PageLayoutController.javap.txt` 对类级路径和方法字面量有对应静态证据。不能把 `page-layout/update` 的存在等同于设计器“保存并提交”按钮已走该接口。

## 3. PageGroup、PageInfo、FunctionNode、Layout 的 ID 角色

### 3.1 页面基础 DTO

`PageDefinitionDto` 定义了基础创建输入：

```text
PageDefinitionDto.java:33-87
```

关键字段：

```text
appId             应用数字 ID
relationGroupId   PC/移动等同组页面的关联组
caption           页面显示名
pageType          LIST/DETAIL/PORTLET/SUBPAGE 等受控页面类型
pageUrl           页面标识/URL
pageItems         各终端页面定义列表
curTerminalType   当前终端
masterEntityIds   页面对应主实体
relationAppName   依赖应用实体时的来源应用名
groupId           PORTLET 栏目分组
```

`relationGroupId` 不是单个页面的 `pageId`；它用于把 PC、移动等页面定义放入一个关联组，源码注释见 `PageDefinitionDto.java:53-55`。

### 3.2 PageItemDefinitionDto

`PageItemDefinitionDto.java:28-86` 是 `pageItems[]` 的单终端/单页面输入：

```text
actionType       NORMAL/INSERT/UPDATE/DELETE 等
sourceId         来源页面/模板 ID，复制场景使用
layoutId         本应用外框 ID；默认 NULL_ID
layoutInfo       外部应用外框 JSON 信息
pageUrl          该终端页面 URL
urlType          PC/MOBILE
menuId           归属菜单节点 ID
menuName         需要自动创建的菜单名
inParams         页面入参 schema
outParameters    页面出参 schema
pageSchema       页面定义 JSON 字符串
referConfigParameters 自定义参照配置
schemaState      页面 schema 状态
```

所以一个列表页/详情页组合不是一个平面 page JSON；至少要有页面基础信息、终端 item、schema、菜单引用和可能的外框引用。

### 3.3 PageInfoEntity 与 PageSchemaEntity

`PageInfoService.create`/`batchCreate` 将 `PageInfoDto` 拆成基础表和 schema 表：

```text
PageInfoService.java:877-915
```

它为一批页面生成同一个 `relationGroupId`，为每个页面分配自己的 page id，基础信息写 `PageInfoEntity`，以下字段进入 `PageSchemaEntity`：

```text
pageSchema
inParams
pageId
appId
```

`PageSchemaEntity.java:24-87` 显示真实表是 `udc_page_schema`，关键列包括：

```text
page_id
layout_id
page_schema
draft_page_schema
operation_steps
in_params
out_parameters
in_portlet_params
schema_state
```

`layout_id` 默认是 `NULL_ID`，因此普通页面 schema 与外框 schema 是同一张 schema 表的不同关联方式，不能只按 page_id 查而忽略 layout_id。

### 3.4 FunctionNode 的 ID 和引用关系

`PageInfoService.createRefer` 直接构造页面功能节点：

```text
PageInfoService.java:817-831
```

字段关系是：

```text
FunctionNodeEntity.id       菜单/页面引用节点自身 ID
FunctionNodeEntity.parentId 父菜单节点 ID
FunctionNodeEntity.resourceId 页面资源 ID，写入 PageInfoEntity.id
FunctionNodeEntity.relationId 页面关联组 ID
FunctionNodeEntity.type      PAGE 或 MENU
FunctionNodeEntity.url       PageInfoEntity.pageUrl
```

这条关系是页面能从菜单打开的关键：

```text
FunctionNode(PAGE).resourceId → PageInfoEntity.id
FunctionNode(PAGE).relationId → PageInfoEntity.relationGroupId
```

页面不是“建了就自动可见”。还要有 PAGE 类型功能节点、正确 parent、终端类型、URL 和 schema 状态。

## 4. createBaseInfo 到底做什么

Controller 调用 `PageInfoService.baseCreate`：

```text
PageInfoController.java:55-58
PageInfoService.java:378-409
```

`baseCreate` 的实际链路：

1. `checkDefinitionPageDto` 校验 pageItems、URL、pageType、appId、菜单归属、分组和子页面限制。
2. `createPages` 生成关联组、PageInfoEntity、PageSchemaEntity。
3. 非复制来源发布 `PageCreateEvent`。
4. 如果 pageItems 带 `menuId/menuName`，调用 `setFunctionRefer` 建菜单/页面引用。
5. 返回 `PageInfoGroupDto`，包括 relation group id、page ids 和 page items。

源码证据：`PageInfoService.java:379-408`。

`createPages` 的关键行为：

```text
PageInfoService.java:443-538
```

- 生成新的 `relationGroupId`。
- 给每个 item 生成或保留页面 id。
- 复制 `pageUrl/urlType/layoutId/layoutInfo/inParams/outParameters/pageSchema`。
- 生成 `PageSchemaEntity`。
- 复制场景下替换筛选方案 id。
- 批量保存 PageInfoEntity 和 PageSchemaEntity。
- 复制/保存草稿及正式筛选方案。

因此 `createBaseInfo` 不是“只写一行 page_info”，也不是“只保存 pageSchema”；它可能同时创建页面 schema、菜单引用、默认/复制过滤方案和设计态日志。

### 创建校验

`checkDefinitionPageDto` 和相关方法：

```text
PageInfoService.java:2592-2739
```

已经确认的边界：

- `pageItems` 为空会拒绝。
- 顶层 `pageUrl` 必须存在且通过特殊字符校验。
- pageType 必须属于 `PageTypeEnum`。
- appId 必须能被 `applicationService.checkApplication` 找到。
- 非表单应用的关联页面必须有 `menuId` 或 `menuName`。
- PORTLET 的 groupId 若存在必须对应栏目分组。
- SUBPAGE 不能绑定外框，不能有非空 outParameters。

这解释了为什么“写入一个最小页面 JSON”不等于平台认可的页面。

## 5. 正式提交、草稿和数据源转换

### 5.1 正式 `update`

`PageInfoService.update(PageInfoDto)`：

```text
PageInfoService.java:1202-1315
```

实际步骤：

1. 要求页面 id。
2. 读取 `inParams`，同步到关联 FunctionNode 的 `pageParam`。
3. 保留菜单已有默认表达式值，再用页面参数更新/删除/追加菜单参数。
4. 校验子页面 outParameters/layout 限制。
5. `updataSchema` 把 pageSchema 写为正式内容，并把 draftPageSchema 同步为相同内容，schemaState 置 FORMAL。
6. 发布 `PageSchemaStateChangeEvent(FORMAL)`。
7. 更新 PageInfoEntity。
8. 读取页面数据源、过滤方案、自定义参照，保存默认过滤方案。
9. PORTLET 页面同步门户。
10. 发布 `FunctionCreatePageSchemaEvent` 和 `PageInfoSaveEvent`。
11. 清理资源解析缓存。

`updataSchema` 的直接证据：

```text
PageInfoService.java:2418-2474
```

如果正式 schema 为空，已有 schema 时会拒绝；更新时同时写 `page_schema`、`draft_page_schema` 和 schema state。

### 5.2 草稿 `updateDraft`

`PageInfoService.updateDraft(PageInfoDto)`：

```text
PageInfoService.java:1417-1506
```

它只把 `draftPageSchema`、`operationSteps` 写入 `udc_page_schema`，schemaState 置 DRAFT，并发布 `PageSchemaStateChangeEvent(DRAFT)`。它不会把草稿变成正式 `page_schema`。

因此：

```text
暂存草稿 != 保存并提交
draft_page_schema != page_schema
schema_state=DRAFT != schema_state=FORMAL
```

### 5.3 pageSchema 与独立 PageDataSource

`PageDataSourceService` 证明页面数据源是独立对象：

```text
PageDataSourceService.java:180-242
```

- `update4Page` 给每个数据源补 appId、pageId、layoutId=NULL_ID、draft 标志，先按 pageId/draft 删除再批量创建。
- `update4Layout` 给每个数据源补 appId、pageId=NULL_ID、layoutId、draft 标志，先按 layoutId/draft 删除再批量创建。

需要特别标注旧源码行为差异：

```text
PageInfoService.update:1280-1282
PageInfoService.updateDraft:1479-1482
```

这两个页面方法中“更新页面数据源”的调用是注释掉的，当前代码只读取 `pageDataSourceService.selectByPageId` 用于日志快照；而 `PageLayoutService.update` 和 `updateDraft` 明确调用了：

```text
PageLayoutService.java:446-449
PageLayoutService.java:565-568
```

所以不能仅根据 `pageSchema` 顶层有 `dataSource` 就断言独立 PageDataSource 表一定同步；必须按目标版本和真实保存通道回读两者。

### 5.4 默认过滤方案不是页面规则

正式保存和草稿保存都会处理 `defaultPlan`。`saveOrUpdateDefaultPlan` 将每个 schema 转成列表过滤方案：

```text
PageInfoService.java:2482-2507
PageLayoutService.java:1300-1336
```

写入的语义包括：

```text
caption="列表默认方案"
sourceType=SYSTEM
planType=LIST
pageId
pageUrl
componentId/sourceId
drivenEntity
content
```

这是列表默认过滤方案，不是 FRONTEND 页面规则微流程。

## 6. 菜单、页面引用和默认页

### 6.1 页面创建时挂菜单

`setFunctionRefer`：

```text
PageInfoService.java:772-813
```

行为：

- `menuName` 非空时，以 menuId 为 parentId 创建或复用 `type=MENU` 的 FunctionNode。
- `menuId` 非空时，查父节点并为页面创建 `type=PAGE` 的引用。
- 页面引用使用页面 caption、pageUrl、relationGroupId、page id、pageType、schemaState。
- `curTerminalType` 决定返回 PC 或 MOBILE 的引用 id。

`createMenuRefer`：

```text
PageInfoService.java:835-856
```

按 `name + terminalType + type=MENU + parentId + appId` 查重，存在则复用，否则创建菜单节点。

### 6.2 FunctionNode 创建时的默认行为

`FunctionNodeService.createFunctionNode`：

```text
FunctionNodeService.java:161-208
```

- appId 必须对应真实应用。
- PAGE 节点必须有非空 relationId。
- 没有 parentId 时挂到终端根节点。
- orderNo 会调整同层节点顺序。
- 根据节点类型/来源设置 schemaState。
- 创建后处理父节点默认页并发布 `FunctionNodeAddEvent`。

这说明菜单、页面引用、排序、终端和 schemaState 都是独立字段，不能只用 pageSchema 的 menuId 替代。

### 6.3 设置默认页面

`FunctionNodeService.setFunctionDefaultPage`：

```text
FunctionNodeService.java:492-530
```

它要求页面引用节点是菜单的直接子节点，复制页面 URL、relationApp 并设置 defaultPage；`excludeSubPage` 会拒绝把 `SUBPAGE` 作为菜单默认页。页面资源 id 必须能查到真实 PageInfo。

### 6.4 页面入参如何进入菜单

`FunctionNodeService.findPageInParams`：

```text
FunctionNodeService.java:2029-2072
```

本应用页面通过 FunctionNode.resourceId 找 PageInfo，再取页面 inParams；依赖应用页面则根据 relationApp、依赖版本和完整资源名查运行元数据。这个逻辑进一步证明：菜单节点不是页面 JSON 的复制品，而是运行时页面入口和参数桥接对象。

## 7. 子页面和外框

### 7.1 子页面硬约束

`PageInfoService.validationSubpage4Layout` 与 `validationSubpage4OutParameters`：

```text
PageInfoService.java:2627-2671
```

当 `pageType=SUBPAGE`：

- `layoutId` 不能是有效外框 id。
- `layoutInfo` 不能引用外部外框。
- `outParameters` 不能是非空 JSON 数组。

该校验在基础创建和页面 update/updateDraft 路径都会被调用：

```text
PageInfoService.java:895-896
PageInfoService.java:1257-1262
PageInfoService.java:1422-1430
```

所以子页面不是“普通页面加一个子页面控件”这么简单；它有自己的 pageType 和参数/外框边界。

### 7.2 子页面控件与资源注册

`PageUtils` 解析页面控件资源时，如果控件类型是 `UdcSubPage`，会从控件 settings 的 `relatedSubPages` 继续解析子页面资源：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/page/util/PageUtils.java:330-369
```

控件本身的资源 code 会带页面 id、控件 id 和父级 code；子页面相关资源也进入资源注册列表。这是页面 schema → 资源/权限树的直接静态证据。

前端控件语义和 settings 来源仍以 bundle 为准，当前主线已有事实件：

```text
core/facts/udc/frontend-assembly-protocol.md:6-24
```

其中 `UdcSubPage` 的 `settings.relatedSubPages` 不能由普通 panel 或任意 container 替代。

### 7.3 外框创建

`PageLayoutService.checkDefinitionPageDto`：

```text
PageLayoutService.java:932-947
```

它校验：

- 外框 item 不能为空。
- 终端类型集合。
- pageUrl 唯一性和合法性。
- appId 应用存在。

`createPages`：

```text
PageLayoutService.java:950-1008
```

行为：

- 为外框组生成 relationGroupId。
- 每个终端生成 PageLayoutEntity 和自己的 layout id。
- 生成 `PageSchemaEntity(layout_id=layoutId)`。
- 如果来源外框/模板存在，复制自定义参照和过滤方案。
- 保存外框、schema、日志。

### 7.4 外框正式保存与草稿

正式 `PageLayoutService.update`：

```text
PageLayoutService.java:434-469
```

会更新外框基础信息、正式 schema、正式数据源、默认过滤方案、参照配置，发布 `PageLayoutSaveEvent` 并清资源缓存。

草稿 `updateDraft`：

```text
PageLayoutService.java:540-584
```

会写 draftPageSchema、operationSteps、草稿数据源和过滤方案，但不会把草稿当正式 schema。

### 7.5 复制外框/页面时的微流程和 ID 替换

页面和外框复制都使用 `PageCreation4MicroFlowContext`：

```text
PageCreation4MicroFlowContext.java:17-59
```

它携带：

```text
sourceAppName
newAppId
functionMiroFlowMapping
microFlowGroupMapping
```

页面复制：`PageInfoService.java:2767-2823`。

外框复制：`PageLayoutService.java:1250-1292`。

复制时先复制页面规则分组和微流程，再构造 old id → new id 映射，最后用 `SchemaParser.idReplace` 替换 pageSchema 中的页面/微流程引用。由此可知，复制一个 JSON 页面不能只复制文本；必须同时处理微流程分组、微流程 ID、页面 ID、筛选方案和参照配置。

## 8. 测试按钮、保存、构建的边界

### 已确认

```text
前端 savePageDraf / submitPage
  → 页面草稿/正式保存意图

后端 PageInfoController.update-draf/update
  → PageSchema + PageInfo + 参数/过滤/参照/资源事件

前端 deploy-normal / app-online-new
  → 设计器构建/上线链路候选
```

前端静态证据已区分：

```text
udcRuntimeDeployNormalPost → {deployDto: e}
udcDeploymentAppOnlineNewPost → deployType=ON_ONLINE
```

### 尚未确认

没有当前会话中通过 CDP `Network.requestWillBeSent` 逐字捕获“页面上测试/构建按钮”请求，因此不能声明：

- 某个 REST 路径就是页面按钮实际请求。
- `deploy-normal` 与按钮请求在 body、鉴权、前置保存、响应处理上完全等价。
- `app-online-new` 是测试构建按钮。

构建验收还必须独立检查 deploy record、前端/后端生成物、运行态元数据和业务页面。HTTP 200、页面保存成功或设计态 schema 存在都不能替代构建结果。

## 9. 对之前手拼页面的直接影响

以前的订单临时页面若出现以下任一情况，不能称为正确页面：

```text
页面只存 PageInfo，没有 PageSchema
页面有 pageSchema，但 dataSource 放进 settings
表格列缺标品列的 componentName/uiModel 等关键键
按钮有文字但 events[] 为空
编辑动作写成未经标品证明的 ENTITY_EDIT
页面有 filter plan，却没有 FRONTEND 页面规则微流程
页面挂了 menuId，但 FunctionNode.resourceId/relationId/schemaState 未回读
子页面绑定了 layoutId 或非空 outParameters
只保存 draft_page_schema，未正式 submit
只查设计态，没有构建记录/生成物/运行态回读
```

这些是协议/验收问题，不是继续追加一个 JSON 字段就能证明已经解决的问题。

## 10. xiaozhua-agent 当前缺口和正确落地顺序

当前主线仍缺：

1. 版本化 PageInfo/PageSchema/PageDataSource/PageLayout/FunctionNode 模型。
2. 前端控件 registry/schema reader。
3. childById 树、dataSource、列、events 的 validator/builder。
4. pageType、terminal、relationGroup、layout、subpage 参数约束 validator。
5. 页面保存与菜单/页面引用的 operation contract/readback verifier。
6. 页面规则 FRONTEND 与 filter plan 分离的 planner。
7. 页面复制时微流程/分组/页面 ID 替换器。
8. 页面按钮真实 Network 抓包和构建等价性测试。

正确顺序：

```text
读取标品 schema
  → PageSchema model/validator
  → PageDataSource/FilterPlan/ReferConfig model
  → PageInfo/FunctionNode/PageLayout model
  → dry-run 页面/菜单/外框计划
  → 只读回读 verifier
  → 经用户授权的宿主执行
  → submit/构建/生成物/运行态验收
```

当前仍保持：`xiaozhua-agent` 不直接执行平台写操作；任何历史订单页面对象均为 `UNVERIFIED_PROBE`，不能当正式交付。
