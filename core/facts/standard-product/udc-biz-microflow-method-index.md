# udc-biz｜MicroFlow 专题方法索引

## 1. Capability

**回答「微流程的 CRUD、检查、元数据查询、调用关系，调哪个类哪个方法」。**

从 `udc-biz`（1856 类 / 22172 方法）里抽出 **83 个 MicroFlow 相关类**，只保留开发/运维真正会调的。

## 2. Version

`com.seeyon:udc-biz` → **实际 jar `udc-biz-5.3.605.jar`**（`pom.properties` version=5.3.605，构建 2026-10-28）

规模：**1856 类 / 148 接口 / 10 注解 / 90 枚举 / 492 个关键类 / 22172 方法**
其中 **MicroFlow 相关类 83 个**（实测类名匹配）。

> ⚠️ **版本漂移登记**：`surface-index` 里写的构件版本是 **5.3.517**，但 `cplib/` 实际 jar 是 **5.3.605**。
> 类数两版一致（1856/1856），**内容按 605 实证**；`udc-extend` 同样 517→605 漂移。
> **⇒ 引用本格签名时以 5.3.605 为准。**

## 3. Input

`docs/audit/reference/surface-index.tar.gz` → `packages/udc-biz.md`

## 4. Required

无前置。跨进程 `@DubboReference`。

## 5. Execution

```java
@DubboReference private MicroFlowAppService microFlowAppService;

// 取流程定义（含节点树）
MicroFlowDefinitionDto def = microFlowAppService
    .getMicroFlowDefinition(SingleRequest.from(flowId))
    .getData().getContent();

// 建流程
Long id = microFlowAppService.create(
    SingleRequest.from(definitionDto)).getData().getContent();

// 检查（后端 checkSchema）
CheckSchemaDto check = microFlowAppService
    .checkSchema(SingleRequest.from(definitionDto))
    .getData().getContent();
```

## 6. Output

---

## 6.1 `MicroFlowAppService`（95 方法：75 真方法 + 20 个 `lambda$`）—— 主入口

`com.seeyon.udc.appservice.MicroFlowAppService`

### 6.1.1 CRUD（最常用）

```java
SingleResponse<Long>    create(SingleRequest<MicroFlowDefinitionDto>);
SingleResponse<Integer> update(SingleRequest<MicroFlowDefinitionDto>);
SingleResponse<Boolean> deleteById(SingleRequest<Long>);
SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>>);
SingleResponse<Boolean> deleteBySourceId(SingleRequest<String>);
SingleResponse<Long>    copy(SingleRequest<CopyInfoDto>);
ListResponse<CopyInfoBySourceIdRespDto> copyBySourceId(SingleRequest<...>);
SingleResponse<MicroFlowItemDto> recover(Long, Long);      ★ 不用 SingleRequest
```

### 6.1.2 查询

```java
SingleResponse<MicroFlowDefinitionDto> getMicroFlowDefinition(SingleRequest<Long>);
PageResponse<MicroFlowItemDto>         selectListByCondition(PageRequest);
ListResponse<MicroFlowItemDto>         selectListByQuery(SingleRequest<MicroFlowQueryDto>);
PageResponse<MicroFlowItemDto>         searchListByCaption(PageRequest);
ListResponse<MicroFlowDefinitionDto>   selectDetailsBySourceId(SingleRequest<String>);
ListResponse<MicroFlowDefinitionDto>   selectListByCondition4Deploy(SingleRequest<...>);
```

### 6.1.3 ★★★ 检查（生成后必调）

```java
SingleResponse<CheckSchemaDto> checkSchema(SingleRequest<MicroFlowDefinitionDto>);
SingleResponse<CheckSchemaDto> checkSchemaAndUpdate(SingleRequest<MicroFlowDefinitionDto>);
ListResponse<MicroFlowNodeDefinitionDto> getDisableNodes(SingleRequest<...>);
```

**★★★★★ 四条铁律（呼应白明涛的微流程铁律）：**

| # | 事实 |
|---|---|
| 1 | **`checkSchema` 只返回后端校验结果** —— 前端绑定错它认不出 |
| 2 | **`checkSchemaAndUpdate` 会顺手落库** —— 只检查不要用这个 |
| 3 | **前后端两套必填都要满** —— 必填未满前端零请求 |
| 4 | **真验收必须在 UI 点「检查」+ 逐节点开抽屉看红字** |

### 6.1.4 唯一性检查

```java
SingleResponse<Boolean> checkMicroFlowCaptionIsExists(SingleRequest<...>);
SingleResponse<Boolean> checkMicroFlowNameIsExists(SingleRequest<...>);
```

### 6.1.5 服务信息（出入参签名来源）

```java
SingleResponse<MicroFlowServiceInfoDto> getServiceInfoById(SingleRequest<Long>);
SingleResponse<MicroFlowServiceInfoDto> getServiceInfoByParams(SingleRequest<...>);
SingleResponse<MicroFlowAppServiceMetaDataDto> getMicroFlowAppServiceMetaDataBoById(...);
```

**⇒ 想知道微流程生成了什么方法签名，查 `getServiceInfoById` 返回的 `MicroFlowServiceInfoDto`。**

### 6.1.6 元数据查询（节点选对象/字段/枚举/AppService 的数据源）

```java
ListResponse<MfDtoMetadataItemDto>  selectNonEntityTreeExcludeBoot(SingleRequest<...>);
SingleResponse<MfDtoMetadataDto>    findCustomDto(SingleRequest<...>);
ListResponse<MfAggEntityItemDto>    searchEntityTree(SingleRequest<...>);
ListResponse<MfAggEntityItemDto>    searchEntityDtoTree(SingleRequest<...>);
SingleResponse<MfAggDtoMetadataDto>  selectMfAggDtoByAggDtoFullNameList(SingleRequest<...>);
SingleResponse<MfFullAggDtoMetadataDto> selectMfFullAggDto(SingleRequest<...>);
ListResponse<MfJavaEnumDto>         selectMfJavaEnumByAggDtoFullNameList(SingleRequest<...>);
ListResponse<MfJavaEnumDto>         searchEnumByAppName(SingleRequest<...>);
SingleResponse<MfJavaEnumDto>       findEnumByName(SingleRequest<...>);
ListResponse<String>                filterNotVirtualDto(SingleRequest<List<String>>);
ListResponse<Set<String>>           selectDataSystemInfo(SingleRequest<MetaDataQueryDto>);
SingleResponse<Boolean>             checkDtoMetaDataExist(SingleRequest<MetaDataQueryDto>);
```

**⇒ 「这个字段能不能在微流程里选」= `filterNotVirtualDto` + `checkDtoMetaDataExist`。**

### 6.1.7 AppService / 方法搜索（节点调用标品用）

```java
SingleResponse<MfAppServiceMetadataDto>       searchAppService(SingleRequest<...>);
ListResponse<MfAppServiceMetadataDto>         searchAppServiceByAppName(SingleRequest<...>);
SingleResponse<MfAppServiceMetadataDto>       searchAppServiceByName(SingleRequest<...>);
SingleResponse<MfAppServiceMethodDto>         searchMethodByName(SingleRequest<...>);
SingleResponse<MfRestDto>                     searchRestWithOutBoot(SingleRequest<...>);
ListResponse<UdcApplicationMetaDataDto>       searchApps(SingleRequest<...>);
```

### 6.1.8 事件 / MQ / 消息（触发器类节点）

```java
ListResponse<EventQueryResultDto>  filterEvent(SingleRequest<...>);
ListResponse<MfMqDto>              filterSystemMqInfo(SingleRequest<...>);
ListResponse<MfMqDto>              searchMqList(SingleRequest<MetaDataQueryDto>);
ListResponse<MfDtoMetadataItemDto> searchMicroFlowEventList(SingleRequest<...>);
ListResponse<MfDtoMetadataItemDto> selectMessageExcludeBoot(SingleRequest<...>);

// 消息 CRUD
SingleResponse<Long>    createMessage(SingleRequest<MicroFlowMsgDto>);
SingleResponse<Integer> updateMessage(SingleRequest<MicroFlowMsgDto>);
ListResponse<MicroFlowMsgDto> searchMsgByAppId(SingleRequest<Long>);
ListResponse<MicroFlowMsgDto> searchEventByAppId(SingleRequest<Long>);
SingleResponse<Integer> deleteMessageById(SingleRequest<Long>);
SingleResponse<MicroFlowMsgDto> getMessageById(SingleRequest<Long>);
```

### 6.1.9 调用关系（上下游）

```java
ListResponse<MicroFlowCallInfoDto> findUpstreamCallInfo(Long, Long);     ★ 裸参数
ListResponse<MicroFlowCallInfoDto> findDownstreamCallInfo(Long, Long);   ★ 裸参数
SingleResponse<Map<String,List<String>>> findCallExtendAppServiceNode(SingleRequest<...>);
```

**⇒ 「谁调了我 / 我调了谁」用这两个，参数是 `(id, id)` 不带包装。**

### 6.1.10 子流程 / 分页查询

```java
PageResponse<MicroFlowSubMfDto> selectSubMfPageByAppId(PageRequest);
PageResponse<MicroFlowSubMfDto> selectServiceMicroFlowPageByAppId(PageRequest);
PageResponse<MicroFlowSubMfDto> selectFrontendServiceMicroFlowPageBySourceId(PageRequest);
PageResponse<MicroFlowItemDto>  selectEntityRulePageByEntityId(PageRequest);
```

### 6.1.11 排序 / 分组 / 表达式

```java
SingleResponse<Integer> updateOrderNoAndGroup(SingleRequest<MicroFlowOrderDto>);
SingleResponse<Integer> batchMove(SingleRequest<List<MicroFlowOrderDto>>);
SingleResponse<String>  generateExpressionId(SingleRequest<String>);
ListResponse<ListOperationTypeDto> getListOperationTypes();
```

### 6.1.12 部署用

```java
Map<Long, List<Map<String,Object>>> getUsedEntityActionByAppId(SingleRequest<Long>);
SingleResponse<Integer> disableLastVersionMetadata(SingleRequest<Long>);
ListResponse<String> findNodeSchemaByCondition(SingleRequest<NodeSchemaQueryDto>);
```

---

## 6.2 `MicroFlowCodeUtil`（110 真方法 / 123 含 lambda）—— 代码生成工具

`com.seeyon.udc.common.autocode.util.MicroFlowCodeUtil`

**★ 这是生成器内部工具，业务代码不直接调。** 但要知道它在，因为：

| 用途 | 代表方法 |
|---|---|
| 类型判定 | `isEntityType(ApplicationDto, Map)` / `isSelectedEntityField(Map, Collection)` |
| 选择参数取值 | `getSelectParamValue(SelectParam)` / `getSingleSelectParamValue(SelectParam)` |
| 类型转换 | `castTypeObject(String, String)` |
| 必填判定 | `requiredOperationParam(String)` |
| 列表名 | `getRealListName(ApplicationDto, Map, String, String)` |

**⇒ 排查「生成的代码类型不对/取值不对」时读这个类，业务代码别调。**

## 6.3 `MicroFlowFrontEndService`（79 真方法 / 122 含 lambda）—— 前端检查

`com.seeyon.udc.microflow.domain.service.MicroFlowFrontEndService`

**★ 这是「前端检查」的真实实现** —— 逐节点遍历 `ArrayNode`，检查：

```java
static void detection(MicroFlowDefinitionDto, NodeContext);
static void parseNodes(ArrayNode, NodeContext, String);
static void dealSelectParam(...);          // 选择参数
static void dealCtpEnum(...);              // 枚举值
static void checkUiModelExist(...);        // UI 模型存在性
static void checkDataTargetHiddenField(..);// 隐藏字段
static void checkFormSelectParamDataType(...); // 数据类型
static void checkFormSelectParamDataTypeBySelectParam(...);
```

**★★★★★ 这是白明涛那条铁律的技术根源：**

```
checkSchema（MicroFlowAppService）= 后端校验
detection / parseNodes（MicroFlowFrontEndService）= 前端校验，逐节点

⇒ 两者不同。后端绿 ≠ 前端过。
⇒ 前端绑定错只有 MicroFlowFrontEndService 这条链路认得出。
```

## 6.4 其余 80 个类（分类，按需查 JSON）

| 类别 | 类 |
|---|---|
| **模板** | `MicroFlowTemplate` / `CustomMicroFlowTemplate` / `CustomMicroFlowControllerTemplate` / `MicroFlowWebControllerTemplate` / `MicroFlowTriggerTemplate` / `MicroFlowScheduleTemplate` / `HostAppMicroFlowTemplate` |
| **节点解析** | `MicroflowNodeParser` / `MicroflowNodeParserFactory` / `MicroFlowNodeFindUtil` / `MicroFlowParserUtils` |
| **组件级联** | `MicroFlowComponentHandler` / `MicroFlowSubComponentHandler` / `MicroFlowRecursiveComponentHandler` / `MicroFlowComponentCascadeHandler` / `DefaultMicroFlowComponentCascadeHandlerDispatcher` |
| **Metadata** | `MicroFlowMetaDataQueryService` / `MicroFlowRuntimeMetadataQueryService` / `MicroFlowMetadataQueryUtil` / `MicroFlowLastVersionMetadataService` / `UdcMicroFlowMetadata4OssService` |
| **升级/重构** | `MicroFlowUpgradeAppService` / `MicroFlowUpgradeService` / `MicroFlowUpgradeUtil` / `MicroFlowRefactorService` / `MicroFlowRefactorAppService` |
| **DAO** | `MicroFlowEntityDao` / `MicroFlowGroupDao` / `MicroFlowPresetTemplateDao` |
| **其他** | `MicroFlowBoFactory` / `MicroFlowDtoFactory` / `MicroFlowCallGraphUtil` / `MicroFlowOperationLogBuilder` / `MicroFlowLocatorManager` / `MicroFlowCascadeUtil` / `BackendMicroFlowCallServiceResolver` |

---

## 7. Side Effects

| 方法 | 副作用 |
|---|---|
| `create` | **建流程定义（可能连带生成代码）** |
| `update` | 改定义 |
| `checkSchemaAndUpdate` | **检查 + 落库** |
| `deleteById` / `deleteByIds` / `deleteBySourceId` | **删流程，可能保留死壳** |
| `disableLastVersionMetadata` | 停用元数据（影响运行态） |
| `createMessage` / `updateMessage` / `deleteMessageById` | 改消息定义 |
| `recover` | 恢复删除的流程 |

**⇒ 删除类操作有「死壳」风险，必须先确认关联。**

## 8. Known Constraints

| # | 约束 |
|---|---|
| 1 | **`checkSchema` ≠ 前端检查**（前端在 `MicroFlowFrontEndService`） |
| 2 | **`checkSchemaAndUpdate` 会落库**，纯检查用 `checkSchema` |
| 3 | **`recover` / `findUpstreamCallInfo` / `findDownstreamCallInfo` 用裸参数**，不包 `SingleRequest` |
| 4 | **三个方法用 `PageRequest`**（`selectListByCondition` 等） |
| 5 | **`MicroFlowCodeUtil` / `MicroFlowFrontEndService` 是内部工具**，业务不直调 |
| 6 | **`createMessage` 与微流程本体是两套**，别混 |
| 7 | **删除会留死壳**（REST 建页面留死壳是同类问题） |
| 8 | **取值两层 `getData().getContent()`** |

## 9. Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 1856 类 / 22172 方法 | `packages/udc-biz.md` 头部 + 实际 jar 类数核对（1856=1856） | **VERIFIED_STATIC_BYTECODE** |
| **实际 jar = 5.3.605** | `pom.properties` `version=5.3.605` + MANIFEST `Implementation-Version: 5.3.605` | **LIVE** |
| **`MicroFlowAppService` 95 = 75 真方法 + 20 `lambda$`** | `interfaces.json` 逐个枚举：95 个方法名中 20 个以 `lambda$` 开头 | **LIVE（本次重建）** |
| **`MicroFlowCodeUtil` 110 / `MicroFlowFrontEndService` 79 / `MicroFlowService` 126** | 方法表扣除 `lambda$` 后精确等于索引声称值（123−13 / 122−43 / 224−98） | **VERIFIED_STATIC_BYTECODE** |
| **83 个 MicroFlow 相关类** | 类名正则匹配实测 | **VERIFIED_STATIC_BYTECODE** |
| `MicroFlowAppService` 95 方法（75 真 + 20 lambda） | `interfaces.json` 枚举 | **LIVE（本次重建）** |
| `MicroFlowCodeUtil` 110 方法 | javap 原文 | **VERIFIED_STATIC_BYTECODE** |
| `MicroFlowFrontEndService` 79 方法 | javap 原文 | **VERIFIED_STATIC_BYTECODE** |
| `checkSchema` 签名 | javap 原文 | **VERIFIED_STATIC_BYTECODE** |
| 前端检查在 `MicroFlowFrontEndService` | 方法名 `detection` + `parseNodes` + `checkFormSelectParamDataType*` | **VERIFIED_STATIC_BYTECODE** |
| 删除留死壳 | `udc/` 域 LIVE 事实（`datamigration-page-lifecycle` 同类） | 跨格引用 |

## 10. Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：`MicroFlowAppService` 全部方法签名（javap）
- ✅ **VERIFIED_STATIC_BYTECODE**：83 个 MicroFlow 类清单
- ✅ **VERIFIED_STATIC_BYTECODE**：`MicroFlowCodeUtil` 110 / `MicroFlowFrontEndService` 79 方法数
- ✅ **LIVE**：`MicroFlowAppService` = **95 个方法名**，其中 **20 个 `lambda$` 合成 + 75 个真方法**
  （`interfaces.json` 逐个枚举所得，不是从文档渲染结果推断）
- ✅ **VERIFIED_STATIC_BYTECODE**：`MicroFlowCodeUtil` 110 / `MicroFlowFrontEndService` 79 / `MicroFlowService` 126
  （均扣除 `lambda$` 后与索引一致 → 索引口径是「真方法」，可信）
- ⚠️ **UNVERIFIED**：`checkSchema` 的真实返回结构（需 LIVE）
- ⚠️ **未覆盖**：其余 80 个类的方法签名（按需查 JSON）

## 11. 给 Agent 的判据

```
问「怎么建微流程定义」
  → MicroFlowAppService.create(SingleRequest<MicroFlowDefinitionDto>)

问「怎么拉流程定义看节点树」
  → MicroFlowAppService.getMicroFlowDefinition(id)

问「生成后怎么检查」
  → 后端：checkSchema(dto)          ← 只检查，不落库
  → 前端：UI 点「检查」+ 逐节点开抽屉看红字
     ★ 后端绿 ≠ 前端过

问「为什么后端过了前端报错」
  → MicroFlowFrontEndService.detection/parseNodes 是前端校验链路
     checkFormSelectParamDataType 等只有它认得出

问「微流程生成了什么方法签名」
  → MicroFlowAppService.getServiceInfoById(id) → MicroFlowServiceInfoDto

问「这个字段/枚举能不能选进节点」
  → filterNotVirtualDto / checkDtoMetaDataExist / findEnumByName

问「谁调用了这个微流程」
  → findUpstreamCallInfo(id, id)     ← 裸参数

问「节点里能调哪些标品 AppService」
  → searchAppService / searchMethodByName

问「删微流程会不会留死壳」
  → 会。删除前先查上下游调用关系
```