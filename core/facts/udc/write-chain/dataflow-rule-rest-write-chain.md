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
