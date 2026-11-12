# UDC 搭建语义总审计

日期：2026-10-11
主线：`<XIAOZHUA_AGENT_ROOT>`
状态：只读源码审计报告完成；协议模型、完整搭建、test2 写入与构建验收均未完成/未执行。

## 结论

当前 `xiaozhua-agent` 主线不是完整 UDC 搭建执行器，而是：

```text
证据目录 + 只读组件 + 需求解析 + 声明级生成 + dry-run/deploy plan + 宿主适配
```

Hermes 下的 skill 是操作规程，不是 `xiaozhua-agent` 的实现证明。仓库测试最新实跑为 `399 passed in 9.43s`，但测试不覆盖“按自然语言搭建完整订单表单、菜单、微流程和构建回读”。

## 已确认的正确链路

### 1. 页面

```text
前端控件注册表/remote schema
  → Redux childById 控件树
  → pageSchema JSON
  → savePageDraf / submitPage
  → udc_page_schema draft_page_schema/page_schema
  → 页面规则/功能节点/元数据
  → 构建一致性检测
  → 运行态元数据与页面
```

控件不是数据库里的一张“组件用法表”。内置控件 schema 由前端 bundle 注册；自定义控件可按 package、copVersion、schemaModule 动态加载。页面实例保存后才进入 `udc_page_schema`。

页面控件至少涉及：

```text
id/type/parentId/settings/dataSource/events/uiModel/uiModelSchema/children/extraChildren
```

实体数据源必须位于控件顶层 `dataSource`，不是 `settings.dataSource`。表格列必须从同类标品 deep-copy，不能手写少量字段。

### 2. 页面规则、过滤方案、实体规则

这三类不能混用：

```text
udc_filter_plan                 列表/表格查询过滤方案
微流程 type=FRONTEND             页面规则
微流程 type=FRONTEND_PARAM       子规则
微流程 type=ENTITYRULE           实体规则
```

前端创建类型映射在 customer frontend bundle 中已找到：

```text
frontend               → FRONTEND + MANUAL
frontendparam          → FRONTEND_PARAM
frontendfunction       → FUNCTION + MANUAL
entityrule             → ENTITYRULE + MANUAL
eventmonitor           → SERVICE + BUSINESS_EVENT
timingtask             → SERVICE + SCHEDULE
servicedefinition      → SERVICE + MANUAL
```

所以之前把 `udc_filter_plan` 叫页面规则是错误口径。

### 3. 页面事件

真正挂载点是：

```text
pageSchema.childById[controlId].events[]
```

`eventDefine[]` 只登记事件元数据，不能替代行为绑定。

动作类型真实值域：

```text
buildin | widget | microflow | enevtThrow
```

行编辑应当是 `buildin/openPage` 穿透详情页，配 `paramsMapping`；不是随便挂 `ENTITY_EDIT`。面板打开/关闭是 `widget + CONTROL + targetAction=panel_openPanel/panel_closePanel`。微流程按钮必须带真实微流程 id。没有 events 的按钮只会渲染，不会有行为。

### 4. 微流程

```text
dataSchema JSON string
  → 后端反序列化为 MicroFlow BO
  → NodeParser/节点解析
  → actionType 对应 Activity
  → 模板/代码生成
  → state=20 的发布态微流程参与构建
  → 生成 Service/Controller/Listener/Schedule
  → 运行态调用/回读
```

前端节点 actionType 至少包括：

```text
RETRIEVE / RETRIEVE_ARRAY / CONVERT_DATA / CREATE_VARIABLE /
CREATE_LIST / CREATE_ENTITY / CREATE_BATCH_ENTITY /
CHANGE_ENTITY / CHANGE_BATCH_ENTITY / DELETE_ENTITY /
CALL_APP_SERVICE / SUB_MICROFLOW / CALL_DATA_FLOW /
DATA_MAPPING / LIST_OPERATION / MAP_OPERATION / FOR_EACH
```

5.3.517 `udc-biz` jar 已找到真实模板，例如：

```text
autocode/JAVA/2.7/templates/microflow/RetrieveActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/ConvertDataActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/CreateEntityActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/ChangeEntityActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/BusinessEventActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/event/BusinessEventListener.java.ftl
autocode/JAVA/2.7/templates/microflow/schedule/MicroFlowSchedule.java.ftl
```

这证明节点必须同时满足前端 schema、checkSchema、后端解析器、模板和发布态要求；保存成功不等于节点功能成立。

前面订单微流程的问题：

- 人员多选转列表只做了一个临时 `CONVERT_DATA` 探针，没有平台生成物和运行回读。
- “流程信息”没有真实 BPM 查询契约闭环。
- “流转日志和意见列表拼接”实际没有真实日志查询、意见查询和合并节点，只拼了订单流程字段，不能算完成。
- 生单/扣减不能混成普通微流程节点：实体生单、DataFlow、DeductionRule、DeductionMap 是独立对象/链路。

### 5. 实体/字段/默认值/参照/枚举/事件

字段创建不是简单插入：

```text
AttributeDto
 → defaultValue/default expression/system variable caption
 → dataType/relation/multiSelect 校验
 → reserved name/duplicate/db-length/index-length 校验
 → DAO
 → AttributeCreateEvent
 → audit log
```

源码证据：

- `udc/udc-biz/.../AttributeService.java:298-332`
- `AttributeService.java:617-705`
- `AttributeService.java:735-769`
- `AttributeService.java:2380-2424`

默认值至少分为：

```text
defaultValue
defaultValueCaption
defaultValueExpressionDesignData
defaultValueExpressionRuntimeData
defaultValueSystemVariable
defaultValueIsChange
```

多选人员不是自定义 `UserSelect`：

```text
dataType=ENTITY
relationType=Many2OneAssociation
relationApp/relationEntity
multiSelect=true
```

前端实际注册过的人员组件是 `UiBusinessSelectPeople`；参照类组件是 `UdcReference` / 关系字段 schema。

实体装配时会单独加载属性、索引和实体规则标志：

- `EntityService.java:1245-1259`
- `EntityService.java:1350-1376`
- `EntityService.java:1408-1425`

实体规则标志来自 `microFlowService.loadHasRuleEntityId(appId)`，按 `VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE` 区分，不能用字段默认值替代。

事件 REST 控制器事实：

- `POST /udc/event`
- `POST /udc/event/create-with-data`
- `POST /udc/event/update`
- `POST /udc/event/list/business-event`
- `POST /udc/event/list/events`

源码：`udc/udc-web/.../EventController.java:43-131`。

事件定义和事件监听动作仍是两层：事件表保存事件，监听微流程 `trigger=BUSINESS_EVENT + messageInfo` 才是动作绑定。

枚举项导入导出已在源码确认：`UdcEnumItemController.java:126-143`。这不等于实体列表的 Excel 导入导出；后者还需要页面动作、模板和实体数据导入链的独立证据。

## 当前主线代码缺口

| 能力 | 当前状态 |
|---|---|
| UDC 只读证据/报告 | 已有 |
| 需求解析 | 已有，确定性，不能替代语义规划 |
| Java skeleton | 已有，声明级，不是平台生成物 |
| 页面定义骨架 | 已有，有限元数据字段，不是可运行 pageSchema builder |
| 前端组件注册表解析 | 未实现 |
| 页面 childById/dataSource/columns/events builder | 未实现 |
| 页面 schema validator | 未实现 |
| 页面规则 builder | 未实现 |
| 菜单/function tree builder | 未实现；已有查询证据，不代表写能力 |
| 子页面/外框 builder | 未实现 |
| 微流程 graph/dataSchema builder | 未实现 |
| 节点输入输出/模板映射 | 未实现为主线代码；源码/模板矩阵已形成 |
| 实体字段默认值/参照/事件/字段集 planner | 未实现为独立模型 |
| DataFlow/Deduction 生单扣减链 | 保存/生成/触发/IO 静态契约已补齐；主线模型和目标运行链未完成 |
| 实体 Excel 默认模板/实体数据导入导出完整 planner | 入口和模板静态证据已找到；目标应用运行链未验证 |
| 页面按钮构建抓包/等价性验证 | 未实现 |
| 写入执行器 | 明确 DENIED，宿主执行方案 |

## 之前临时搭建结果应如何定性

全部降级为：

```text
UNVERIFIED_PROBE
```

不能称为已完成搭建，原因是缺少：

1. 前端 schema 约束验证；
2. 页面事件/组件标品对照；
3. 页面规则与过滤方案分类；
4. 微流程节点模板/解析器验证；
5. state=20 发布态与生成类验证；
6. 页面按钮真实 Network 构建证据；
7. 构建终态、运行态元数据和业务数据回读。

## 页面/菜单/子页面/外框审计结论

独立逐行报告已完成：`docs/audit/udc-semantics/page-menu-source-audit.md`。该报告基于旧源码 Controller/Service/DTO 行号和 xiaozhua-agent 持有的 5.3.517 静态 javap 索引；不是 test2 运行验证。关键内容包括 PageInfo/PageSchema/PageDataSource/FunctionNode/PageLayout 的 ID 角色、基础创建与草稿/正式提交差异、菜单页面引用、子页面外框限制、页面复制时微流程/ID 替换，以及页面按钮构建仍未逐字抓包的边界。

## 生单、扣减与导入导出的证据进展

专门报告 `flow-excel-source-audit.md` 和机器清单 `flow-excel-contracts.json` 已补齐设计态保存、落表、代码生成模板、生命周期触发和 Excel 异步处理的静态契约。离线工具 `tools/core/audit_udc_flow_excel.py`（**已移入 `_attic_pending/one-off/unsorted/audit_udc_flow_excel.py`**，仓库内已无此路径） 可重新提取/回放证据，但不接入平台执行 registry。

- `CALL_DATA_FLOW` 调用实体生单运行服务，输出 `CallDataFlowResultDto` 的 targetIds/updateIds；没有直接调用 Deduction 的证据。
- Deduction 独立保存图、规则、算法和状态明细，生成 BeforeCreate/BeforeUpdate/BeforeDelete 同步监听器，执行 DO/UNDO 并写 deductionInfo/日志。
- Excel 模板表静态确认为 `ctp_excel_export_template`，metadataContent 与 excelHeadInfo 分别记录层级列元数据和拉平表头；当前环境的实际 schema/database 未读取。
- Excel check 可能创建跨环境模板并发布异步检查事件，不应自动分类为只读。导入/导出返回 redisKey，只是任务句柄。
- 未闭合的项仍是目标运行版本绑定、当前应用生成物、Gateway/前端实际调用和订单业务结果回读。静态证据不称 LIVE PASS。

## 下一步正确顺序

1. 在 `xiaozhua-agent` 内实现版本化 UDC schema model：Entity/Attribute/Enum/Reference/Event/Index/AttributeGroup/Page/FunctionNode/MicroFlow/DataFlow/Deduction。
2. 从前端 bundle 和 5.3.517 jar 提取控件 schema、动作枚举、节点类型和模板映射，保存为可引用事实，不写死到临时脚本。
3. 实现只读 validator：页面 tree、数据源、列、组件属性、events、微流程 input/output、节点模板、页面规则分类。
4. 实现 dry-run planner，输出完整需求链和 unknowns；仍不执行写。
5. 再实现宿主适配和写步骤回读；构建必须先抓页面按钮请求，再证明与 API 的等价性。
6. 最后用独立 `zzprobe` 应用做最小闭环：实体→字段→页面→事件/规则→微流程→按钮→页面构建→deploy_record→生成物→运行态回读。
