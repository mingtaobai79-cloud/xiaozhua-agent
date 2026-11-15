# 生单规则（DataFlow）REST 写链 —— 全链打通

> 领域：规则 → 生单规则（`udc/data-flow`）+ 映射规则（`udc/data-flow/mapping`）
> 状态：**生单规则 LIVE PASS / 映射规则 LIVE PASS**
> 证据：CFR 反编译（udc-dataflow / udc-starter-dataflow / udc-common 5.3.517）+ pod 真实堆栈 + DB 回读

## 1. 端点面

| 写 | 路径 | 说明 |
|---|---|---|
| W | `POST /udc/data-flow` | **新建生单规则 → `SingleResponse<Long>`** |
| W | `POST /udc/data-flow/update` | 更新生单规则 |
| W | `POST /udc/data-flow/delete` / `batch-delete` | 删除 |
| W | `POST /udc/data-flow/delete/content` | 图删节点/连线并保存（`DataFlowDeleteContentDto`） |
| W | `POST /udc/data-flow/mapping` | 新建映射规则（入参 `DataFlowMappingSaveDto`，出参 `DataFlowMappingResultDto`） |
| W | `POST /udc/data-flow/mapping/update` | 更新映射规则 |
| W | `POST /udc/data-flow/mapping/delete` | 删除映射规则 |
| | `GET /udc/data-flow/app/{appId}`、`GET /udc/data-flow/{id}` | 读生单规则 |
| | `POST /udc/data-flow/mapping/count`、`mapping/line/count` | 映射计数 |
| | `GET /udc/data-flow/mapping/{id}`、`POST /udc/data-flow/mapping/list` | 读映射 |
| | `POST /udc/data-flow/list/entity`、`search` | 实体树/查询 |

## 2. 生单规则 DTO 契约（CFR `udc-common-5.3.517`）

```jsonc
DataFlowDto {
  appId,
  caption*,        // @Length(1,50) @NotNull
  definition,      // 图定义 JSON（可为空串）
  description,     // @Length(max=255)
  state,           // UsageStateEnum，默认 'ON'
  creator, lastModifier   // 服务端按会话填充
}
```

**实测成功体**：
```json
{"appId":"8704025620829192834","caption":"小爪生单规则","description":"REST 实测生单规则",
 "state":"ON","definition":""}
→ content = "908877618948883045"
```
落库 `udc_data_flow`：本应用 **1 → 2 行**（`caption=1` 为既有原型，`caption=小爪生单规则` 为新建）。
表列：`id, app_id, caption, creator, definition, description, last_modifier, state, original_id`。

## 3. 映射规则 DTO（部分，来自 udc-common）

```jsonc
DataFlowMappingDto {
  appId, appName, sourceAppId, sourceAppName, dataFlowId, orderNo,
  state,                    // 默认 'ON'
  caption*,                 // @Length(1,50) @NotNull
  name*,                    // @Length(1,30) @NotNull
  sourceEntityId, sourceEntityFullName, targetEntityId, targetEntityFullName,
  description,              // @Length(max=255)
  triggerPoint,             // TriggerPointEnum
  bindEvent, eventId, eventEntityId
}
DataFlowEntityDto {  // 实体树节点
  name, tableName, fullName, dtoFullName, capFirstName, unCapFirstName, caption, appName,
  stereotype, category(默认 ENTITY), attributeDtoMap, extAttributeDtoMap,
  parentEntityId(默认 NULL_ID), parent, children, multiplicity(默认 ONE2MANY), orderNo
}
```

## 4. 映射规则：契约全解 + LIVE PASS

### 4.1 ★ 关键突破：缺失构件已取到

`POST /udc/data-flow/mapping` 的入参类型 `com.seeyon.udc.dataflow.dto.DataFlowMappingSaveDto`
**本地原缺**（`<MAVEN_REPO>` 全量搜索 0 命中；`udc-web-5.3.517.jar` 内 `dataflow` 包计数 = 0）。
**已从 Artifactory 取回**：`http://10.0.0.1/artifactory/libs-release/com/seeyon/udc-dataflow/5.3.517/udc-dataflow-5.3.517.jar`
（849,883 bytes，HTTP 200）。**这推翻了我上一条"本地不可得"的结论** —— 该构件在 Artifactory 存在且可直接拉。

### 4.2 契约（CFR 实测，拼齐）

```jsonc
// 顶层入参
DataFlowMappingSaveDto { String definition; DataFlowMappingDto dataFlowMappingDto; }

// 出参
DataFlowMappingResultDto { Long dataFlowMappingId; Integer affectCount; Integer mappingsCount; }

DataFlowMappingDto {
  appId, appName, sourceAppId*, sourceAppName, dataFlowId, orderNo, state,
  caption*(1-50), name*(1-30),
  sourceEntityId, sourceEntityFullName, targetEntityId, targetEntityFullName, description,
  triggerPoint*,                    // TriggerPointEnum: MANUALLY(0) | EVENT_SUBSCRIBE(1)
  bindEvent, eventId, eventEntityId, eventAppName, bindEventCaption, ruleInfo,
  creator, lastModifier, createTime, updateTime,
  mappingDetailDto*                 // ★ 不是顶层，是 DataFlowMappingDto 的字段
}

DataFlowMappingDetailDto {
  preConditionJson, eventFilterConditionJson, sourceEntitySearchConditionJson,
  rules: List<DataFlowMappingRuleDto>, preCondition, eventFilterCondition
}

DataFlowMappingRuleDto {
  operationType,           // DataFlowOperationTypeEnum: CREATE(0) | UPDATE(1) | CREATE_OR_UPDATE(2)
  keyAttribute: List<DataFlowMappingFieldDto>,
  pageId, pageFullName, pageCaption, pageParamsMapping,
  mobilePageId, mobilePageFullName, mobilePageCaption, mobileParamsMapping,
  autoProcess, entityMappingRelation: List<DataFlowEntityMappingRelationDto>,
  mappingArea: List<DataFlowMappingAreaDto>, listSchema,
  writeBackRuleList: List<DataFlowMappingWriteBackDto>
}

DataFlowMappingAreaDto {
  entityId, entityFullName, frontendConditionList, checkRuleJson, ruleTips,
  updateConditionList, mappingRow: List<DataFlowMappingRowDto>, conditionJson, uuid,
  checkRule, targetEntity, targetEntityName4Class, dynamicMappingRow, dynamicMappingIdMapping,
  groupMappingRow
}

DataFlowMappingFieldDto {
  entityId, entityFullName, attributeId, attributeFullName, formulaJson, fixedValue,
  formula, entityName, attributeName, fieldJavaType, attributeDto, entityDto, ctpEnumHostAppName
}
```

### 4.3 ★ 全链已打通（校验错误链 = 复现顺序）

```
dataFlowMappingDto must not be null
 → mappingDetailDto must not be null（放顶层无效 → 它是 DataFlowMappingDto 的字段）
 → sourceAppId must not be null
 → triggerPoint must not be null
 → appId must not be null        ← 真因：DataFlowMappingSaveDto extends DataFlowDto，顶层要带 appId
 → BOOT_3000 (message=null)      ← definition="" → NPE @ handleGraphDefinition(:227)，需含 lines 的图 JSON
 → BOOT_3000 "Index: 0, Size: 0" ← rules=[] → dataProcess(:1173) 直接 getRules().get(0)
 → UDC_DATAFLOW_0003 entityMappingRelation cant be null!
 → UDC_DATAFLOW_0060 来源实体列表方案 scheme 参数错误（MANUALLY 时 listSchema 必填）
 → ✅ BOOT_0000 SUCCESS
```

**LIVE 证据**：
```jsonc
POST /service/udc/data-flow/mapping
→ {"status":0,"code":"BOOT_0000","data":{"content":{
     "validate":true,"dataFlowMappingId":"7702563982566312936","affectCount":1,"mappingsCount":1}}}
落库 udc_data_flow_mapping id=7702563982566312936（trigger_point=0 MANUALLY, state=0）
udc_data_flow_mapping 全库 56 行
```

### 4.4 两个 NPE/IOOBE 的真实堆栈（pod 日志）

```
java.lang.NullPointerException
  at com.seeyon.udc.dataflow.domain.service.DataFlowMappingDesignService.handleGraphDefinition(:227)
  at ...DataFlowMappingDesignService.create(:177)

java.lang.IndexOutOfBoundsException: Index: 0, Size: 0
  at ...DataFlowMappingDesignService.dataProcess(:1173)
  at ...DataFlowMappingDesignService.create(:267) → create(:180)
```
`handleGraphDefinition`：`JsonUtils.toMap(definition)` → 空串得 null → `graphMap.get("lines")` 抛 NPE。
`dataProcess`：直接 `mappingDetailDto.getRules().get(0)`。

### 4.5 `listSchema`（MANUALLY 必填）契约

`com.seeyon.udc.dataflow.dto.DataFlowListSchemaDto`：
```jsonc
{"entities":["<entityId 字符串，列实体白名单>"],
 "columns":[{"id":<属性id>,"name":"expText","caption":"...","dataType":"STRING",
             "entityId":<实体id>,"mobile":true,"splitField":false,"namePath":"..."}],
 "whereCond":[],"orders":[{"id":..,"property":"..","direction":"ASC"}],
 "search":[{"id":..,"name":"..","dataType":"..","quick":true,"entityId":..,"placeholder":[]}],
 "splitField":null}
```
校验点：`column.id`=**属性 id**；列实体须在 `entities`（0076）；`entities` 内 id 可解析（0077）；同一系统（0066）；与根实体串接（0067）；命中区域（0064）。

### 4.6 `definition` 图 JSON 真实形状

取自库内既有 `udc_data_flow.definition`（`{lines, nodes, transform}`）：
```jsonc
{"lines":[{"id":"<startId>-<endId>","startId":"id_x","endId":"id_y","text":1,
           "startDirection":"right","endDirection":"left","x1":..,"y1":..,"x2":..,"y2":..,
           "circleX":..,"circleY":..,"path":"M ..,.. L ..,.."}],
 "nodes":[{"id":"id_x","title":"<实体名>","appId":"<appId>","appName":"<appName>",
           "fullName":"<entityFullName>","x":..,"y":..,
           "style":{"width":180,"height":50,"left":..,"top":..},"direction":""}],
 "transform":{"x":14.7,"y":..,"scale":1}}
```
`line.id` 必须等于 `DataFlowUtil.getGraphDefinitionLinesKey(mappingDto)`，否则 `text`(序数) 不回填。

### 4.6.1 ★ 节点 id 必须是实体 id（否则 UDC_CE_DATA_FLOW_05005）

`node.id` = `"id_" + <实体 id>`（真实样本 `id_-4724619979276168735` = 实体 `qfkmxb` 的 id）。
**用伪造 id（如 `id_-7000000000000000001`）会被检测器判为"实体不存在"**：

```
UDC_CE_DATA_FLOW_05005 | Data flow [小爪生单规则]
  element: 小爪实验实体950795V2
  message: Entities in the data flow diagram no longer exist
  route: {"type":"node","id":"908877618948883045","address":"id_-7000000000000000002"}
```
检测器按 `node.id` 去 `udc_entity` 反查，查不到即 ERROR × 节点数。
**修法**：节点 id 改为各实体 id，`POST /udc/data-flow/update` 重存 definition → 05005 归零（LIVE VERIFIED）。

### 4.7 检测面（复核口径）

检测读必须走 GraphQL 且带 `query`，否则报 `Invalid Syntax '<EOF>'`：
```
POST /service/udc/graphql?udcApplicationSearchDetectionPost
{query:"query graphqlLoader ($params0: udcApplicationSearchDetectionPostInputBody) {
   data0: udcApplicationSearchDetectionPost(body: $params0) { code data { content } message status } }",
 variables:{params0:{appId}}}
```
触发 `POST /service/udc/application/do/detection`（**类级映射 `udc/application`**，早期误用 `/udc/do/detection` → 404）；
轮询 `do/detection-state` 至非 `EXECUTING` 再读。
**本领域本轮后：9 WARN / 0 ERROR。**

## 5. 枚举真值（实测）

| 枚举 | 值 |
|---|---|
| `TriggerPointEnum` | `MANUALLY(0)` / `EVENT_SUBSCRIBE(1)` |
| `DataFlowOperationTypeEnum` | `CREATE(0)` / `UPDATE(1)` / `CREATE_OR_UPDATE(2)` |
| `MappingModeCategoryEnum` | `FIELD(0)` / `FIXED_VALUE(1)` / `FORMULA(2)` / `GROUPING_FUNCTION(3)` |
| `MappingMode.name` | `FieldCopy` / `FixedValue` / `Formula` / …（`MappingModes.get()`） |
| `DataFlowMappingEntityInfoDto` | `{Long entityId; String entityFullName;}`（**无 appId**） |

## 6. 构件获取通道（重要）

本领域 DTO **不在** udc-web / udc-common，在 **`udc-dataflow`**（原先本地缺）：
```
http://10.0.0.1/artifactory/libs-release/com/seeyon/udc-dataflow/5.3.517/udc-dataflow-5.3.517.jar
→ HTTP 200, 849,883 bytes（含 com/seeyon/udc/dataflow/dto/*）
```
`DataFlowMappingDesignAppService` 在 `udc-dataflow`；`DataFlowMappingAppServiceImpl` 在 `udc-starter-dataflow`（AppService 层，**无** create 校验，别在它身上找）。
**教训：缺类先探 Artifactory 直连，不要判"本地不可得"。**

## 7. 边界（未做）

- 规则**执行语义**未验（只写设计态定义；未触发一次真实生单）。
- `EVENT_SUBSCRIBE` 触发分支（`dataCheck4EventSubscribe` / `dataCheck4CycleDetection`）未走通。
- `writeBackRuleList`（回写规则）、`keyAttribute`（更新键）、`pageId`/`autoProcess`（0071）未验。
- `mappingMode` 仅用 `FieldCopy`；`FixedValue`/`Formula`/分组函数未验。

## 8. 复现

`scratch/` 内联脚本（见上 LIVE 证据体）；错误链按 §4.3 顺序逐层补齐即可复现。
