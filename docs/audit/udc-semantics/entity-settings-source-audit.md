# UDC 实体、字段、设置与规则链源码审计

日期：2026-10-11
主线：`<XIAOZHUA_AGENT_ROOT>`
平台源码证据：`<PATH>
证据性质：旧源码树静态证据，不能直接等同当前 test2 live；5.3.517 运行包/字节码需单独标注。
本轮：只读，无 test2 写入。

## 1. 结论先行

实体、字段、默认值、参照、枚举、事件、索引、字段集、实体规则、dataflow/deduction 不是一个“基础设置 JSON”。它们至少分属：

```text
Entity / Attribute / AttributeGroup / Index
CtpEnum / CtpEnumItem / UdcEnum / UdcEnumItem
ReferConfig / Relation metadata
Event / EventData / BusinessEvent listener
MicroFlow / EntityRule
DataFlow / DeductionRule / DeductionMap
Page / FunctionNode / Excel import-export
```

当前 `xiaozhua-agent` 没有实现这些设计态对象的完整写入执行器，也没有把它们统一成一个可自动搭建的 schema compiler。项目当前是只读证据、dry-run、deployment plan 主线；前面临时脚本直连平台不能反推项目已经具备这些能力。

## 2. 字段创建和属性校验

### 2.1 创建不是“写入一行”

`AttributeService.create(AttributeDto)` 在旧源码 `udc/udc-biz/src/main/java/com/seeyon/udc/entity/domain/service/AttributeService.java:298-332` 的实际顺序是：

1. 分配 id。
2. `initDefaultValueCaption(dto)`。
3. `changeErrorAttribute`。
4. `preCreateProcessor`。
5. DTO → Attribute 实体。
6. `checkAttributeIsLegal`。
7. `resolveExpression`。
8. 设置最大排序号。
9. `Names.checkAttrName`。
10. DAO 落库。
11. 发布 `AttributeCreateEvent`。
12. 写审计日志。

因此 HTTP 返回成功并不等于所有副作用都完成；字段创建包含校验、表达式处理、数据库落库、事件和日志。

### 2.2 名称、保留字、数据类型、索引长度

`checkAttributeIsLegal`：

- 字段编码先过 `checkName`，保留字检查见 `AttributeService.java:735-744`。
- 编码必须以字母开头，只允许字母、数字、下划线；长度上限 30，见 `735-753`。
- 创建 SERIAL 字段必须指定序列号规则，见 `617-635`。
- String 唯一字段长度超过 100 会被拒绝，见 `639-644`。
- 系统变量、国际化默认值和数据类型在创建前处理，见 `646-657`。
- 全实体字段合并后做数据库总长度检查，见 `671-705`、`763-769`。

这解释了前面 `orderNo` 被拒和 `uniqueness` 类型必须 Boolean 的现象，但项目目前没有把这些错误 oracle 固化为正式 contract validator。

### 2.3 多选人员不是普通字符串

`AttributeService.java:1846-1851` 表明：

```text
relationType == Many2OneAssociation
+ dataType == ENTITY 或 CTPENUM
+ multiSelect == true
→ maxLength 使用 ENTITY_MULTISELECT_LENGTH
```

因此人员多选至少需要：

```text
dataType=ENTITY
relationType=Many2OneAssociation
relationApp/relationEntity
multiSelect=true
```

真正的字段组件还要由 `DataTypeDefaultComponentEnum` 和前端组件 schema 决定，不能写一个未经注册的 `UserSelect` 控件名。

## 3. 默认值机制

### 3.1 字段静态默认值/表达式/系统变量是三种不同机制

`AttributeService.initDefaultValueCaption` 位于 `AttributeService.java:2380-2400`：

- `dataType=CTPENUM`：按枚举关系解析默认值显示文本。
- `defaultValueSystemVariable` 非空：解析 JSON，读取 `desc` 作为显示文本。
- `defaultValueExpressionDesignData` 非空：解析 `ExpressionDesignDataDto`，读取 `expressionTranslation`。
- 否则使用普通 `defaultValue` 作为 caption。

因此“默认值”至少需要区分：

```text
defaultValue
 defaultValueCaption
defaultValueExpressionDesignData
defaultValueExpressionRuntimeData
defaultValueSystemVariable
defaultValueIsChange
```

不能只给一个 `defaultValue` 字符串就宣称系统变量或表达式默认值已实现。

### 3.2 默认值表达式依赖元数据

`AttributeDefaultValueExprServiceImpl`：

- 参数类型为 `ATTR_DEFAULT_VALUE`，见 `expression/domain/service/AttributeDefaultValueExprServiceImpl.java:44-48`。
- 通过 `UdcMetaDataAppService`、`EntityService` 获取实体/字段元数据，见 `58-68`。
- 对枚举、Java enum、关联实体、1:1 子实体分别构造表达式 schema，见 `195-229`、`274-345`。

结论：默认值表达式不是页面字段的自由文本，而是依赖实体元数据、关联关系和表达式 schema 的设计态对象。`xiaozhua-agent` 当前没有实现这个 schema 构造器。

## 4. 实体加载、索引、字段集和实体规则标记

### 4.1 实体加载会组装字段与索引

`EntityService.selectEntityMapByAppId`：

- 查询应用实体。
- 加载实体和属性。
- `loadEntityHasOrderNo`。
- `loadEntityHasDefaultValueSystemVariable`。
- `loadEntityRule`。

见 `udc/udc-biz/src/main/java/com/seeyon/udc/entity/domain/service/EntityService.java:1245-1259`。

`loadEntityAndAttribute` 在 `1350-1376`：

- 查询实体下字段。
- 按 dataType 转换显示名。
- 按 entityId 分组。
- 通过 `indexService.selectByEntityAttributeMap` 加载索引。
- 构造父子实体/字段内存结构。

这说明索引是实体元数据装配的一部分，但不等同于字段集；字段集应从 AttributeGroup 关系单独读取。

### 4.2 字段集不是字段本身

`EntityService.selectByPrimaryEntityId` 在 `1306-1321`：

- 先按实体 id 查询 AttributeGroup。
- 从每个 group 的 `attributeDtoList` 汇总字段。
- 赋回 entity.attributes。

所以字段集的正确链路是：

```text
AttributeGroup → AttributeGroup.attributeDtoList → Attribute
```

不能只修改 `attribute_group_id` 后就认为页面/字段集 UI 一定正确；需要读回 AttributeGroup 及其字段列表。

### 4.3 实体规则标志来自 MicroFlow，不是属性默认值

`EntityService.loadEntityRule` 位于 `1404-1425`：

- `microFlowService.loadHasRuleEntityId(appId)` 返回按 `GroupTypeEnum` 分组的实体 id。
- `VALIDATE` → `hasValidateRule`。
- `DEFAULT_VALUE` → `hasDefaultValueRule`。
- `ASSIGN_VALUE` → `hasAssignValueRule`。
- 聚合根按子实体规则再设置生成标志。

因此实体规则页面不是字段 defaultValue 的别名，而是 microflow/entity-rule 体系。全租户某张 deduction 表没有数据，不能据此断言所有实体规则功能未启用；应先确认对应 GroupType、MicroFlow 表、控制器查询面和应用范围。

## 5. 事件

旧源码 `udc/udc-web/src/main/java/com/seeyon/udc/controller/EventController.java`：

- 类级 `/udc/event`，且要求 `UDC_APP_DESIGNER` 角色，见 `43-46`。
- `POST /udc/event` 创建纯事件，见 `55-58`。
- `POST /udc/event/create-with-data` 创建事件带事件数据，见 `61-64`。
- `POST /udc/event/update` 与 `update-with-data`，见 `67-76`。
- `POST /udc/event/list/business-event` 查询业务事件，见 `117-120`。
- `POST /udc/event/list/events` 查询实体事件/业务事件，见 `123-126`。

事件定义与动作绑定必须分开：

```text
EventController/EventAppService → 事件定义/事件数据
MicroFlow trigger BUSINESS_EVENT + messageInfo → 监听动作
```

所以 `udc_event` 表里建一行，不能说明它已经触发了哪个动作；必须检查监听微流程 dataSchema 和生成/运行链。

## 6. 枚举与枚举项

### 6.1 UDC 枚举 REST 契约

旧源码控制器：

- `UdcEnumController` 类级 `/udc/udc-enum`。
- 根 `POST /udc/udc-enum` 创建枚举。
- `POST /udc/udc-enum/update`、`delete`、`search`、`list`、`search/term`。
- `UdcEnumItemController` 类级 `/udc/udc-enum-item`。
- 根 `POST /udc/udc-enum-item` 创建枚举项。
- `POST .../update`、`operate-batch`、`delete`、`search`、`list`。
- `GET .../{enumId}/{level}` 按枚举和层级查询。
- `POST .../export` 和 `POST .../import` 已在 `UdcEnumItemController.java:126-143` 明确存在。

这说明导入导出确实有后端入口，但它是枚举项 Excel 导入导出，不等于订单实体列表导入导出。列表导入导出需要页面控件事件 + 对应实体 Excel 配置/模板链另行取证。

### 6.2 实体 Excel 模板与订单数据导入导出边界

实体设计态有独立的默认 Excel 模板入口：

```text
POST /udc/entity/preset/create-default-excel-template
```

Controller 证据：

```text
udc/udc-web/src/main/java/com/seeyon/udc/controller/EntityController.java:345-349
```

它调用 `EntityPresetAppService.createDefaultExcelTemplate(entityId)`；接口定义和实现见：

```text
udc/udc-biz/src/main/java/com/seeyon/udc/api/EntityPresetAppService.java:54-58
udc/udc-biz/src/main/java/com/seeyon/udc/appservice/EntityPresetAppServiceImpl.java:55-59
udc/udc-biz/src/main/java/com/seeyon/udc/entity/domain/service/EntityPresetService.java:302-339
```

`EntityPresetService` 取实体 fullName/appName/appId，构造 `ExcelExportTemplate4GridDto`，设置 `isImport=true`、`isCustom=false`、`isDefault=true`，再调用 `excelExportAppService.createExcelDataGridTemplate`。沿 Excel starter 继续核对后，默认模板落在 `ctp_excel_export_template`，由 `metadata_content` 与 `excel_head_info` 分别记录层级列元数据和拉平表头；见 `flow-excel-source-audit.md` 和机器清单 `flow-excel-contracts.json`。目标环境实际 database/schema 与订单模板记录仍未回读。

实体列表数据导入/导出的源模板来自旧源码树 `JAVA/2.9`；它与本地 reference artifact 的版本绑定仍需逐文件比对，不能仅凭目录名宣称为 5.3.517 实现：

```text
udc/udc-biz/src/main/resources/autocode/JAVA/2.9/templates/entity/pageEntityController.java.ftl:103-112
udc/udc-biz/src/main/resources/autocode/JAVA/2.9/templates/entity/pageEntityController.java.ftl:249-256
udc/udc-biz/src/main/resources/autocode/JAVA/2.9/templates/entity/pageEntityController2.java.ftl:115-127
```

根实体 controller 模板提供 `import`，调用 `ExcelImportAppService.importExcelData`；导出使用 `ExcelDynamicExportDto` 并走 `appService.exportExcel`。子实体/页面数据源模板按 `actionNames` 决定是否生成 `${baseUrl}/import`。这只是模板静态证据，未证明指定订单实体已生成对应 endpoint。

这与枚举项导入导出是两条链：

```text
枚举项：UdcEnumItemController → ExcelExportAppService/ExcelImportAppService
实体数据：生成的 pageEntityController → ExcelImportAppService + appService.exportExcel
```

枚举项 Controller 的证据为：`UdcEnumItemController.java:125-143`。

因此订单应用要验收导入导出，至少要分别回读：实体默认模板 id/配置、生成实体 Controller 路由、导入模板列映射、导出响应和真实订单数据；目前仅源码/模板结构已确认，订单目标应用生成物与运行态执行仍是 `UNVERIFIED`。

### 7.1 deduction 是独立对象，不是字段默认值

`DeductionCodeUtil.java:17-40`：

- 根据实体名生成 `DeductionConditionQuery<Entity>Service`。
- 根据实体名生成 `DeductionConditionUpdate<Entity>Service`。

`DeductionCodeUtil.java:45-80`：

- 识别根实体。
- 识别根实体的一对一子实体。
- 决定是否平铺一对一关系。

`DeductionCheckUtil.java:23-53`：

- 校验对象存在。
- 将图形定义中的 `id_<numeric>` 节点 id 转成实体 id。
- 校验底层 BaseResponse。

这些是 deduction 代码生成/条件处理辅助，不是普通页面规则，也不是 Attribute 默认值。

### 7.2 deduction 的保存和生命周期执行静态链

专门审计与机器清单已补充：`flow-excel-source-audit.md`、`flow-excel-contracts.json`。

Controller → AppService(@Transactional) → DeductionRuleService 的直接链已经核对，规则会保存到 `udc_deduction_rule`，关联算法/状态明细分别进 `udc_deduction_algorithm` / `udc_deduction_rule_detail`，图定义进 `udc_deduction_map`。生成器输出 BeforeCreate/BeforeUpdate/BeforeDelete 同步监听器，分别 DO、按新旧数据 UNDO/DO、删除时 UNDO；并使用来源 deductionInfo 追踪规则/算法关系。

这些都是旧源码静态证据；当前部署版本、目标订单应用 listener/service、真实目标值/事务回滚/业务日志回读仍为 UNVERIFIED。`CALL_DATA_FLOW` 只证实调用生单服务，不能视为直接调用扣减的公共入口。

## 8. 导入导出模板

已确认的静态链：

- 枚举项导入导出：`UdcEnumItemController.java:126-143`，依赖 `ExcelExportAppService` / `ExcelImportAppService`。
- 实体默认模板：`EntityController.java:345-349` → `EntityPresetAppService` → `EntityPresetService.java:302-339`，构造 `ExcelExportTemplate4GridDto` 并委托 `createExcelDataGridTemplate`。
- 实体数据导入/导出：生成模板 `pageEntityController.java.ftl:103-112,249-256` 和 `pageEntityController2.java.ftl:115-127`，分别调用 `ExcelImportAppService.importExcelData` 与 `appService.exportExcel`。

仍未验证：目标订单实体的模板物理记录与列映射、构建后实际 Controller 路由、导入文件业务效果、导出文件内容和运行态数据回读。因此订单应用的完整导入导出链仍是 `UNVERIFIED`，不能用枚举项接口代替。

## 9. 当前主线实现缺口

`xiaozhua-agent` 当前没有：

1. AttributeDto 级字段定义/默认值/关系/多选校验模型。
2. AttributeGroup/Index/Reference/Event/Enum/Deduction/DataFlow 独立对象模型。
3. 页面组件 schema 注册表读取器。
4. 页面 childById/dataSource/column/events 构造器和 validator。
5. MicroFlow dataSchema graph validator、节点输入输出检查和模板映射。
6. 页面规则与过滤方案的区分及各自 planner。
7. 页面按钮构建 Network 抓包与构建结果验证器。

因此下一步应先在仓库实现“只读协议模型 + validator + dry-run plan”，再讨论宿主执行器；不能先写 test2。

## 10. 证据等级和未知项

| 主题 | 结论 | 等级 |
|---|---|---|
| 字段创建顺序/校验/事件 | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| 默认值 caption/表达式类型 | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| 实体加载索引/规则标志 | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| 事件 REST 路由 | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| 枚举项 Excel import/export | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| deduction 命名/关系判断 | 源码可见 | VERIFIED_STATIC_SOURCE（旧源码树） |
| 当前 test2 运行包是否完全同源码 | 未完成版本绑定 | UNVERIFIED |
| 订单表单导入导出完整链 | 未完成 | UNVERIFIED |
| 生单/扣减业务节点完整执行链 | 未完成 | UNVERIFIED |
| 当前 xiaozhua-agent 已能执行上述写链 | 项目代码显示只读/方案 | FACT: NOT IMPLEMENTED |
