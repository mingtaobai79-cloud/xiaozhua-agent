# setting / entity 域工具 body ↔ 平台 DTO 字段对照

> 证据级：**VERIFIED_STATIC_BYTECODE**（javap 读 DTO 字段）+ 工具实际输出（本地生成，未提交）
> jar：`udc-biz-5.3.517` / `udc-common-5.3.605`
> 方法：jar → javap `private` 字段表 → 与工具 body 的 key 集合做差

## 1. Capability

工具产出的 body 是不是平台真收的字段。
多一个字段可能被静默忽略，也可能直接 400；少一个必填直接拒。
本格只记**已用字节码证实的差**，没找到 DTO 的一律标 UNVERIFIED。

## 2. 已确认的对照

### 2.1 `refer_config_body` ↔ `ReferConfigInfoDto`

```java
// com.seeyon.udc.dto.ReferConfigInfoDto
String caption;  Long appId;  Long entityId;  String type;
List<ReferConfigDto> referConfigDetail;
OperationLogDetailsDto operationLog;
```

写入入口：`ReferConfigGroupService.createConfigInfo(ReferConfigInfoDto)`

工具实际产出 key：

```
appId  entityId  caption  type  referConfigDetail  id  unknowns
                                              ↑     ↑
                                          DTO 里没有
```

**★ `unknowns`：已确认是垃圾键，已修**

`ReferConfigInfoDto` 没有这个字段。工具原来把自身的"未确认项"塞进 body 一起发出去。
现在改成**不进 body**（构造器里直接不写），非法 `refer_type` 改为 **raise ValueError**。

**★ `type` 的真实取值：不是 ENTITY**

工具 docstring 写明（来源 module-75586 F/Sv 字面量）：

```
refer_type ∈ List | TreeList | LeftTreeRightList     ← 列表形态，这是 type 的值
```

而 `ReferConfigSourceTypeEnum`（javap 实测）只有：

```
ENTITY  BASIC_DATA
```

两者是**不同字段**：`ENTITY`/`BASIC_DATA` 是"数据来源类型"，`List`/`TreeList`/`LeftTreeRightList`
是"参照列表形态"。工具原来对非法值只记 unknowns 不报错，导致 `ENTITY` 一路发到平台。

现改为：非三种形态直接 `ValueError`。

**★ `id` 保留**：`ReferConfigInfoDto` 没有 id，但它是编排意图
（`id` 有值 → 路由 `updateConfigInfo`，空 → `createConfigInfo`）。
GraphQL 入参 DTO 是否收这个键**未验证**，暂不动。

### 2.2 `event_body` ↔ `Event` 实体

```java
// com.seeyon.udc.entity.domain.entity.Event
String name;      String caption;
EventSourceEnum source;        MessageTypeEnum messageType;
Long sourceId;    Boolean enabled;
String expDesignData;          String expRuntimeData;
EventActionTypeEnum actionType;
Long eventData;   String numberFiredOnce;
ObjectTypeEnum eventDataType;
String messageTopic;           String messageTags;   String description;
```

工具产出 key：

```
appId  caption  name  source  sourceId  actionType  numberFiredOnce
messageType  enabled  eventData  eventDataType
```

**★ `appId` 不在 Event 实体里**。工具的 body 用它，实体没有这个字段。

**工具没给**：`expDesignData` / `expRuntimeData` / `messageTopic` / `messageTags` / `description`。
这几个是否必填**未验证** —— 需要看 `EventService.create` 的校验分支（下一步）。

### 2.3 `index_body` ↔ `IndexDto`（**无问题**）

```java
// com.seeyon.udc.common.dto.IndexDto
Long appId;  String caption;  String name;  String code;
String fieldIds;      // ★ 确实是 String，不是 List
String fieldNames;    String fieldCaptions;  String remark;
IndexSourceEnum indexSource;  Long entityId;  IndexTypeEnum type;
```

工具产出 `{caption, entityId, fieldIds}` —— `fieldIds` 传字符串是**对的**（DTO 里就是 String）。
`IndexTypeEnum` 只有 `NORMAL` / `UNIQUE`。

### 2.4 `dto_body` ↔ `DataTransferObjectDto` + `DtoAttributeDto`

```java
// udc-plugin-api-5.3.517
DataTransferObjectDto extends UdcBaseEntityDto
  name caption source sourceType isRoot parentEntityId batchId
  appId appName appCaption sourceId isCommandDto attributes
  description isMetaData fullName refId

DtoAttributeDto extends BaseUdcAttributeDto
  自身:  appId dtoId dataTypeCategory type mappingId fullName
  父类:  actionType createTime updateTime name caption dataType
         dataTypeDisplayName notNull description minLength maxLength
         decimalDigits multiSelect relationEntity relationEntityCategory
         relationEntityName relationCode relationType
```

写入入口：`DataTransferObjectAppServiceImpl.createDtoWithAttrs(DataTransferObjectDto)`
→ 取 `getAttributes()` → `DtoAttributeService.createBatch(List)`
→ 按 `dtoId` 分组（`ldc "dtoId"`）+ `IN_name` 查询

**★ 真 bug：`isNotNull` → 应为 `notNull`**

| | |
|---|---|
| 工具产出 | `{"isNotNull": 0}` |
| 平台字段 | `private Boolean notNull;` / `public Boolean getNotNull()` |
| JSON key（Jackson 用 getter） | **`notNull`**，值是 Boolean |
| `@JsonProperty` 注解 | `javap -v` 查无（所以就是字段/getter 名） |

`isNotNull` 平台完全不认，等于"非空约束"这个设置静默丢失。已改。

**★ 其余字段是对的**：
`name` / `caption` / `dataType` 在父类 `BaseUdcAttributeDto`；
`dataTypeCategory` / `type` 在 `DtoAttributeDto` 自身。
`dtoId` 由平台在建完 DTO 后回填（`createDtoWithAttrs` 里先 `setId`）。

### 2.5 `event_data_body` ↔ `EventAndDataDto`（**不是 bug，别改**）

```java
// udc-plugin-api-5.3.517
EventDto extends UdcBaseEntityDto
  name caption source messageType sourceId appId appName
  expDesignData expRuntimeData actionType triggerType enabled type
  eventDataType eventData eventDataFullName numberFiredOnce createTime
  description messageTopic messageTags className

EventAndDataDto extends EventDto
  List<DataTransferObjectDto> eventDataList
  DtoSourceTypeEnum sourceType        // PART / ALL
```

**上一轮怀疑 `appId` 多余 —— 错，`EventDto` 有 `appId`。**（实体 `Event` 没有，但 DTO 有。）

**`eventDataList` 单对象 vs List**：DTO 声明是 `List`，但前端提交的是单对象：

```js
// src_redux_store_ts.14dc061e.js  offset 789645
r = { appId, caption, name, source:"MICRO_FLOW", sourceId,
      eventDataType, description, eventDataList: l, messageType }
```

`l` 是单个 `M({...n, attrs:a})`。前端就传单对象 —— **GraphQL 层负责包**。工具照抄，不改。

**`sourceType` 工具没传**：前端提交同样没传。`checkAttribute` 里读
`DataTransferObjectDto.getSourceType()` 是有条件的（`ifnull` 分支），不是必填。**不算 bug。**

**枚举实值（javap）**：
```
DtoSourceTypeEnum  PART / ALL
DtoSourceEnum      ENTITY_BUSINESS_EVENT MICRO_FLOW ENTITY CONNECTOR
                   MICRO_FLOW_EVENT MICRO_FLOW_MESSAGE PAGE_VARIABLE DYNAMIC_DEPENDENCY
ObjectTypeEnum     OBJECT / LIST
```

## 3. 找不到 DTO 的（UNVERIFIED，别当成已通）

| 工具 | 搜索方式 | 结果 |
|---|---|---|
| `event_data_body` | grep `eventDataList` | 只出现在 `EventService` / `Entity4RecordService`，**无对应 DTO 类**，是 Map 驱动 |
| `excel_template_body` | grep `ExcelTemplateData` | 0 命中 |
| `scalability_field_body` | grep `ScalabilityAttribute` | 只在 Service 里，无 DTO |
| `app_dependency_body` | grep `AppDependency` | 只有 `MicroFlowDependencyAnalyser` |

⇒ 这四个的字段对不对**不知道**。要么继续往 `udc-biz` 里挖 Service 方法签名，要么等真机提交炸出来。

## 4. `app_dependency_body` 的形状要注意

工具产出的是**操作描述**，不是纯 body：

```
{op, body, dependentAppType, autoFollowUp, note, missingFrontendFields}
```

只有 `body` 是给平台的，其余是编排元数据。
**调用方如果直接把整个 dict 发出去就会带上垃圾字段** —— 需要确认 dispatch 层有没有剥壳。

## 5. 已修 / 待修

已修：

1. `refer_config_body` 不再往 body 塞 `unknowns`
2. `refer_config_body` 的 `refer_type` 非 `List`/`TreeList`/`LeftTreeRightList` 直接 raise
   （以前只记 unknowns，非法值照发）
3. 三条回归测试 + 反向验证（注入 `body["unknowns"]=[...]` → 测试红）

待查：

- `event_body` 的 `appId`：`Event` 实体没有，但 `EventService.create(EventDto)` 收的是 DTO
  （`EventDto` 不在已解包的 udc-common/udc-biz 里，需继续找 jar）
- `event_data_body` → `EventAndDataDto`（`udc-common` 也没解出，同批）
- `excel_template_body` / `scalability_field_body` / `app_dependency_body` 的 DTO 未定位
