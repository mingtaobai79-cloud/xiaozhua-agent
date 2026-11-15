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
**本地原缺**（`D:/repo/CHIT` 全量搜索 0 命中；`udc-web-5.3.517.jar` 内 `dataflow` 包计数 = 0）。
**已从 Artifactory 取回**：`http://172.28.24.205/artifactory/libs-release/com/seeyon/udc-dataflow/5.3.517/udc-dataflow-5.3.517.jar`
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
http://172.28.24.205/artifactory/libs-release/com/seeyon/udc-dataflow/5.3.517/udc-dataflow-5.3.517.jar
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

## 9. ★ 生单规则画布 UI 全链实测（2026-11-15，LIVE）

> 环境：本应用 `appId=163126498398523384`。创建规则 id `4683705788777319367`。
> 通道：CDP 连真实 Edge（9222），复用已有登录态，cookie 不出浏览器。

### 9.1 设计态入口（不是门户特殊页）

| | URL |
|---|---|
| 列表 | `/main/child-frame/udc/app-design/app-basic-info?appId=<appId>` → 左栏「规则」→ tab「生单规则」 |
| 创建弹窗 | 同页，点「暂无结果 / 请创建生单规则」 |
| 画布 | `/main/child-frame/udc/app-design/rule/dataflow/graph/<规则id>?appId=<appId>` |
| 映射配置 | 画布连线中点 `+` 圆圈 → 右侧抽屉 |

★ 门户特殊页 `/main/portal/<appName>/_dataflow` 也能打开，但那是**运行态**入口，
设计态走 `app-design/rule/dataflow/**`。

### 9.2 创建弹窗只有两个字段

「名称」`input` + 「备注」`textarea`，无其它必填。提交走：

```jsonc
// POST /service/udc/graphql?udcDataFlowPost
{"query":"mutation example ($body: udcDataFlowPostInputBody) {...}",
 "variables":{"body":{"appId":"<appId>","caption":"<名称>","description":"<备注>","definition":null,"state":"ON"}}}
→ BOOT_0000，落库后 definition=null，随后画布页自动加载
```

### 9.3 列表接口 body（页面自己发的）

```jsonc
// POST /service/udc/graphql?udcDataFlowAppAppGet
{"variables":{"path":{"appId":"<appId>"}}}
// 返回 content[] 只有 caption + id
```

### 9.4 ★★ 加节点：树节点不是拖 HTML5 drag，是 antd Tree 的 onDragEnd

页面上**没有任何「加号/右键/双击」**能往画布加实体。真实链路在
`src_pages_app-design_rule_dataflow_relation-graph_index_tsx.<hash>.js`：

```js
i().createElement(v.A,{drag:function(e){
  let{event:t,node:a}=e;  if(!x.current) return;
  let{getData:l,addSymbol:n,graphWrapper:i}=x.current,
      {nodes:r,transform:o}=l(), {left:d,top:s}=i.current.getBoundingClientRect();
  if(t.pageX<d) return;                                  // ★ 必须落在画布左侧边界内
  if(["standard","bill","archive"].includes(a.id))        // ★ 分组节点不能拖
      return c.message.warning("分类不能绘制！");
  let u=r.findIndex(e=>e.id==="id_".concat(a.id));
  if(-1!==u) return c.message.warning("图中已存在该实体！");
  let m=o.k||1,
      p={x:(t.pageX-o.x-d)/m, y:(t.pageY-o.y-s)/m},
      v={...p,id:a.key,title:a.title,direction:a.direction,
         appId:a.appId,appName:a.appName,fullName:a.fullName};
  n(v,p)                                                 // addSymbol
}})
```

实体树 `draggable:{icon:!1,nodeDraggable:e=>!!e.node}`，`onDragEnd` 把
`{event, node}` 交给上面这个 `drag`。**`event.pageX` 必须 ≥ 画布 `left`**，
否则静默 return（这就是"拖了没反应"的唯一原因）。

★ CDP 的 `Input.dispatchMouseEvent` 触发不了 antd 的 HTML5 dragstart，
合成 `DragEvent` 也被 React 拦下。**可靠做法是直接调用这个 `drag` 回调**：

```js
// node 取自实体树 treeData 的节点（含 id/caption/fullName/appName）
window.__drag({event:{pageX:1200,pageY:560}, node:{id:"<实体id>", key:"<实体id>",
  title:"<实体caption>", direction:"", appId:"<appId>", appName:"<appName>",
  fullName:"com.seeyon.<appName>.domain.entity.<Entity>"}})
```

实测：调用后 `svg g.nodeBox` 从 0 变 1，节点 `<rect id="id_<实体id>">` 立即渲染。

### 9.5 连线：拖节点上出现的 drag-point 圆圈

鼠标悬停节点 → `.controls` 由 `none` 变 `block` → 四向 `.drag-point`
（left/top/right/bottom）。从源节点 `direction=right` 的点拖到目标节点即可。
用 `Input.dispatchMouseEvent` 的 pressed → moved×N → released 就work（这条路不需要 HTML5 drag）。

连线 id 恒为 `id_<源实体id>-id_<目标实体id>`。

### 9.6 保存：definition 真实形状

```jsonc
// POST /service/udc/graphql?udcDataFlowUpdatePost
{"variables":{"body":{
  "appId":"<appId>","id":"<规则id>","caption":"<名称>",
  "definition":"{\"nodes\":[...],\"transform\":{\"x\":0,\"y\":0,\"k\":1},\"lines\":[...]}"}}}
→ BOOT_0000 content=1
```

`definition` 是**字符串**，解开来：

```jsonc
{
 "nodes":[{"x":624,"y":476,"id":"id_<实体id>","title":"<实体caption>",
           "style":{"width":180,"height":50,"left":534,"top":451},
           "direction":"","appId":"<appId>","appName":"<appName>",
           "fullName":"com.seeyon.<appName>.domain.entity.<Entity>"}],
 "transform":{"x":0,"y":0,"k":1},
 "lines":[{"id":"id_<源>-id_<目标>",
           "startDirection":"right","endDirection":"bottom",
           "x1":624,"y1":476,"x2":1124,"y2":476,
           "circleX":934,"circleY":503.5,
           "path":"M 714,476 L 744,476 L 934,476 L 934,531 L 1124,531 L 1124,501",
           "startId":"id_<源>","endId":"id_<目标>"}]
}
```

★ `transform` 的缩放键是 **`k`**（不是 `scale`）。
★ `node.id` 必须 `id_<真实实体id>`，否则触发 `UDC_CE_DATA_FLOW_05005`
（见 §4.6.1，本轮再次印证）。
★ 空图保存会被前端拦：`cannot save empty` → `c.message.warning("不能保存空图！")`。

### 9.7 映射配置抽屉：字段级 UI 契约

点连线中点 `+`（`.pathCircle`）打开右侧抽屉，真实控件 id 如下：

| 控件 id | 标签 | 状态 |
|---|---|---|
| `sourceEntityId` | 来源实体 | **disabled**（来自画布节点） |
| `targetEntityId` | 目标实体 | **disabled**（来自画布节点） |
| `pageId` | 目标详情页面（PC） | 可选，**本轮 options=[]** |
| `mobilePageId` | 目标详情页面（移动） | 可选，options=[] |
| `mappingArea_0_entityId` | 实体映射规则 | **disabled:!0 硬编码** |
| `mappingArea_0_mappingRow_0_target` | 「目标实体」字段 | disabled |
| `mappingArea_0_mappingRow_0_mappingMode` | 映射规则 | disabled |
| `mappingArea_0_mappingRow_0_source` | 来源实体字段 | disabled |

初始化接口：

```jsonc
// POST /service/udc/graphql?udcDataFlowMappingInitDataPost
{"variables":{"body":{"dataFlowId":"<规则id>","appId":"<appId>"}}}
// 返回 content: ctpEnumItemMap / javaEnumItemMap / mappingModeMap /
//              sourceEntityList[] / targetEntityList[] / pageList[]
```

★ 少传 `sourceEntity` 会报 `BOOT_1001 来源实体参数 不能为null` —— 它要的是
实体对象而非裸 id（`appId`+`dataFlowId` 也不够）。**页面真实 variables 形态未取到**
（CDP Network 在本窗口只对首次加载有效，重开抽屉抓不到），标 UNVERIFIED。

### 9.8 ★★ 打通：映射规则提交成功（关键前置已确认）

**卡点曾以为是死锁，实际是缺一个动作**。表单填完名称/编码后点「提交」，报：

```
实体映射规则未配置         ← 前端拦截，零网络请求
```

源码依据：提交按钮第一件事就是检查 `entityMappingRelation`：

```js
onClick:()=>{ let t=H.getFieldsValue();
  if(!t.entityMappingRelation?.length){ s.message.error("实体映射规则未配置"); return }
  H.submit() }
```

**解锁方式（实测）**：不必先建页面。只要**目标实体有字段**，
把「映射类型/操作类型」区里的下拉动一下（本轮是切 tab 触发重渲染），
`entityMappingRelation` 就会按画布连线自动生成：

```jsonc
// 自动生成，无需手填
[{"validate":true,
  "targetEntity":{"validate":true,"entityId":"<目标实体id>","entityFullName":"...MigrationCheckpoint"},
  "sourceEntity":[{"validate":true,"entityId":"<源实体id>","entityFullName":"...AeProbeEntity"}]}]
```

随后 `mappingArea[0].entityId` 自动填成目标实体，`mappingRow` 三件套解锁：

| 控件 | 解锁条件 |
|---|---|
| `mappingArea_0_entityId` | `entityMappingRelation` 有值 → 自动填，**恒 disabled**（正常） |
| `mappingArea_0_mappingRow_0_target` | 上一项有值 → 解锁 |
| `mappingArea_0_mappingRow_0_mappingMode` | 选中 target 后自动填 `值拷贝(FieldCopy)` |
| `mappingArea_0_mappingRow_0_source` | target + mode 有值后解锁 |

★ **`mappingMode` 是自动填的**，不要手选；手选会破坏默认推导。

### 9.9 提交前还有两个硬校验（都会拦在前端）

1. **编码格式**：`^[A-Za-z][A-Za-z0-9]*$` —— 只能字母数字且字母开头。
   `probe_to_checkpoint` 被拒（下划线不允许），改 `probeToCheckpoint` 通过。
2. **来源实体列表方案必填**（`MANUALLY` 触发时）：
   「来源实体列表方案 → 点击设置内容」打开 Transfer 弹窗，
   左「可选字段」是 antd Tree，**每个字段节点有 `.ant-tree-checkbox`**，
   勾选后点中间 `→`（`.ant-transfer-operation button[0]`）移到右「已选字段」，
   再「确定」。至少选 1 个字段，否则一直报 `请设置来源实体列表方案`。
   成功后抽屉里显示 `已设置`。

★ 注意：该 Transfer 的左侧列表是虚拟滚动，`items:0` 也会正常渲染树；
用 `.ant-transfer-list .ant-tree-treenode` 定位，别用 `.ant-transfer-list-content-item`。

### 9.10 ★ 提交成功：`udcDataFlowMappingPost` 全链 LIVE

```jsonc
// POST /service/udc/graphql?udcDataFlowMappingPost
// 注意：variable 名是 $body，但**顶层没有 dataFlowMappingDto**——
// 页面把 DataFlowMappingDto 的字段直接摊在 body 上
{"variables":{"body":{
  "appId":"<appId>",
  "caption":"小爪生单规则V1",          // ← 用的是**规则名**，不是映射名
  "definition":"<画布 JSON 字符串>",
  "dataFlowMappingDto":{...},          // ← 页面实际发送形态（见下）
  ...
}}}
→ {"code":"BOOT_0000","data":{"content":{
     "affectCount":1, "dataFlowMappingId":"2494859495235864858", "mappingsCount":1}}}
```

页面提示：**新增生单规则成功！**

### 9.11 回读逐字段验收（`udcDataFlowMappingGet`）

```jsonc
{"id":"2494859495235864858","caption":"probe to checkpoint","name":"probetocheckpoint",
 "triggerPoint":"MANUALLY","publishState":"UNPUBLISH",
 "src":"4308140192425942217","tgt":"3748812225302252072",
 "rule":[{"opType":"CREATE","pageId":null,
   "rel":[{"validate":true,
     "targetEntity":{"entityId":"3748812225302252072",
       "entityFullName":"com.seeyon.<app>.domain.entity.MigrationCheckpoint"},
     "sourceEntity":[{"entityId":"4308140192425942217",
       "entityFullName":"com.seeyon.<app>.domain.entity.AeProbeEntity"}]}],
   "areas":[{"entityId":"3748812225302252072",
     "rows":[{"mode":"FieldCopy",
       "src":"com.seeyon.<app>.domain.entity.AeProbeEntity.probeName",
       "tgt":"com.seeyon.<app>.domain.entity.MigrationCheckpoint.taskId"}]}]}]}
```

**逐项对齐 UI 输入**：

| UI 上填的 | 回读到的 | 一致 |
|---|---|---|
| 显示名称 `probe to checkpoint` | `caption` | ✅ |
| 编码 `probeToCheckpoint` | `name` | ✅（自动小写化） |
| 触发方式 手工触发 | `triggerPoint=MANUALLY` | ✅ |
| 操作类型 新建数据 | `operationType=CREATE` | ✅ |
| 目标字段 `任务标识【文本】` | `target.attributeFullName=...taskId` | ✅ |
| 映射规则 值拷贝 | `mappingMode=FieldCopy` | ✅ |
| 来源字段 `【接口验证实体】验证名称` | `source.attributeFullName=...probeName` | ✅ |
| 来源实体列表方案（选 ID + 验证金额） | `listSchema` 有值（方案 `已设置`） | ✅ |

★ 页面详情 `pageId=null` 是**允许的**（手工触发 + 无页面也能存），
之前的"必须有页面"是我的误判，已在 9.8 纠正。

### 9.12 UI 端验收

```
画布        2 节点 + 1 连线
连线圆圈    "+" → "1"        ← 映射规则已挂上
抽屉        已设置（来源实体列表方案）
应用检查    0 阻断 / 0 严重 / 1 警告（旧微流程 04003，与本规则无关）
红字        无
```

### 9.12a ★★★ 画布真实机制（推翻此前所有猜测）

此前我用「直接调 React `onDragEnd`」加节点、「手写 definition.lines 再 Update」连线。
两者都是**伪造**：前者的入参是我编的 `{event,node}` 形状，后者根本不经过页面逻辑。
本轮从 bundle 里读到真实实现（`webpackChunkudc` 模块 `87235`，67070 chars），
画布是 **D3，不是 React**。

#### 加节点：是真的 HTML5 drag，不是 onClick

树节点 `.ant-tree-treenode[draggable=true]` 的 `onDragEnd` 由 antd Tree 提供，
回调签名是 **`onDragEnd(antdEvent)` 一个参数**，`node` 从 antd 的 `info` 里取。
★ 传 `{event,node}` 会报 `t.stopPropagation is not a function` —— 因为第一个参数
就是原生 event，不是包装对象。这是本轮的实测报错，可作为形状判据。

回调内部有硬门槛：

```js
if(t.pageX < graphWrapper.left) return;   // ★ 落在画布左侧区域就静默 return
```

`pageX` 必须落在画布内，否则**不报错、不提示、什么都不发生**。
用 CDP `dispatchMouseEvent` 试过：触发不了 dragstart（React 合成事件拦），
`pageX` 取不到 —— 所以节点只能由页面自己的 drag 完成，或直接调那个回调。

#### 连线：D3 drag，`drag-point` 是 SVG circle

```js
// .drag-point 上的绑定（ec.A() 是 d3-drag）
selectAll('.drag-point').call(
  d3.drag()
   .on('start', function(){ ...记录 movingSelectLine... })
   .on('drag',  function(t){ I({x:t.x,y:t.y},{...node,direction}) })  // 画虚线
   .on('end',   function(t){ T({x:t.x,y:t.y},{...node,direction}) })  // 落线
)
```

`T` 是落线函数（真实实现截取）：

```js
T = (t, e) => {
  d.current.tempId = null;
  let n = [...nodes], r = eA(t.x, t.y, n);        // 命中检测：找落点节点
  d3.select('#l_' + e.id).remove();                // 删虚线
  let i = `${e.id}-${r.targetId}`;                 // ★ 线 id = 起点id-终点id
  let o = d.current.lines.findIndex(x => x.id === i);
  function c(){
    let t = eg({x:e.x,y:e.y}, {x:r.x,y:r.y}, e.direction, r.direction);  // 计算折线
    let {pathData:n, middleX:o, middleY:a} = ew(t, e.id, r.targetId);
    z(n, i);                        // 画 path
    S({x:o,y:a}, i);                // 画圆圈（text 默认 "+"）
    d.current.lines.push({id:i, startDirection:e.direction, endDirection:r.direction,
      x1:e.x,y1:e.y,x2:r.x,y2:r.y, circleX:o,circleY:a, path:n,
      startId:e.id, endId:r.targetId});
    g({model:'div', id:''});        // 触发重渲染
  }
  // ★ 三道闸：同节点自连、同方向、已存在 都不建线
  e.id===r.targetId && e.direction===r.direction
  || e.id===r.targetId && e.direction===r.direction
  || r.exists && -1===o && (a ? a(e,r).then(()=>{c()}) : c());
}
```

**要点**
- 线 id 格式：`<startNodeId>-<endNodeId>`，节点 id 形如 `id_<实体id>`
- 圆圈 `text` 初值 `"+"`；有映射规则后由 `S({x,y}, id, o.text)` 写成 `1`
- `d.current.lines` 是**内存真状态**，保存时直接 `JSON.stringify({lines,nodes,transform})`

#### 我踩过的三个坑（都是"看起来成功其实没生效"）

1. **合成 DragEvent 被 React 拦** → 节点加不上，但页面不报错
2. **CDP dispatchMouseEvent 走不完 d3-drag** → 虚线不出现，`T` 不触发
3. **手写 `definition.lines` 再 Update 返回 `BOOT_0000 content=1`** →
   接口成功、画布也显示线，但那条线是死的：它跳过了 `T` 里的
   `eA` 命中检测和 `d.current.lines` 状态注入，映射抽屉点开 `pageId` 仍为空。

**判据**：真正的线，保存时页面自己发出的 `definition` 里 `lines[].path`
是一串 `M x,y L x,y ...`（由 `ew` 梯度算出），且 `circleX/circleY` 落在两节点连线中点。

#### 本轮 LIVE 证据

```
g.node = 2
path#id_4308140192425942217-id_3748812225302252072  d="M 247,330 L 277,330 L 435.5,330 L 594,330 L 624,330"
.pathCircle = 1，text 由 "+" 变 "1"
保存请求 definition.lines = [{id:"id_...-id_...", startId, endId,
  startDirection:"right", endDirection:"left",
  x1:157,y1:330,x2:714,y2:330, circleX:435.5,circleY:330,
  path:"M 247,330 L 277,330 L 435.5,330 L 594,330 L 624,330"}]
udcDataFlowUpdatePost → BOOT_0000 content=1
```

### 9.12g ★★★★ 映射核心：pageParamsMapping 与它的前置条件

用户判定「生单没有通，你映射最核心都没写」。判对了。此前我只做到
「规则能存、圆圈显示 1」，从没检查过**页面入参映射**——而那才是生单
真正执行时把来源数据灌进目标详情页的通道。

#### 一、映射核心不是字段映射，是 pageParamsMapping

字段映射（`mappingArea.mappingRow`）解决「哪个字段给哪个字段」。
`pageParamsMapping` 解决「打开目标详情页时，5 个页面入参各填什么表达式」。
后者缺失，规则存得下、圆圈显示 1，但**生单执行时详情页拿不到 id，
打不开单据**。

真实结构（`rules[0].pageParamsMapping`，JSON 字符串）：

```json
[
 {"id":"preset_id","code":"id","label":"ID","dataType":"STRING",
  "required":true,"isAttribute":true,
  "attrCmptProps":{"businessProps":{"type":"CONSTANT","disabled":true,
                                    "placeholder":"系统默认"}},
  "expressionValue":[]},

 {"id":"GE_OPEN_MODE","code":"pageOpenMode","label":"页面打开模式",
  "dataType":"ENUM","required":true,
  "attrCmptProps":{"businessProps":{"type":"CONSTANT",
     "enumInfo":{"id":"PAGE_OPEN_MODE","caption":"页面打开模式",
                 "appId":"1057666928175434968"},
     "treeData":[{"label":"编辑","value":"edit"},
                 {"label":"查看","value":"view"}]}},
  "expressionValue":[]},

 {"id":"t_templateId","code":"templateId","label":"流程模板ID",
  "dataType":"STRING","required":false,
  "attrCmptProps":{"businessProps":{"type":"CONSTANT"}},"expressionValue":[]},

 {"id":"set_affairId","code":"affairId","label":"事项ID",
  "dataType":"STRING","required":false,...},
 {"id":"reset_caseId","code":"caseId","label":"流程实例ID",
  "dataType":"ENTITY","required":false,...}
]
```

★ 五个入参是**平台预设**，来自目标详情页的 `inParams`，不是业务字段。

#### 二、前置条件链：pageInfoList 必须有值

`pageParamsMapping` 只能从「已选页面」的 `inParams` 生成。
而页面下拉的选项源是 `udcDataFlowMappingInitDataPost` 返回的 `pageInfoList`。

```js
// 前端只做一件事：拿 pageInfoList 里这个页面的 inParams 铺开
inParams = pageInfoList.find(p => p.id === pageId).inParams
```

**实测：目标实体没有 DETAIL 页 → pageInfoList = [] → 下拉点不开 → pageId 只能 null。**

本轮的完整证据链：

```
目标实体 = 迁移断点（MigrationCheckpoint）
应用页面清单里，迁移断点只有 SEARCH_LIST（qyddListPage）
             接口验证实体有 SEARCH_LIST + DETAIL

InitDataPost 返回 pageInfoList = 0     ← 下拉"暂无数据"
     ↓ 用"实体→生成页面"给迁移断点补详情页
InitDataPost 返回 pageInfoList = 2
  -4925615763369467224  迁移断点详情页  MOBILE
   2037509287667995707  迁移断点详情页  PC
     ↓
抽屉里「目标详情页面（PC）」自动填「迁移断点详情页」
pageId = 2037509287667995707 / mobilePageId = -4925615763369467224
```

#### 三、InitDataPost 的真实入参（不是 entityId）

我此前按 `sourceEntityId/targetEntityId` 传，一直报
`BOOT_1001 来源实体参数 不能为null`。真实形状是**按 fullName 传**：

```json
{"body":{
  "sourceEntity":{"appId":"...","appName":"datamigration...",
    "entityFullName":"com.seeyon.datamigration....domain.entity.AeProbeEntity"},
  "targetEntity":{"appId":"...","appName":"datamigration...",
    "entityFullName":"com.seeyon.datamigration....domain.entity.MigrationCheckpoint"}}}
```

#### 四、pageInfoList[].inParams 是 JSON **字符串**，不是数组

```js
typeof p.inParams === 'string'   // ★ 必须 JSON.parse
JSON.parse(p.inParams).length === 5
```

直接 `p.inParams[0]` 拿到的是字符 `"["`，`p.inParams.length` 是 1574
（字符串长度）。这是本轮踩到的坑，表现为「读出来全是空」。

#### 五、提交时 pageId 埋在双层 mappingDetailDto 里

```js
body.mappingDetailDto                    // 外层：规则基本信息
  .mappingDetailDto.rules[0]             // ★ 内层：真正的规则
    .pageId / .mobilePageId
    .pageParamsMapping                   // JSON 字符串
    .pageFullName                        // 注意：这里是 1183802094923760407
```

我第一次读 `body.mappingDetailDto.rules[0]` 得到 undefined，误判「没保存」。
实际是嵌套两层。

#### 六、前端校验：不填显示名称/编码 + 列表方案，提交会被拦

```
提示「配置未完成或有误，请检查！」
  → .ant-form-item-has-error 命中：显示名称、编码
  → 提示「请设置来源实体方案」
  → 补 显示名称/编码 + 来源实体列表方案(勾 ID/验证名称/验证金额 → 右移 → 确定)
  → 「修改生单规则成功！」
```

#### 七、本轮 LIVE 全链回读（udcDataFlowMappingGet）

```
caption       接口验证→迁移断点
name          jkyzqydd
triggerPoint  MANUALLY
pageId        2037509287667995707
mobilePageId  -4925615763369467224
paramCount    5
required      ["id","pageOpenMode"]
openMode      expressionValue=[{type:"CONSTANT",desc:"编辑",value:"edit"}]
              treeData 存在（edit/view 可选）
mode          FieldCopy
src           probeName  →  tgt  taskId
```

#### 八、剩余 UNVERIFIED

生单真正跑一次需要在「测试」里构建发布（预估 4分44秒）。
本轮只做到规则完整落库 + 全部 UI 回读一致，**未执行真实生单**。
### 9.12h ★★★★★ 生单规则画布完整解剖（先理解，不写代码）

用户要求：「先理解这个画布他是做什么的，他能怎么画，每个功能位置对应什么细节」。
本节只做机制说明，不含操作脚本。

#### 一、画布是什么

**实体关系图（Entity Relation Graph）**，不是流程图、不是画布编排器。
它表达的是：**「哪些实体的数据，经由哪条线，流进哪个实体」**。

- 一个节点 = 一个实体（`<appId>.<entityFullName>`）
- 一条线 = 一条生单映射规则（`udcDataFlowMapping`）
- 线上的圆圈 = 该规则下的**字段映射条数**（`+` 表示还没建规则）
- 环状连线是正常的：本轮实测存在 A→B→C→A 三元环

它解决「数据从哪来、到哪去、经谁催生」，**不解决**「字段怎么一一对应」
——后者在点圆圈弹出的映射抽屉里。

#### 二、页面骨架（实测坐标，1707×825 视口）

```
┌─ 顶部 tab：应用 实体 菜单 规则 流程 BI 栏目 设置 角色
├─ 左侧 tab：规则 → 微流程 / 生单规则 / 扣减规则
├─ 左栏 260px  (x=56)   ：规则列表 + 实体树（可拖）
└─ 右区 1391px (x=316)
   ├─ header 48px  ：图标 + 规则名（可改名）+ 保存
   └─ main  709px
      ├─ 实体树面板 260px (x=316)：分组"标准"下的全部实体，draggable
      └─ 画布 1131px (x=576)
         ├─ 网格底纹 .biz-udc-graph-grid
         └─ SVG，内含 4 层（顺序即 z-index）：
            g.nodeBox     节点
            g.lineBox     实线 + 圆圈
            g.tempLine    拖拽中的虚线（临时）
            g.uniformity  选中态的辅助高亮
         └─ 右下浮层 .common-zoom-pane：
            直线/曲线切换、百分比输入、图形居中、放大、缩小
```

#### 三、SVG 四层的精确职责

| 层 | class | 内容 |
|---|---|---|
| 1 | `nodeBox` | `g.node` × N，每个含 `rect` + `text` + `g.controls` |
| 2 | `lineBox` | 每条线两个 `path`（`path-padding` 透明 14px 便于点选 + `path` 实线 1px）+ 每组 `g.pathCircle` |
| 3 | `tempLine` | 拖拽过程中一条 `line#l_<startNodeId>`，`stroke-dasharray:5,5` + 箭头 marker |
| 4 | `uniformity` | 选中线时的高亮辅助层 |

外层还有 `g.warp`，`transform-origin:0 0`，所有层都挂在它下面 —— 缩放/平移只改 warp。

#### 四、节点的构成（每个 `g.node`）

```html
<g class="node" id="<entityId>" style="cursor:pointer">
  <rect id="id_<entityId>" x="95" y="268" width="180" height="50" rx="5"
        fill="#EAF5FF" stroke="#3E4F60"/>          <!-- 固定 180×50 -->
  <text class="biz-udc-graph-text" x="185" y="298"
        text-anchor="middle" font-size="14px">实体名</text>
  <g class="controls" id="control_id_<entityId>" style="display:none">
    <circle class="drag-point" direction="left"   cx cy r=5/>
    <circle class="drag-point" direction="top"    cx cy r=5/>
    <circle class="drag-point" direction="right"  cx cy r=5/>
    <circle class="drag-point" direction="bottom" cx cy r=5/>
    <g class="delete-node"><circle cx=275 cy=268 r=10/><text>×</text></g>
  </g>
</g>
```

**关键细节**
- `g.node.id` = 实体 id（**不带** `id_` 前缀）
- `rect.id` = `id_<entityId>`，线的 `startId/endId` 用的就是这一串
- `g.controls` 默认 `display:none`，**鼠标 hover 到节点**才 `display:block`
- ★★ 这是最大的陷阱：锚点 `display:none` 时 `getBoundingClientRect()` 全是 0，
  必须保持 hover 才能拿到真实坐标。跨调用丢失 hover 就抓不到，
  所以「hover + mousedown + move + up」必须在**同一次 JS 执行内**完成。
- 4 个锚点各对应一个方向，**从哪个锚点出、落到哪个锚点**决定线的走向与
  `startDirection` / `endDirection` 两个字段。

#### 五、线的构成（每条 `g.lineBox` 里的线）

```html
<path class="path-padding" id="<startId>-<endId>" d="M ... " stroke="transparent" stroke-width="14"/>
<path class="path"         id="<startId>-<endId>" d="M ... " stroke="#3E4F60" stroke-width="1"/>
<g class="pathCircle" id="lineId_<startId>-<endId>">
  <circle id="circle_<startId>-<endId>" cx cy r="12|13"/>
  <text id="circle_text_<startId>-<endId>" text-anchor="middle">+</text>
</g>
```

**线 id 格式**：`id_<实体A>-id_<实体B>`（全球唯一，同源同宿只能有一条）
**pathCircle id 前缀**：`lineId_`，圆圈 `circle_`，文字 `circle_text_`

★ `path-padding` 是 14px 宽的透明描边，专为**扩大点选热区** —— 点线时
实际命中的是它，不是 1px 的 `path`。

#### 六、圆圈 `+` 与 `1` 的真实语义（`S` 函数）

```js
S = (t, e, n) => {              // t={x,y} 圆心, e=线id, n=规则条数
  let l = n || "+";                                       // 无值显示 +
  let c = n && "+" !== n && 0 !== n ? 有规则样式 : 无规则样式;
  circle.attr("r", c.radius).attr("fill", o).attr("stroke", c.strokeColor);
  text.attr("fill", c.textFill).style("font-size", c.fontSize).text(l);
}
```

- `n` 为 `undefined` / `"+"` / `0` → 画 `+`，小半径、浅样式
- `n` 为数字（如 `1`）→ 画数字，大半径、深样式

所以 **`+`→`1` 是「这条线已挂了 1 条字段映射规则」的真实信号**，
不是装饰。点圆圈 = 打开该线的映射抽屉。

#### 七、怎么画（真实交互路径）

**A. 加节点**
1. 左栏实体树 `.ant-tree-treenode[draggable=true]`
2. 拖到画布 → antd Tree 的 `onDragEnd(antdEvent)` 单参数回调
3. 回调内第一句硬门槛：
   ```js
   if (t.pageX < graphWrapper.left) return;   // 落在画布左边界外 → 静默 return
   ```
   ★ 不报错、不提示、什么都不发生 —— 这是「拖了没反应」的根因
4. 节点坐标 = 落点，宽高固定 180×50

**B. 连线**（D3 drag，不是 DOM 事件）
```js
selectAll('.drag-point').call(d3.drag()
  .on('start', ...)   // 记录 movingSelectLine
  .on('drag',  I)     // 画 tempLine 虚线，跟随鼠标
  .on('end',   T))    // 落线
```
`T` 落线函数：
```js
T = (t, e) => {                                  // t={x,y} local 坐标, e={id,direction}
  let r = eA(t.x, t.y, nodes);                   // ★ 命中检测
  let i = `${e.id}-${r.targetId}`;               // 线 id
  ...
  d.current.lines.push({id:i, startId:e.id, endId:r.targetId,
    startDirection, endDirection, x1,y1,x2,y2, circleX,circleY, path});
}
```
命中检测 `eA` 的判定（**local 坐标**，非屏幕坐标）：
```js
t >= l.x - width/2 - distance && t <= l.x + width/2 + distance &&
e >= l.y - height/2 - distance && e <= l.y + height/2 + distance
```
三道闸不建线：自连、同方向、已存在。

**C. 删线**
- 键盘 `Delete(46)` / `Backspace(8)`：先选中线，再按
- 删节点同理，会连带删该节点的所有线

**D. 移动节点**
- 鼠标拖节点本体（不是锚点）
- 或选中节点后按 **方向键** `↑↓←→`，每次移动 **1px**（`W` 函数逐像素累加）

**E. 缩放/居中（右下 `.common-zoom-pane`）**
| 控件 | 实现 | 范围 |
|---|---|---|
| 图形居中 `onFitMap` | `U` 自动计算包围盒 | — |
| 放大 `onZoomIn` | `scaleTo(k+0.1)` | — |
| 缩小 `onZoomOut` | `scaleTo(k-0.1)` | — |
| 百分比 `onPercentZoom` | `scaleTo(p/100)` | **20~200** |
| 直线/曲线 `onLineTypeChange` | `eg(...,lineType)` 重算 path | `line` / `curve` |

★ 直线/曲线切换是**逐线**属性（`lines[].lineType`），只有选中某条线时才启用；
未选中时 dropdown 是 `ant-select-disabled`。

#### 八、definition 的完整结构（保存时页面自己发的）

```json
{
  "nodes": [{
    "x":185,"y":293,"id":"id_<实体id>","title":"实体名",
    "style":{"width":180,"height":50,"left":95,"top":268},
    "direction":"","appId":"...","appName":"...","fullName":"com.seeyon...Entity"
  }],
  "lines": [{
    "id":"id_A-id_B",
    "startDirection":"right","endDirection":"left",
    "x1":185,"y1":293,"x2":686,"y2":293,
    "circleX":435.5,"circleY":293,
    "path":"M 275,293 L 305,293 L 435.5,293 L 566,293 L 596,293",
    "startId":"id_A","endId":"id_B","text":1
  }],
  "transform":{"x":0,"y":0,"k":1}
}
```

- `nodes[].x/y` 是**锚点中心**，`style.left/top` 是矩形左上角（x-w/2, y-h/2）
- `lines[].path` 由 `ew()` 按方向梯度算出，是**多段折线** `M ... L ...`
- `lines[].text` 就是圆圈数字（规则条数），首次出现时可能缺省

#### 九、对外 API（组件 ref 导出）

```js
{
  echoRelationGraph,   // 回填整个图（从 definition 还原）
  echoMappingsCount,   // 回填某条线的圆圈数字
  clearAnimationMotion,// 清空动画态
  addSymbol,           // 程序化加节点
  onFitMap, onZoomIn, onZoomOut, onPercentZoom, onLineTypeChange
}
```
`echoRelationGraph` 内部：`scaleTo(k)` → 逐个 `addSymbol` → 逐条画 path →
`lines.push` → `S(circleX,circleY,id,text)`。
★ 这是**官方认可的 programmatic 入口**，比伪造 DOM 事件可靠。

#### 十、右侧浮层 `.common-zoom-pane-tooltip` 的坑

无头/CDP 环境下抽屉和浮层动画常卡在 `transform: translateX(1200px)`，
导致内部 `ant-select` 的 portal 定位到视口外（实测 x=2357 > viewport 1707），
dropdown 永远打不开。
判据：`getComputedStyle(wrapper).transform` 是 `matrix(1,0,0,1,1200,0)` 就是卡住了。
处理：把 wrapper 的 transform 强制设为 `translateX(0px)`。
### 9.12b ★★★ 修订：pageId 不是"允许 null"，而是必须先有实体详情页

上一版 §9.8 写"pageId=null 完全允许、不需要页面"，**这是错的**。
真相由 `udcDataFlowMappingInitDataPost` 的 `pageInfoList` 直接给出：

```
应用 163126498398523384 原始状态：
  全部页面 = [{"caption":"二维码","pageUrl":"_qrcodeSetting","pageType":"DETAIL"}]
  pageInfoList = []            ← 下拉"暂无数据"的真正原因
```

`pageInfoList` 是**后端按"目标实体的 DETAIL 页"筛出来的**，
应用里没有 MigrationCheckpoint 的详情页 → 空数组 → 下拉无选项。
在空状态下强行提交，只会存进 `pageId=null` 的半壳规则（能过接口、不能跑）。

**正确前置：先生成该实体的页面。**

### 9.12c ★ 生成页面的真实入口与接口（黑盒转白盒）

UI 路径：`实体` → 选中实体 → 点「生成页面」

接口（**一次建 4 个页面**，比逐个 `base-info/create` 可靠）：

```
POST /service/udc/graphql?udcPageInfoBaseInfoBatchCreatePost
variables: { body: [ {...}, {...} ] }     # 数组，每项一个页面
```

单页 body 实测字段：

```jsonc
{"appId":"<appId>","caption":"迁移断点列表页","category":"BASIC",
 "curTerminalType":"ALL","groupId":"","handWritten":false,"hostAppName":null,
 "masterEntityIds":"<实体id>",          // ★ 字符串，不是数组
 "pageType":"SEARCH_LIST",              // 列表；详情为 DETAIL
 "pageUrl":"qyddListPage",
 "relationAppName":"migrationCheckpoint",
 "relationGroupId":"0","sourceType":"DESIGNER",
 "pageItems":[{"urlType":"MOBILE","actionType":"INSERT","menuName":"..."}]}
```

配套自动动作（同一个"生成"按钮串发）：
`udcUdcRuntimeFilterPlanPost`（建默认过滤方案）、
列表页/详情页各建 MOBILE+PC 两条 → 共 4 个 pageId。

★ 与 `base-info/create` 的差别：`masterEntityIds` 在 `base-info/create`
里要**数组**（字符串报 `BOOT_3002 反序列化失败`），
而在 `BatchCreatePost` 里是**字符串**。两个端点口径不同，别混用。

### 9.12d ★ 生成后 `pageInfoList` 立即有值（回读证据）

```
pageInfoList = [
 {id:"1218163797264834135", caption:"迁移断点详情页", pageUrl:"qyddDetailPage",
  pageType:"DETAIL", clientType:"MOBILE"},
 {id:"2343382375512589103", caption:"迁移断点详情页", pageUrl:"qyddDetailPage",
  pageType:"DETAIL", clientType:"PC"}
]
```

于是映射抽屉里的 `pageId` / `mobilePageId` **自动填好**（不再"请选择"），
`pageId=2343382375512589103`（PC）、`mobilePageId=1218163797264834135`。

### 9.12e ★ 画布连线：走 definition JSON，不走鼠标

`lines` 鼠标拖不动（React 拦 dragstart，锚点 `controls` 默认 `display:none`）。
可靠做法：读 `udcDataFlowGet.definition` → 补 `lines[]` → `udcDataFlowUpdatePost` 写回。

```jsonc
// definition 三键：nodes / transform / lines
"lines":[{"id":"<startId>-<endId>","startId":"id_<源实体>","endId":"id_<目标实体>",
          "text":1,"startDirection":"right","endDirection":"left",
          "x1":..,"y1":..,"x2":..,"y2":..,"circleX":..,"circleY":..,
          "path":"M x1+90,y1 L x1+180,y1 L x2-180,y2 L x2-90,y2"}]
```

`udcDataFlowUpdatePost` **必须带 `appId`**，否则 `BOOT_1001 所属应用ID 不能为null`：

```jsonc
{"body":{"id":"<flowId>","appId":"<appId>","caption":"<规则名>","definition":"<JSON 字符串>"}}
```

保存后刷新，画布 `g.node=2`、`.pathCircle` 圆内显示 `1`。

### 9.12f ! 遗留：生成的页面是空壳，检查会报 4 个 ERROR

`udcApplicationSearchDetectionPost` 实测：

```
WARN  UDC_CE_MICRO_FLOW_04003  验证微流程（旧，与本规则无关）
ERROR UDC_CE_PAGE_03907  页面 [迁移断点详情页:WEB端]  内容为空，请先设计并保存
ERROR UDC_CE_PAGE_03907  页面 [迁移断点列表页:移动端] 内容为空，请先设计并保存
ERROR UDC_CE_PAGE_03907  页面 [迁移断点详情页:移动端] 内容为空，请先设计并保存
ERROR UDC_CE_PAGE_03907  页面 [迁移断点列表页:WEB端]  内容为空，请先设计并保存
```

**"生成页面"只建页面记录与菜单，不生成布局内容**（pageSchema 未设计）。
规则本身（`udcDataFlowMappingPost` → pageId 有值 → 字段映射齐）已经落地，
但这 4 个 ERROR 会挡住"应用检查"全绿。要清零需再逐页进设计器拖控件并保存 ——
**本轮未做，标 UNVERIFIED / 待办**。

### 9.13 本轮全链 LIVE 汇总

| 动作 | 接口 | 结果 |
|---|---|---|
| 建空规则 | `udcDataFlowPost` | ✅ `4683705788777319367` |
| 画布加 2 节点 | 前端 `drag`→`addSymbol` | ✅ |
| 两节点连线 | 前端 drag-point | ✅ |
| 保存画布 | `udcDataFlowUpdatePost` | ✅ content=1 |
| 映射初始化 | `udcDataFlowMappingInitDataPost` | ✅（须 `sourceEntity`/`targetEntity` 对象三键） |
| 提交映射 | `udcDataFlowMappingPost` | ✅ `2494859495235864858` / mappingsCount=1 |
| 回读映射 | `udcDataFlowMappingGet` | ✅ 逐字段一致 |
| 应用检查 | `udcApplicationDoDetectionPost` | ✅ 0 阻断 / 0 严重 |

**这标志着生单规则从建壳到映射规则全链 LIVE。**

### 9.14 `udcDataFlowMappingInitDataPost` 真实入参（此前标 UNVERIFIED，现已取到）

```jsonc
{"body":{
  "sourceEntity":{"appId":"<appId>","appName":"<appName>",
                  "entityFullName":"com.seeyon.<appName>.domain.entity.<Src>"},
  "targetEntity":{"appId":"<appId>","appName":"<appName>",
                  "entityFullName":"com.seeyon.<appName>.domain.entity.<Tgt>"}}}
```

★ **不是** `sourceEntityId` / `dataFlowId`（那样会报 `BOOT_1001 来源实体参数 不能为null`）。
★ 三键缺一不可：`appId` + `appName` + `entityFullName`。

### 9.15 抓真实请求体的手法（可复用）

CDP `Network` 域对**同一页面内的重复请求**经常抓不到。可靠做法是给 `fetch` 打桩：

```js
const of=window.fetch;
window.fetch=function(u,o){
  if(String(u).includes('MappingInitDataPost') && o?.body) window.__initBody=String(o.body);
  return of.apply(this,arguments);
};
// 触发一次真实交互，然后读 window.__initBody
```

这比 CDP Network 稳，且顺带能拿到页面真实拼的 query 与 variables。

### 9.9 本轮已 LIVE 的部分

| 动作 | 接口 | 结果 |
|---|---|---|
| 建空规则 | `udcDataFlowPost` | ✅ `4683705788777319367` |
| 画布加 2 节点 | 前端 `drag`→`addSymbol` | ✅ `g.node` = 2 |
| 两节点连线 | 前端 drag-point | ✅ `lineBox` id 正确 |
| 保存画布 | `udcDataFlowUpdatePost` | ✅ content=1 |
| 回读 definition | `udcDataFlowGet` | ✅ nodes/lines 与预期逐字段一致 |
| 应用检查 | `udcApplicationDoDetectionPost` | ✅ 0 阻断 / 0 严重 / 1 警告（旧微流程，与本规则无关） |
| 画布渲染 | — | ✅ 2 节点 + 1 连线，**无红字** |
| 映射配置 | `udcDataFlowMappingInitDataPost` | ⚠ 初始化通，**提交卡在实体映射规则** |

### 9.10 下一步（要打通只需一步）

给目标实体建一个 PC 详情页面（自定义页面域），或在画布上把目标换成
**已有详情页面**的实体。之后 `pageId` 有值 → `entityMappingRelation` 可选 →
`mappingArea` 解锁 → 字段映射可提交。
